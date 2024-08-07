import unittest
import asyncio

from pydantic import BaseModel

from proxystr import Proxy, PlaywrightProxySettings


class Account(BaseModel):
    proxy: Proxy


class TestProxy(unittest.TestCase):
    def test_input_formats(self):
        default = 'login:password@210.173.88.77:3001'
        self.assertEqual(Proxy('login:password@210.173.88.77:3001'), default)
        self.assertEqual(Proxy('login:password:210.173.88.77:3001'), default)
        self.assertEqual(Proxy('210.173.88.77:3001:login:password'), default)
        self.assertEqual(Proxy('210.173.88.77:3001|login:password'), default)
        self.assertEqual(Proxy('http://login:password@210.173.88.77:3001'), default)
        self.assertEqual(Proxy('https://login:password@210.173.88.77:3001').__str__(), default)
        self.assertEqual(Proxy('socks5://login:password@210.173.88.77:3001').__str__(), default)
        self.assertEqual(Proxy('socks4://login:password@210.173.88.77:3001').__str__(), default)
        self.assertEqual(Proxy('socks5://210.173.88.77:3001').__str__(), '210.173.88.77:3001')
        self.assertEqual(Proxy('socks5://myproxy.com:3001').__str__(), 'myproxy.com:3001')

        self.assertEqual(Proxy('login:password@210.173.88.77:3001[https://myproxy.com?refresh=123]'), default)

    def test_wrong_input_formats(self):
        with self.assertRaises(ValueError):
            Proxy('login:pass:word@210.173.88.77:3001')
        with self.assertRaises(ValueError):
            Proxy('login:pass@word@210.173.88.77:3001')
        with self.assertRaises(ValueError):
            Proxy('login:pass|word@210.173.88.77:3001')
        with self.assertRaises(ValueError):
            Proxy('login:password@210.173.88.77:300111')
        with self.assertRaises(ValueError):
            Proxy('login:password@210.173.88.77.23:3001')
        with self.assertRaises(ValueError):
            Proxy('login:password@210.173.88:3001')
        with self.assertRaises(ValueError):
            Proxy('login:password@myproxy.c om:3001')
        with self.assertRaises(ValueError):
            Proxy('login:password@210.173.88.999:3001')
        with self.assertRaises(ValueError):
            Proxy('socks6://login:password@210.173.88.999:3001')
        with self.assertRaises(ValueError):
            Proxy('http:/login:password@210.173.88.999:3001')
        with self.assertRaises(ValueError):
            Proxy('socks://login:password@210.173.88.999:3001')

        with self.assertRaises(ValueError):
            Proxy('login:password@210.173.88.77:3001[https://myproxy.c om?refresh=123]')

    def test_ip(self):
        p = Proxy('login:password@210.173.88.77:3001')
        self.assertEqual(p.ip, '210.173.88.77')
        self.assertEqual(p.host, '210.173.88.77')

    def test_port(self):
        self.assertEqual(Proxy('login:password@210.173.88.77:3001').port, 3001)

    def test_refresh_url(self):
        p = Proxy('login:password@210.173.88.77:3001[https://myproxy.com?refresh=123]')
        self.assertEqual(p.refresh_url, 'https://myproxy.com?refresh=123')
        self.assertEqual(p.rotation_url, 'https://myproxy.com?refresh=123')

    def test_login(self):
        p = Proxy('login:password@210.173.88.77:3001')
        self.assertEqual(p.login, 'login')
        self.assertEqual(p.username, 'login')

    def test_password(self):
        self.assertEqual(Proxy('login:password@210.173.88.77:3001').password, 'password')

    def test_protocol(self):
        self.assertEqual(Proxy('login:password@210.173.88.77:3001').protocol, 'http')
        self.assertEqual(Proxy('socks5://login:password@210.173.88.77:3001').protocol, 'socks5')

    def test_url(self):
        self.assertEqual(Proxy('210.173.88.77:3001:login:password').url, 'http://login:password@210.173.88.77:3001')
        self.assertEqual(Proxy('socks5://210.173.88.77:3001:login:password').url, 'socks5://login:password@210.173.88.77:3001')

    def test_dict(self):
        d1 = {
            'http': 'http://login:password@210.173.88.77:3001',
            'https': 'http://login:password@210.173.88.77:3001',
        }
        d2 = {'socks5': 'socks5://login:password@210.173.88.77:3001'}
        self.assertEqual(Proxy('210.173.88.77:3001:login:password').dict, d1)
        self.assertEqual(Proxy('210.173.88.77:3001:login:password').proxies, d1)
        self.assertEqual(Proxy('socks5://210.173.88.77:3001:login:password').dict, d2)
        self.assertEqual(Proxy('socks5://210.173.88.77:3001:login:password').proxies, d2)

    def test_server(self):
        self.assertEqual(Proxy('socks5://210.173.88.77:3001:login:password').server, 'socks5://210.173.88.77:3001')
        self.assertEqual(Proxy('210.173.88.77:3001:login:password').server, 'http://210.173.88.77:3001')

    def test_playwright(self):
        r1 = PlaywrightProxySettings(
            server='http://210.173.88.77:3001',
            password='password',
            username='login',
        )
        r2 = PlaywrightProxySettings(
            server='http://210.173.88.77:3001',
            password=None,
            username=None,
        )
        self.assertEqual(Proxy('210.173.88.77:3001:login:password').playwright, r1)
        self.assertEqual(Proxy('210.173.88.77:3001').playwright, r2)

    def test_rotate(self):
        p = Proxy('login:password@210.173.88.77:3001[https://github.com]')
        self.assertTrue(p.rotate())
        self.assertTrue(asyncio.run(p.arotate()))
        self.assertTrue(p.refresh())
        self.assertTrue(asyncio.run(p.arefresh()))

    def test_string(self):
        self.assertTrue(isinstance(Proxy('210.173.88.77:3001'), str))

    def test_pydantic(self):
        self.assertTrue(isinstance(Account(proxy=Proxy('210.173.88.77:3001')).proxy, Proxy))
        self.assertTrue(isinstance(Account(proxy='210.173.88.77:3001').proxy, Proxy))


if __name__ == '__main__':
    unittest.main()

