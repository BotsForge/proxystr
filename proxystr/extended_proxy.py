from typing import Dict

from pydantic.networks import HttpUrl

from .proxy import Proxy as BaseProxy
from .check import check_proxy, acheck_proxy, DEFAULT_CHECK_FIELDS, URL_FOR_CHECK
from .client import Client, AsyncClient


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
