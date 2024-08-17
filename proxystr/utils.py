from typing import TYPE_CHECKING, Literal, Optional, Union, List
import re

from pydantic import BaseModel, Field, validator
from pydantic.networks import IPv4Address, HttpUrl

if TYPE_CHECKING:
    from .proxy import Proxy, ProxyPattern


ALLOWED_PROTOCOLS = Literal['http', 'https', 'socks5', 'socks4']

PROXY_FORMATS_REGEXP = [
    re.compile(
        r'^(?:(?P<protocol>.+)://)?'
        r'(?P<username>[^@|:]+):(?P<password>[^@|:]+)[@|:]'
        r'(?P<ip>[^@|:]+):(?P<port>\d+)'
        r'(\[(?P<url>https?://[^\s/$.?#].[^\s]*)\])?$'),
    re.compile(
        r'^(?:(?P<protocol>.+)://)?'
        r'(?P<ip>[^@|:]+):(?P<port>\d+)[@|:]'
        r'(?P<username>[^@|:]+):(?P<password>[^@|:]+)'
        r'(\[(?P<url>https?://[^\s/$.?#].[^\s]*)\])?$'),
    re.compile(
        r'^(?:(?P<protocol>.+)://)?'
        r'(?P<ip>[^@|:]+):(?P<port>\d+)'
        r'(\[(?P<url>https?://[^\s/$.?#].[^\s]*)\])?$'),
]


class ProxyStringParser(BaseModel, validate_assignment=True):
    protocol: ALLOWED_PROTOCOLS = 'http'
    ip: str
    port: int = Field(gt=0, le=65535)
    username: Optional[str] = None
    password: Optional[str] = None
    rotation_url: Optional[str] = None

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

    @validator('ip')
    def check_ip(cls, v):
        if v.replace('.', '').isdigit():
            IPv4Address(v)
        else:
            HttpUrl(f'http://{v}')
        return v

    @validator('rotation_url')
    def check_rotation_url(cls, v):
        if v:
            HttpUrl(v)
        return v


def get_fromated_proxy_string(proxy: Union['Proxy', ProxyStringParser], pattern: 'ProxyPattern') -> str:
    if not all((proxy.username, proxy.password)):
        pattern = re.sub(r'[^a-zA-Z0-9_/]?username[^a-zA-Z0-9_/]password[^a-zA-Z0-9_/]?', '', pattern)
    if not proxy.rotation_url:
        pattern = re.sub(r'[^a-zA-Z0-9_/]?rotation_url[^a-zA-Z0-9_/]?', '', pattern)

    parts = re.findall(r'\w+', pattern)
    pattern = re.sub(r'\w+', '{}', pattern)
    return pattern.format(*(proxy.__dict__[p] for p in parts))
