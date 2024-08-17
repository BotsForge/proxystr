from typing import Union, Dict, List, Tuple
import asyncio

from pydantic.networks import HttpUrl
import httpx
from python_socks._errors import ProxyConnectionError

from .proxy import Proxy as BaseProxy
from .client import Client, AsyncClient


URL_FOR_CHECK = 'https://whoer.net'
URL_FOR_CHECK_WHITH_INFO = 'http://ip-api.com/json/?fields={fields}'
DEFAULT_CHECK_FIELDS = '8211'


class Proxy(BaseProxy):
    def get_info(self, fields: str = DEFAULT_CHECK_FIELDS) -> Dict[str, str]:
        # {'country': 'Germany', 'countryCode': 'DE', 'city': 'Frankfurt am Main', 'query': '64.137.94.11'}
        return check_proxy(self, with_info=True, fields=fields)[1]

    async def aget_info(self, fields: str = DEFAULT_CHECK_FIELDS) -> Dict[str, str]:
        # {'country': 'Germany', 'countryCode': 'DE', 'city': 'Frankfurt am Main', 'query': '64.137.94.11'}
        return (await acheck_proxy(self, with_info=True, fields=fields))[1]

    def check(self, url: HttpUrl = URL_FOR_CHECK, raise_on_error=False) -> bool:
        return check_proxy(self, url=url, raise_on_error=raise_on_error)[1]

    async def acheck(self, url: HttpUrl = URL_FOR_CHECK, raise_on_error=False) -> bool:
        return (await acheck_proxy(self, url=url, raise_on_error=raise_on_error))[1]

    def get_client(self) -> Client:
        return Client(proxy=self)

    def get_async_client(self) -> AsyncClient:
        return AsyncClient(proxy=self)


async def acheck_proxy(
    proxy: Union[Proxy, str],
    url: str = None,
    with_info: bool = False,
    fields: str = DEFAULT_CHECK_FIELDS,
    raise_on_error: bool = False
) -> Tuple[Proxy, Union[bool, Dict]]:
    if not isinstance(proxy, Proxy):
        proxy = Proxy(proxy)

    if not url:
        url = URL_FOR_CHECK_WHITH_INFO.format(fields=fields) if with_info else URL_FOR_CHECK

    try:
        async with AsyncClient(proxy=proxy, timeout=10) as client:
            response = await client.get(url)
            if response.status_code == 200:
                if with_info:
                    return proxy, response.json()
                return proxy, True

    except (httpx.HTTPError, ProxyConnectionError, asyncio.TimeoutError) as er:
        if raise_on_error:
            raise type(er)(f"{proxy.url} --> {er}").with_traceback(er.__traceback__)
        return proxy, False

    return proxy, False


async def acheck_proxies(
    proxy_list: List[Union[Proxy, str]],
    url: str = None,
    with_info: bool = False,
    fields: str = DEFAULT_CHECK_FIELDS,
    raise_on_error: bool = False
) -> Union[
    Tuple[List[Proxy], List[Proxy]],
    Tuple[List[Tuple[Proxy, Dict]], List[Tuple[Proxy, bool]]]
]:

    tasks = [acheck_proxy(proxy, url, with_info, fields, raise_on_error) for proxy in proxy_list]
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
    fields: str = DEFAULT_CHECK_FIELDS,
    raise_on_error: bool = False
) -> Tuple[Proxy, Union[bool, Dict]]:
    if not isinstance(proxy, Proxy):
        proxy = Proxy(proxy)

    if not url:
        url = URL_FOR_CHECK_WHITH_INFO.format(fields=fields) if with_info else URL_FOR_CHECK

    try:
        with Client(timeout=10, proxy=proxy) as client:
            response = client.get(url)
            if response.status_code == 200:
                if with_info:
                    return proxy, response.json()
                return proxy, True

    except (httpx.HTTPError, ProxyConnectionError) as er:
        if raise_on_error:
            raise type(er)(f"{proxy.url} --> {er}").with_traceback(er.__traceback__)
        return proxy, False

    return proxy, False


def check_proxies(
    proxy_list: List[Union[Proxy, str]],
    url: str = None,
    with_info: bool = False,
    fields: str = DEFAULT_CHECK_FIELDS,
    raise_on_error: bool = False,
    use_async: bool = True
) -> Union[
    Tuple[List[Proxy], List[Proxy]],
    Tuple[List[Tuple[Proxy, Dict]], List[Tuple[Proxy, bool]]]
]:
    if use_async:
        return asyncio.run(acheck_proxies(proxy_list, url, with_info, fields, raise_on_error))
    else:
        success = []
        failed = []
        for proxy in proxy_list:
            proxy, info = check_proxy(proxy, url, with_info, fields, raise_on_error)
            if with_info:
                success.append((proxy, info)) if info else failed.append((proxy, info))
            else:
                success.append(proxy) if info else failed.append(proxy)
        return success, failed


def read_proxies(filepath: str) -> List[Proxy]:
    with open(filepath) as file:
        return [Proxy(i.strip()) for i in file.readlines() if i.strip()]
