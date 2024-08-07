import re
from typing import Dict, Literal, Union, TypedDict, Optional

from pydantic.networks import HttpUrl
import httpx

from .adapter import _ExtraTypeConstructor
from .utils import ProxyStringParser, get_fromated_proxy_string


class PlaywrightProxySettings(TypedDict, total=False):
    server: str
    bypass: Union[str, None]
    username: Union[str, None]
    password: Union[str, None]


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
        instance = str.__new__(cls, proxy_string)
        instance.__dict__.update(proxy.model_dump())
        return instance

    @property
    def refresh_url(self) -> Optional[HttpUrl]:
        return self.rotation_url

    @property
    def host(self) -> str:
        return self.ip

    @property
    def login(self) -> Optional[str]:
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

    def rotate(self, method: Literal['GET', 'POST'] = 'GET', **kwargs) -> bool:
        """for mobile proxy only"""
        if not self.rotation_url:
            raise ValueError("This proxy hasn't rotation_url")
        r = httpx.request(method, self.rotation_url, **kwargs)
        return r.status_code == 200

    async def arotate(self, method: Literal['GET', 'POST'] = 'GET', **kwargs) -> bool:
        """for mobile proxy only"""
        if not self.rotation_url:
            raise ValueError("This proxy hasn't rotation_url")
        async with httpx.AsyncClient(follow_redirects=True) as client:
            r = await client.request(method, self.rotation_url, **kwargs)
            return r.status_code == 200

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
            return cls(v)
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
