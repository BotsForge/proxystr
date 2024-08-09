# ProxyStr
[![Telegram channel](https://img.shields.io/endpoint?url=https://runkit.io/damiankrawczyk/telegram-badge/branches/master?url=https://t.me/bots_forge)](https://t.me/bots_forge)

An analogue of [better-proxy](https://github.com/alenkimov/better_proxy) by [alenkimov](https://github.com/alenkimov), but with string-like behavior, support for mobile proxies, and proxy checking functions. ProxyStr is heavier than *better-proxy* and requires **httpx** but if you need proxies, you will likely need this library anyway.
```python
isinstance(Proxy('127.0.0.1:3001'), str)  # --> True
```
```bash
pip install proxystr
```
Full list of depencies: `pydantic, httpx, httpx-socks`
## Supports various proxy formats
```python
from proxystr import Proxy
Proxy('host:port')
Proxy('host:port:login:password')
Proxy('login:password@host:port')
Proxy('login:password|host:port')
Proxy('http://login:password@host:port')
...
```
- for **mobile proxy** you can add a refresh (rotation) url
```python
Proxy('host:port:login:password[https://rotate.my-proxy.io?api_key=your_api_key]')
Proxy('http://login:password@host:port[https://rotate.my-proxy.io?api_key=your_api_key]')
...
```
P.S. The string parsing method was copied from [better-proxy](https://github.com/alenkimov/better_proxy).

## New in v 2.0:
- both `requests` and `aiohttp` changed to one lib `httpx`
- new methods `Proxy.check()` and `Proxy.acheck()`
- proxy checking functions got a new parameter `raise_on_error` defaults to False
- now it is possible to inherit from the Proxy class and pass the new class to the Pydantic BaseModel without an error
- `check_proxy()` now is fully sync
- `check_proxies()` can be called with arg `use_async=False` (not recommended but if u really need this u can use it)
- tests added
- a lot of small fixes

## Common use cases
- **aiohttp**
```python
import aiohttp
from proxystr import Proxy

proxy = Proxy("login:password@210.173.88.77:3001")

async def fetch(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, proxy=proxy.url) as response:
            return await response.text()
```

- **aiohttp-socks**
```python
import aiohttp
from aiohttp_socks import ProxyConnector
from proxystr import Proxy

proxy = Proxy("socks5://login:password@210.173.88.77:3001")

async def fetch(url):
    connector = ProxyConnector.from_url(proxy.url)
    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.get(url) as response:
            return await response.text()
```

- **requests**
```python
import requests
from proxystr import Proxy

proxy = Proxy("login:password@210.173.88.77:3001")

def fetch(url):
    response = requests.get(url, proxies=proxy.dict)    
    return response.text
```

- **httpx**
```python
import httpx
from proxystr import Proxy

proxy = Proxy("login:password@210.173.88.77:3001")

async def fetch(url):
    async with httpx.AsyncClient(proxy=proxy.url, follow_redirects=True) as client:
            response = await client.get(url)
            return response.text
# or
def sync_fetch(url):
    with httpx.Client(proxy=proxy.url, follow_redirects=True) as client:
            return client.get(url).text
# or
def simple_fetch(url):
    return httpx.get(url, proxy=proxy.url, follow_redirects=True).text
```

- **httpx-socks**
```python
import httpx
from httpx_socks import AsyncProxyTransport, SyncProxyTransport
from proxystr import Proxy

proxy = Proxy("socks5://login:password@210.173.88.77:3001")

async def fetch(url):
    transport = AsyncProxyTransport.from_url(proxy.url)
    async with httpx.AsyncClient(transport=transport, follow_redirects=True) as client:
            response = await client.get(url)
            return response.text
# or
def sync_fetch(url):
    transport = SyncProxyTransport.from_url(proxy.url)
    with httpx.Client(transport=transport, follow_redirects=True) as client:
            return client.get(url).text
```

- **playwright**
```python
from playwright.async_api import async_playwright, Playwright
from proxystr import Proxy

proxy = Proxy("login:password@210.173.88.77:3001")

async def fetch(playwright: Playwright, url):
    chromium = playwright.chromium
    browser = await chromium.launch(proxy=proxy.playwright)
    ...
```
P.S. Playwright communication was copied from [better-proxy](https://github.com/alenkimov/better_proxy).

## Object representation
```python
import json
from proxystr import Proxy

proxy = Proxy("login:password@210.173.88.77:3001")
print(proxy)  # according to Proxy.default_pattern
print(json.dumps(proxy))
print({'proxy': proxy})
print(proxy.url)
print(proxy.dict)
print(proxy.json())
print(proxy.playwright())
```
Output:
```
login:password@210.173.88.77:3001
"login:password@210.173.88.77:3001"
{'proxy': Proxy(http://login:password@210.173.88.77:3001)}
http://login:password@210.173.88.77:3001
{'http': 'http://login:password@210.173.88.77:3001', 'https': 'http://login:password@210.173.88.77:3001'}
{'protocol': 'http', 'username': 'login', 'password': 'password', 'ip': '210.173.88.77', 'port': 3001, 'rotation_url': None}
{'server': 'http://210.173.88.77:3001', 'password': 'password', 'username': 'login'}
```
- **You can change default pattern**
```python
import json
from proxystr import Proxy

Proxy.set_default_pattern('protocol://ip:port:username:password[rotation_url]')

proxy = Proxy("login:password@210.173.88.77:3001[https://rotate.my-proxy.io?api_key=your_api_key]")
print(proxy)
print(json.dumps(proxy))
print({'proxy': proxy})
```
Output:
```
http://210.173.88.77:3001:login:password[https://rotate.my-proxy.io/?api_key=your_api_key]
"http://210.173.88.77:3001:login:password[https://rotate.my-proxy.io/?api_key=your_api_key]"
{'proxy': Proxy(http://login:password@210.173.88.77:3001)}
```

## Proxy checking
```python
from proxystr import Proxy, check_proxies, read_proxies

proxies = [
    Proxy("login:password@210.173.88.77:3001"),
    Proxy("login:password@210.173.88.78:3002")
]
good_proxies, bad_proxies = check_proxies(proxies)
# or in raw str format:
good_proxies, bad_proxies = check_proxies(["log:pass@210.173.88.77:3001", "log:pass@210.173.88.78:3002"])
# or read from file and check
good_proxies, bad_proxies = check_proxies(read_proxies('proxies.txt'))

# or for single proxy:
proxy = Proxy("login:password@210.173.88.77:3001")
if proxy.check():
    '''do_something'''
```
Another available functions: `check_proxy` for single proxy, `acheck_proxy` and `acheck_proxies` for async use cases
Note that sync `check_proxies()` by default just wraps async `acheck_proxies()`
- **You can get a proxy info while checking it**
```python
from proxystr import Proxy, check_proxies

proxies = [
    Proxy("login:password@210.173.88.77:3001"),
    Proxy("login:password@210.173.88.78:3002")
]
good_proxies, bad_proxies = check_proxies(proxies, with_info=True)
for proxy, info in good_proxies:
    print(info)

# or for single proxy:
proxy = Proxy("login:password@210.173.88.77:3001")
print(proxy.get_info())
```
output
```
{'country': 'Germany', 'countryCode': 'DE', 'city': 'Frankfurt am Main', 'query': '210.173.88.77'}
{'country': 'Germany', 'countryCode': 'DE', 'city': 'Frankfurt am Main', 'query': '210.173.88.78'}
```
>You can add yours `fields` argument to get another info. More details on [ip-api.com](https://ip-api.com/docs/api:json)

>Another simple way to get info is a sync method `proxy.get_info() -> Dict` or async `await proxy.aget_info() -> Dict`
## Pydantic compatibility
```python
from proxystr import Proxy
from pydantic import BaseModel

class Account(BaseModel):
    number: int
    proxy: Proxy | None = None

for account in [
    Account(number=1, proxy=Proxy('login:password@210.173.88.77:3001')),
    Account(number=2, proxy='login:password@210.173.88.77:3001')
]:
    print(account)
    print(account.model_dump())
```
output
```
number=1 proxy=Proxy(http://login:password@210.173.88.77:3001)
{'number': 1, 'proxy': Proxy(http://login:password@210.173.88.77:3001)}
number=2 proxy=Proxy(http://login:password@210.173.88.77:3001)
{'number': 2, 'proxy': Proxy(http://login:password@210.173.88.77:3001)}
```
## Set and equal support
```python
from proxystr import Proxy

p1 = Proxy('login:password@210.173.88.77:3001')
p2 = Proxy('210.173.88.77:3001:login:password')

print(p1 == '210.173.88.77:3001:login:password')  # --> True
print(p1 == p2)  # --> True
print(p1 is p2)  # --> False
print(set((p1, p2)))  # --> {Proxy(http://login:password@210.173.88.77:3001)}
```
## Available properties and functions
class `Proxy`
| name | type | returns | description |
| ------ | ------ | ------ | ------ |
| ip | attribute | str |  |
| host | property | str | same as `ip` |
| port | attribute | int |  |
| username | attribute | str |  |
| login | property | str | same as `username` |
| password | attribute | str |  |
| rotation_url | attribute | str | for mobile proxy |
| refresh_url | property | str | same as `rotation_url` |
| url | property | str | protocol://login:password@ip:port |
| dict | property | dict | urls for requests session|
| proxies | property | dict | same as `dict` |
| server | property | str | protocol://host:port |
| playwright | property | TypedDict |  |
| json() | method | dict | all attributes |
| get_info() | method | dict | info like country etc. |
| aget_info() | method | dict | async version of `get_info()` |
| check() | method | bool | simple proxy check |
| acheck() | method | bool | async version of `check()` |
| set_default_pattern() | classmethod | None | changes `__str__` pattern |
| rotate() | method | bool | sync function to rotate mobile proxy |
| arotate() | method | bool | async version of `rotate()` |
| refresh() | method | bool | same as rotate |
| arefresh() | method | bool | same as arotate |

module `proxystr`
| name | input | output | description |
| ------ | ------ | ------ | ------ |
| Proxy | str | Proxy object (str) |  |
| check_proxy() | Proxy | Tuple[Proxy, bool] |  |
| check_proxies() | Sequence[Proxy] | Tuple[List[Proxy], List[Proxy]] | returns good and failed proxies |
| acheck_proxy() | -- | -- | async version of `check_proxy()` |
| acheck_proxies() | -- | -- | async version of `check_proxies()` |
| read_proxies() | str('filepath') | List[Proxy] | read proxies from file |

## Support
Developed by `MrSmith06`: [telegram](https://t.me/Mr_Smith06) |  [gtihub](https://github.com/MrSmith06)
If you find this project helpful, feel free to leave a tip!
- EVM address (metamask): `0x6201d7364F01772F8FbDce67A9900d505950aB99`