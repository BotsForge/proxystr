import unittest
import asyncio

import httpx
import python_socks

from proxystr import Proxy, check_proxies, check_proxy, acheck_proxies, acheck_proxy


# TODO tests for mobile real rotate

REAL_HTTP_PROXY = 'your_real_http_proxy_in_any_format'
REAL_SOCKS5_PROXY = 'socks5://your_real_socks5_proxy_in_any_format'
REAL_HTTP_PROXY = 'bAgVACbi:fZhLpcBy@212.193.182.47:64876'
REAL_SOCKS5_PROXY = 'socks5://84.246.87.118:49347:bAgVACbi:fZhLpcBy'


class TestCheck(unittest.TestCase):
    def setUp(self):
        self.p = Proxy(REAL_HTTP_PROXY)
        self.fp = Proxy('bsdfsdfbi:fsdfsdfy@84.246.87.222:60111')
        self.sp = Proxy(REAL_SOCKS5_PROXY)
        self.fsp = Proxy('socks5://bsdfsdfbi:fsdfsdfy@84.246.87.222:60111')
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        self.loop.close()

    def test_proxy_get_info(self):
        self.assertTrue(isinstance(self.p.get_info(), dict))
        self.assertTrue(isinstance(asyncio.run(self.p.aget_info()), dict))

    def test_proxy_check(self):
        self.assertTrue(self.p.check())
        self.assertTrue(asyncio.run(self.p.acheck()))

    def test_check_proxy(self):
        self.assertTrue(check_proxy(self.p)[1])
        self.assertTrue(check_proxy(self.sp)[1])
        self.assertTrue(isinstance(check_proxy(self.p, with_info=True)[1], dict))
        self.assertTrue(isinstance(check_proxy(self.sp, with_info=True)[1], dict))

    def test_acheck_proxy(self):
        tasks = [
            acheck_proxy(self.p),
            acheck_proxy(self.sp),
            acheck_proxy(self.p, with_info=True),
            acheck_proxy(self.sp, with_info=True)
        ]
        r = self.loop.run_until_complete(asyncio.gather(*tasks))
        self.assertTrue(r[0][1])
        self.assertTrue(r[1][1])
        self.assertTrue(isinstance(r[2][1], dict))
        self.assertTrue(isinstance(r[3][1], dict))

    def test_acheck_proxies(self):
        tasks = [
            acheck_proxies([self.p]),
            acheck_proxies([self.sp], with_info=True),
        ]
        r = self.loop.run_until_complete(asyncio.gather(*tasks))
        self.assertEqual(r[0][0][0], self.p)
        self.assertEqual(r[1][0][0][0], self.sp)
        self.assertTrue(isinstance(r[1][0][0][1], dict))

    def test_check_proxies(self):
        self.assertEqual(check_proxies([self.p])[0][0], self.p)
        self.assertEqual(check_proxies([self.sp], use_async=False)[0][0], self.sp)
        self.assertTrue(isinstance(check_proxies([self.p], with_info=True)[0][0][1], dict))
        self.assertTrue(isinstance(check_proxies([self.sp], with_info=True, use_async=False)[0][0][1], dict))

    def test_fail_check_proxy(self):
        self.assertFalse(check_proxy(self.fp)[1])
        self.assertFalse(check_proxy(self.fsp)[1])

        with self.assertRaises(httpx.HTTPError):
            check_proxy(self.fp, raise_on_error=True)
        with self.assertRaises(python_socks._errors.ProxyConnectionError):
            check_proxy(self.fsp, raise_on_error=True)

    def test_fail_acheck_proxy(self):
        r = self.loop.run_until_complete(asyncio.gather(
            acheck_proxy(self.fp),
            acheck_proxy(self.fsp)
        ))
        self.assertFalse(r[0][1])
        self.assertFalse(r[1][1])

        with self.assertRaises(httpx.HTTPError):
            asyncio.run(acheck_proxy(self.fp, raise_on_error=True))
        with self.assertRaises(python_socks._errors.ProxyConnectionError):
            asyncio.run(acheck_proxy(self.fsp, raise_on_error=True))

    def test_fail_check_proxies(self):
        self.assertEqual(check_proxies([self.fp])[1][0], self.fp)
        self.assertEqual(check_proxies([self.fsp], use_async=False)[1][0], self.fsp)

        with self.assertRaises(httpx.HTTPError):
            check_proxies([self.fp], raise_on_error=True)
        with self.assertRaises(python_socks._errors.ProxyConnectionError):
            check_proxies([self.fsp], raise_on_error=True, use_async=False)


if __name__ == '__main__':
    unittest.main()
