from typing import Union

import httpx
from httpx_socks import AsyncProxyTransport, SyncProxyTransport
from .proxy import Proxy


class Client(httpx.Client):
    def __init__(self, *args, proxy: Union[Proxy, str] = None, follow_redirects=True, **kwargs):
        if proxy:
            proxy = Proxy(proxy)
            if 'http' in proxy.protocol:
                kwargs['proxy'] = proxy.url
            elif 'socks' in proxy.protocol:
                kwargs['transport'] = SyncProxyTransport.from_url(proxy.url)
            else:
                raise ValueError(f'Unsupported proxy protocol "{proxy.protocol}".')
        super().__init__(*args, follow_redirects=follow_redirects, **kwargs)


class AsyncClient(httpx.AsyncClient):
    def __init__(self, *args, proxy: Union[Proxy, str] = None, follow_redirects=True, **kwargs):
        if proxy:
            proxy = Proxy(proxy)
            if 'http' in proxy.protocol:
                kwargs['proxy'] = proxy.url
            elif 'socks' in proxy.protocol:
                kwargs['transport'] = AsyncProxyTransport.from_url(proxy.url)
            else:
                raise ValueError(f'Unsupported proxy protocol "{proxy.protocol}".')
        super().__init__(*args, follow_redirects=follow_redirects, **kwargs)
