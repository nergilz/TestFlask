import os
import time
from multiprocessing import cpu_count
from multiprocessing.util import Finalize
from random import choice, randint

import requests
from billiard.pool import Pool
from lxml import html
from requests.exceptions import SSLError, ConnectionError
from selenium import webdriver
from selenium.common.exceptions import TimeoutException

USER_AGENTS = [
    ('Mozilla/5.0 (X11; Linux x86_64) '
     'AppleWebKit/537.36 (KHTML, like Gecko) '
     'Chrome/57.0.2987.110 '
     'Safari/537.36'),  # chrome
    ('Mozilla/5.0 (X11; Linux x86_64) '
     'AppleWebKit/537.36 (KHTML, like Gecko) '
     'Chrome/61.0.3163.79 '
     'Safari/537.36'),  # chrome
    ('Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:55.0) '
     'Gecko/20100101 '
     'Firefox/55.0'),  # firefox
    ('Mozilla/5.0 (X11; Linux x86_64) '
     'AppleWebKit/537.36 (KHTML, like Gecko) '
     'Chrome/61.0.3163.91 '
     'Safari/537.36'),  # chrome
    ('Mozilla/5.0 (Windows NT 6.3; Win64; x64) '
     'AppleWebKit/537.36 (KHTML, like Gecko) '
     'Chrome/63.0.3239.84 Safari/537.36')
]


class Spider:
    def __init__(self):
        self.proxy_list = list()
        self.proxy_list = self.get_proxy_list()
        self.chrome_path = None

    def get_proxy_list(self):
        '''
        Parse proxelist of site (https://premium.freeproxy.ru/) or get from file
        :return: list
        '''
        if not os.path.exists('./proxylist.txt'):
            session = requests.Session()
            session.get('http://premium.freeproxy.ru/?code=B8B6-BDDB-422C-772C-0E8D-ECFC-F1A8-583A'
                        '&login_email=evil-lol%40mail.ru')
            r = session.get(
                'http://premium.freeproxy.ru/proxies/?type%5B%5D=HTTP&type%5B%5D=HTTPS&anon%5B%5D=HIA&anon%5B%5D='
                'ANM&ports=&sort_by=speed&sort_order=desc&per_page=1000'
            )
            tree = html.fromstring(r.content)
            ip_adresses = tree.xpath('//td[@class="ip"]/text()')
            ports = tree.xpath('//td[@class="port"]/text()')
            speed = tree.xpath('//div[@class="speed-label"]/text()')
            uptime = tree.xpath('//td[@class="uptime"]/text()')
            uptime = [item.strip() for item in uptime]
            for ip_adress in ip_adresses:
                ip_uptime = int(uptime[ip_adresses.index(ip_adress)].replace('%', ''))
                ip_speed = speed[ip_adresses.index(ip_adress)]
                if int(ip_uptime) > 80 and (('MB/S' in ip_speed) or (('KB/S' in ip_speed) and
                                                                     (int(ip_speed.split(' ')[0]) > 100))):
                    self.proxy_list.append('%s:%s' % (ip_adress, ports[ip_adresses.index(ip_adress)]))
            return self.proxy_list
        else:
            with open('./proxylist.txt', 'r', encoding='utf-8') as proxylist_file:
                proxy_list = proxylist_file.readlines()
                self.proxy_list = [proxy.strip() for proxy in proxy_list]
            return self.proxy_list

    def get_html(self, url, cookies=None):
        '''
        Get HTML via randomized proxy
        :param url: str
        :return: Requests Object
        '''
        useragent = {'User-Agent': choice(USER_AGENTS)}
        ip_port = choice(self.proxy_list)
        proxy = {'http': 'http://%s' % (ip_port)}
        print('Use proxy: %s for URL: %s' % (proxy['http'], url))
        with requests.Session() as session:
            result = dict(request=None, proxy=proxy, ip_port=ip_port)
            try:
                if cookies:
                    r = session.get(url, headers=useragent, proxies=proxy, cookies=cookies)
                else:
                    r = session.get(url, headers=useragent, proxies=proxy)
                if 'avito' in url:
                    while b'captcha' in r.content:
                        result = self.rotate_proxy(url, result['ip_port'], result['proxy'], useragent)
                        r = result['request']
                    return r
                elif 'cian' in url:
                    while b'Captcha' in r.content:
                        result = self.rotate_proxy(url, result['ip_port'], result['proxy'], useragent)
                        r = result['request']
                    return r
                elif 'yandex' in url:
                    while b'captcha' in r.content:
                        result = self.rotate_proxy(url, result['ip_port'], result['proxy'], useragent)
                        r = result['request']
                    return r
            except (SSLError, ConnectionError):
                result = self.rotate_proxy(url, result['ip_port'], result['proxy'], useragent)
                r = result['request']
                return r

    def rotate_proxy(self, url, ip_port, proxy, useragent):
        '''
        Rotate proxy
        :param url: str
        :param ip_port: str
        :param proxy: dict
        :param useragent: dict
        :return: dict
        '''
        if self.proxy_list:
            print('Proxy %s is banned! Removing..' % (proxy['http']))
            self.proxy_list.remove(ip_port)
            ip_port = choice(self.proxy_list)
            proxy = {'http': 'http://%s' % (ip_port)}
            print('Use proxy: %s for URL: %s' % (proxy['http'], url))
            session = requests.Session()
            time.sleep(randint(10, 30))
            r = session.get(url, headers=useragent, proxies=proxy)
            return dict(request=r, proxy=proxy, ip_port=ip_port)
        else:
            raise ProxyExhaustedException('Proxylist exhausted!')

    def prettify_result(self, item_links_list):
        '''
        Create list from list of lists... lol))
        :param item_links_list: list
        :return: list
        '''
        item_links = list()
        for _list in item_links_list:
            for link in _list:
                item_links.append(link)
        return item_links

    def extract_with_exception(self, item_dict, key):
        '''
        Extract data or retutns None
        :param item_dict: dict
        :param key: str
        :return: str or None
        '''
        try:
            result = item_dict[key]
            return result
        except KeyError:
            return None

    def extractor_pool(self, func, iterable):
        '''
        Extract items (billard multiprocessing use)
        :param func: function
        :param iterable: list
        '''
        _finalizers = list()
        p = Pool(processes=cpu_count())
        _finalizers.append(Finalize(p, p.terminate))
        try:
            p.map_async(func, iterable)
            p.close()
            p.join()
        finally:
            p.terminate()

    def create_browser(self):
        '''
        Create Chrome browser
        :return: object Selenium browser
        '''
        self.chrome_options = webdriver.ChromeOptions()
        proxy = choice(self.proxy_list)
        # need fast proxies
        # print('Browser use proxy: %s' % (proxy))
        # self.chrome_options.add_argument('--proxy-server=%s' % (proxy))
        # self.chrome_options.add_argument('--headless --disable-gpu --proxy-server=%s' % (proxy))
        self.chrome_options.add_argument('--headless --disable-gpu')
        browser = webdriver.Chrome(executable_path=self.chrome_path, chrome_options=self.chrome_options)
        return browser

    def extract_first(self, tree, xpath):
        '''
        Extract from xpath frist element
        :param tree: object lxml tree
        :param xpath: str
        :return: str or None
        '''
        data = tree.xpath(xpath)
        if data:
            return data[0]
        else:
            return None

    def check_connection(self, tree, xpath, url, browser):
        working = self.extract_first(tree, xpath)
        while working is None:
            browser.close()
            for item in self.chrome_options.arguments:
                if '--proxy-server' in item:
                    cur_proxy = item.split('=')[1]
                    print('Proxy %s removed cause bad connection (%s) \n'
                          ' URL %s' % (cur_proxy, len(self.proxy_list), url))
                    self.proxy_list.remove(cur_proxy)
                    if not self.proxy_list:
                        self.proxy_list = self.get_proxy_list()
            browser = self.create_browser()
            while True:
                try:
                    browser.get(url)
                except TimeoutException:
                    browser.close()
                    browser = self.create_browser()
                    browser.get(url)
                else:
                    break
            tree = html.fromstring(browser.page_source)
            working = self.extract_first(tree, xpath)
        return browser

    def search_payments(self, url, payment_data):
        '''
        Return string of payments
        :param url: str
        :return: str or None
        '''
        payments = None
        for item in payment_data:
            if item['url'] == url:
                payments = item['payments']
        if payments:
            if len(payments) > 1:
                result = ', '.join(payments)
            elif len(payments) == 1:
                result = payments[0]
            else:
                result = None
        else:
            result = None
        return result


class ProxyExhaustedException(Exception):
    def __init__(self, text):
        ProxyExhaustedException.txt = text


if __name__ == '__main__':
    spider = Spider()
