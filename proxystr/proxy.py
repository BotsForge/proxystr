import re
import asyncio
from typing import Dict, Optional, Literal, Union, Tuple, List, TypedDict

from pydantic import BaseModel, Field
from pydantic.networks import IPv4Address, HttpUrl
import requests
import aiohttp
from aiohttp_socks import ProxyConnector

from .adapter import _ExtraTypeConstructor


ALLOWED_PROTOCOLS = Literal['http', 'https', 'socks5', 'socks4']

PROXY_FORMATS_REGEXP = [
    re.compile(
        r'^(?:(?P<protocol>.+)://)?'
        r'(?P<username>[^:]+):(?P<password>[^@|:]+)[@|:]'
        r'(?P<ip>[^:]+):(?P<port>\d+)'
        r'(\[(?P<url>https?://[^\s/$.?#].[^\s]*)\])?$'),
    re.compile(
        r'^(?:(?P<protocol>.+)://)?'
        r'(?P<ip>[^:]+):(?P<port>\d+)[@|:]'
        r'(?P<username>[^:]+):(?P<password>[^:]+)'
        r'(\[(?P<url>https?://[^\s/$.?#].[^\s]*)\])?$'),
    re.compile(
        r'^(?:(?P<protocol>.+)://)?'
        r'(?P<ip>[^:]+):(?P<port>\d+)'
        r'(\[(?P<url>https?://[^\s/$.?#].[^\s]*)\])?$'),
]


class PlaywrightProxySettings(TypedDict, total=False):
    server:   str
    bypass:   str | None
    username: str | None
    password: str | None


class ProxyStringParser(BaseModel, validate_assignment=True):
    protocol: ALLOWED_PROTOCOLS = 'http'
    ip: Union[IPv4Address, str]
    port: int = Field(gt=0, le=65535)
    username: Optional[str] = None
    password: Optional[str] = None
    rotation_url: Optional[HttpUrl] = None

    @classmethod
    def from_string(cls, proxy_string: str):
        proxy_string = proxy_string.strip()
        for pattern in PROXY_FORMATS_REGEXP:
            match = pattern.match(proxy_string)
            if match:
                groups = match.groupdict()
                return cls(**{
                    "protocol": groups.get("protocol") or 'http',
                    "ip": groups["ip"],
                    "port": int(groups["port"]),
                    "username": groups.get("username"),
                    "password": groups.get("password"),
                    "rotation_url": groups.get("url")
                })

        raise ValueError(f'Unsupported proxy format: {proxy_string}')


class ProxyPattern(str):
    allowed_words = ('protocol', 'username', 'password', 'ip', 'port', 'rotation_url')

    def __init__(self, pattern: str):
        self.validate()

    def validate(self):
        for r in re.findall(r'\w+', self):
            if r not in self.allowed_words:
                raise ValueError(f"Unexpected word '{r}' in the pattern")


class Proxy(str, metaclass=_ExtraTypeConstructor):
    default_pattern = ProxyPattern('username:password@ip:port')
    _protected_attributes = ('protocol', 'username', 'password', 'ip', 'port', 'rotation_url')

    def __new__(cls, proxy: str, /, protocol=None):
        proxy = ProxyStringParser.from_string(proxy)
        if protocol:
            proxy.protocol = protocol
        proxy_string = get_fromated_proxy_string(proxy, cls.default_pattern)
        instance = super().__new__(cls, proxy_string)
        instance.__dict__.update(proxy.model_dump())
        return instance

    @property
    def refresh_url(self) -> HttpUrl | None:
        return self.rotation_url

    @property
    def host(self) -> str:
        return self.ip

    @property
    def login(self) -> str | None:
        return self.username

    @property
    def url(self) -> str:
        return get_fromated_proxy_string(self, ProxyPattern('protocol://username:password@ip:port'))

    @property
    def dict(self) -> Dict[str, str]:
        """
        returns commonly used pattern of proxies like in requests
        """
        if 'http' in self.protocol:
            return {'http': self.url, 'https': self.url}
        return {self.protocol: self.url}

    @property
    def proxies(self):
        return self.dict

    @property
    def server(self) -> str:
        return f"{self.protocol}://{self.ip}:{self.port}"

    @property
    def playwright(self) -> PlaywrightProxySettings:
        return PlaywrightProxySettings(
            server=self.server,
            password=self.password,
            username=self.username,
        )

    def get_info(self, fields: str = '8211') -> Dict[str, str]:
        # {'country': 'Germany', 'countryCode': 'DE', 'city': 'Frankfurt am Main', 'query': '64.137.94.11'}
        return check_proxy(self, with_info=True, fields=fields)[1]

    async def aget_info(self, fields: str = '8211') -> Dict[str, str]:
        return (await acheck_proxy(self, with_info=True, fields=fields))[1]

    def rotate(self, method: Literal['GET', 'POST'] = 'GET', **kwargs) -> bool:
        """for mobile proxy only"""
        if not self.rotation_url:
            raise ValueError("This proxy hasn't rotation_url")
        r = requests.request(method, self.rotation_url, **kwargs)
        return r.status_code == 200

    async def arotate(self, method: Literal['GET', 'POST'] = 'GET', **kwargs) -> bool:
        """for mobile proxy only"""
        if not self.rotation_url:
            raise ValueError("This proxy hasn't rotation_url")
        async with aiohttp.ClientSession() as session:
            async with session.request(method, self.rotation_url, **kwargs) as response:
                return response.status == 200

    def refresh(self, method: Literal['GET', 'POST'] = 'GET', **kwargs) -> bool:
        """for mobile proxy only"""
        return self.rotate(**kwargs)

    async def arefresh(self, method: Literal['GET', 'POST'] = 'GET', **kwargs) -> bool:
        """for mobile proxy only"""
        return await self.arotate(**kwargs)

    @classmethod
    def set_default_pattern(cls, pattern: Union[str, ProxyPattern]) -> None:
        """
        examples:
        set_default_pattern('username:password@ip:port')
        set_default_pattern('username:password:ip:port[rotation_url]')
        set_default_pattern('protocol://username:password@ip:port')
        set_default_pattern('ip:port')
        """
        cls.default_pattern = ProxyPattern(pattern)

    @classmethod
    def validate(cls, v: str) -> str:
        try:
            return Proxy(v)
        except Exception as er:
            raise ValueError(er)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.url})"

    def __hash__(self):
        return hash(self.url)

    def __eq__(self, other):
        if isinstance(other, Proxy):
            return self.url == other.url
        else:
            try:
                return self.url == Proxy(str(other)).url
            except Exception:
                pass

    def __setattr__(self, key, value):
        if key in self._protected_attributes:
            raise AttributeError(f"attribute '{key}' of '{self.__class__.__name__}' object is not writable")
        return super().__setattr__(key, value)

    def json(self) -> Dict[str, str]:
        return dict((k, self.__dict__[k]) for k in self._protected_attributes)


def get_fromated_proxy_string(proxy: Union[Proxy, ProxyStringParser], pattern: ProxyPattern) -> str:
    if not all((proxy.username, proxy.password)):
        pattern = re.sub(r'\W?username\Wpassword\W?', '', pattern)
    if not proxy.rotation_url:
        pattern = re.sub(r'\W?rotation_url\W?', '', pattern)

    parts = re.findall(r'\w+', pattern)
    pattern = re.sub(r'\w+', '{}', pattern)
    return pattern.format(*(proxy.__dict__[p] for p in parts))


async def acheck_proxy(
    proxy: Union[Proxy, str],
    url: str = None,
    with_info: bool = False,
    fields: str = '8211'
) -> Tuple[Proxy, bool | Dict]:

    if not isinstance(proxy, Proxy):
        proxy = Proxy(proxy)

    if not url:
        url = f'http://ip-api.com/json/?fields={fields}' if with_info else 'https://whoer.net'
    try:
        if 'http' in proxy.protocol:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, proxy=proxy.url, timeout=10) as response:
                    if response.status == 200:
                        if with_info:
                            return proxy, await response.json()
                        return proxy, True
        elif 'socks' in proxy.protocol:
            connector = ProxyConnector.from_url(proxy.url)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        if with_info:
                            return proxy, await response.json()
                        return proxy, True
        else:
            raise ValueError(f'Unsupported proxy protocol "{proxy.protocol}".')
    except (aiohttp.ClientError, asyncio.TimeoutError):
        return proxy, False
    return proxy, False


async def acheck_proxies(
    proxy_list: List[Union[Proxy, str]],
    url: str = None,
    with_info: bool = False,
    fields: str = '8211'
) -> Tuple[List[Proxy], List[Proxy]] | Tuple[List[Tuple[Proxy, Dict]], List[Tuple[Proxy, Dict]]]:

    tasks = [acheck_proxy(proxy, url, with_info, fields) for proxy in proxy_list]
    results = await asyncio.gather(*tasks)

    if with_info:
        success = [(proxy, info) for proxy, info in results if info]
        failed = [(proxy, info) for proxy, info in results if not info]
    else:
        success = [proxy for proxy, status in results if status]
        failed = [proxy for proxy, status in results if not status]

    return success, failed


def check_proxy(
    proxy: Union[Proxy, str],
    url: str = None,
    with_info: bool = False,
    fields: str = '8211'
) -> Tuple[Proxy, bool | Dict]:
    return asyncio.run(acheck_proxy(proxy, url, with_info))


def check_proxies(
    proxy_list: List[Union[Proxy, str]],
    url: str = None,
    with_info: bool = False,
    fields: str = '8211'
) -> Tuple[List[Proxy], List[Proxy]] | Tuple[List[Tuple[Proxy, Dict]], List[Tuple[Proxy, Dict]]]:
    return asyncio.run(acheck_proxies(proxy_list, url, with_info))


def read_proxies(filepath: str) -> List[Proxy]:
    with open(filepath) as file:
        return [Proxy(i.strip()) for i in file.readlines() if i.strip()]
