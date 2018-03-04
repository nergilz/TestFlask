from multiprocessing import cpu_count
from multiprocessing.util import Finalize

from billiard.pool import Pool
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


class Spider:
    def __init__(self):
        self.chrome_options = webdriver.ChromeOptions()

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
        browser = webdriver.Remote(command_executor='http://selenium-hub:4444/wd/hub',
                                   desired_capabilities=DesiredCapabilities.CHROME)
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


if __name__ == '__main__':
    spider = Spider()
