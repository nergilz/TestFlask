import base64
import os
import re
import sys
import time
from datetime import date, timedelta
from random import randint

from PIL import Image
from lxml import html
from pytesseract import image_to_string
from selenium.common.exceptions import NoSuchElementException

from realty_parser_req.realty_peeewee import ItemsDB
from realty_parser_req.terrarium.spider import Spider


class AvitoSpider(Spider):
    start_urls = [
        'https://www.avito.ru/sochi/kvartiry/prodam',
    ]

    # if DOWNLOAD_DELAY < 10 we get ban
    DOWNLOAD_DELAY = randint(3, 6)

    def __init__(self):
        super().__init__()
        self.database = ItemsDB()
        self.database.create_db()
        self.payments_data = list()
        if sys.platform == 'linux':
            self.chrome_path = './driver/linux64_chromedriver'
        elif sys.platform == 'darwin':
            self.chrome_path = './driver/mac_chromedriver'
        else:
            self.chrome_path = './driver/win32_chromedriver.exe'

    def parse(self):
        '''
        Main parse method
        :return: None
        '''
        if sys.platform == 'linux':
            from pyvirtualdisplay import Display
            display = Display(visible=0, size=(1024, 768))
            display.start()
            self.extractor_pool(self.browser_exractor, self.start_urls, item=True)
            display.stop()
        else:
            self.extractor_pool(self.browser_exractor, self.start_urls, item=True)
        return None

    def browser_exractor(self, url):
        '''
        Follow by links and extract ad data
        :param url: str
        :return: bool
        '''
        browser = self.create_browser()
        time.sleep(self.DOWNLOAD_DELAY)
        browser.get(url)
        tree = html.fromstring(browser.page_source)
        pages_links = tree.xpath('//div[@class="pagination-nav clearfix"]/a/text()')[0]
        while 'Следующая страница →' in pages_links:
            time.sleep(self.DOWNLOAD_DELAY)
            tree = html.fromstring(browser.page_source)
            try:
                pages_links = tree.xpath('//div[@class="pagination-nav clearfix"]/a/text()')[1]
            except IndexError:
                pass
            self.payments_data += self._get_ad_payments(tree)
            before_google_ads_items = tree.xpath(self.before_google_ads_items_xhs)
            for num_ad in range(1, len(before_google_ads_items) + 1):
                browser.find_element_by_xpath(self.before_google_ads_items_xhs + '[%s]//a' % (num_ad)).click()
                self.parse_item(browser)
            after_google_ads_items = tree.xpath(self.after_google_ads_items_xhs)
            for num_ad in range(1, len(after_google_ads_items) + 1):
                browser.find_element_by_xpath(self.after_google_ads_items_xhs + '[%s]//a' % (num_ad)).click()
                self.parse_item(browser)
            browser.find_element_by_xpath('//a[@class="pagination-page js-pagination-next"]').click()
            tree = html.fromstring(browser.page_source)
            pages_links = tree.xpath('//div[@class="pagination-nav clearfix"]/a/text()')[1]
        browser.close()
        return True

    # TODO: использовать extract_with_exception, extract_from_xpath
    def parse_item(self, browser):
        '''
        Parse realty URL
        :param item_link: str
        :return: dict
        '''
        tree = html.fromstring(browser.page_source)
        url = browser.current_url
        site = 'avito'
        item_desc_data = self._get_item_props(tree)
        total_square = self.extract_with_exception(item_desc_data, 'Общая площадь')
        try:
            price = tree.xpath('//span[@class="price-value-string js-price-value-string"]'
                               '/text()')[0].strip().replace(' ', '')
            price_per_meter = tree.xpath(
                '//li[@class="price-value-prices-list-item price-value-prices-list-item_size-small '
                'price-value-prices-list-item_pos-between"]/text()')[0].strip().replace('\u2009', '')
            price_per_meter = re.search('(\d+)', price_per_meter).group(0)
        except IndexError or KeyError:
            price = None
            price_per_meter = None
        rooms_square = self.extract_with_exception(item_desc_data, 'Общая площадь')
        living_square = self.extract_with_exception(item_desc_data, 'Жилая площадь')
        kitchen_square = self.extract_with_exception(item_desc_data, 'Площадь кухни')
        wc = None
        balcony = None
        elevator = None
        parking = None
        window_look = None
        issue_date = None
        house_type = None
        matherial_type = self.extract_with_exception(item_desc_data, 'Тип дома')
        floor = self.extract_with_exception(item_desc_data, 'Этаж')
        floors = self.extract_with_exception(item_desc_data, 'Этажей в доме')
        type_salary = self.extract_with_exception(item_desc_data, 'Тип участия')
        adress_data = self._get_adress(tree)
        region = adress_data['region']
        city = adress_data['city']
        district = adress_data['district']
        microdistrict = None
        street = adress_data['street']
        house_num = adress_data['house']
        JK_name = self.extract_with_exception(item_desc_data, 'Название объекта недвижимости')
        phone_publish = self._get_phone_publish_date(browser)
        seller_phone = phone_publish['phone']
        premium_status = self.search_payments(url, self.payments_data)
        up_date = None
        if premium_status and 'Объявление поднято' in premium_status:
            up_date_data = premium_status.split(',')
            for item in up_date_data:
                if 'Объявление поднято' in item:
                    up_date = item
        try:
            views = self.extract_first(tree, '//a[@class="js-show-stat pseudo-link"]/text()')
            views = views.strip().split(' ')[0] if views else views
        except IndexError:
            views = self.extract_first(tree, '//span[@class="title-info-views"]/text()')
            views = views.strip().split(' ')[0] if views else views
        publish_date = phone_publish['publish_date']
        ad_text_data = tree.xpath('//div[@itemprop="description"]/p/text()')
        try:
            ad_text = ' '.join(ad_text_data) if len(ad_text_data) > 1 else ad_text_data[0]
        except IndexError:
            ad_text = 'Error'
        rooms = None
        decoration = None
        kwargs = {
            'url': url, 'site': site, 'price': price, 'price_per_meter': price_per_meter, 'rooms': rooms,
            'total_square': total_square, 'rooms_square': rooms_square, 'living_square': living_square,
            'kitchen_square': kitchen_square, 'wc': wc, 'balcony': balcony, 'elevator': elevator, 'parking': parking,
            'window_look': window_look, 'issue_date': issue_date, 'house_type': house_type,
            'matherial_type': matherial_type, 'floor': floor, 'floors': floors, 'type_salary': type_salary,
            'region': region, 'city': city, 'district': district, 'microdistrict': microdistrict, 'street': street,
            'house_num': house_num, 'JK_name': JK_name, 'seller_phone': seller_phone, 'premium_status': premium_status,
            'publish_date': publish_date, 'up_date': up_date, 'decoration': decoration, 'ad_text': ad_text,
            'views': views
        }
        self.database.add_item(**kwargs)
        browser.back()
        print(kwargs)
        return kwargs

    def _get_pagination_links(self, url):
        '''
        Extract pagination links
        :param url: str
        :return: list
        '''
        pagination_links = list()
        pagination_links.append(url)
        domain_adress = 'https://www.avito.ru'
        request = self.get_html(url)
        tree = html.fromstring(request.content)
        next_link = tree.xpath('//a[@class="pagination-page"]/@href')[0]
        last_link = tree.xpath('//a[@class="pagination-page"]/@href')[-1]
        num_pages = int(re.search(r'p=(\d+)', last_link).group(0).replace('p=', ''))
        for page in range(2, num_pages + 1):
            page_prefix = re.search(r'p=(\d+)', next_link).group(0)
            link = next_link.replace(page_prefix, 'p=%s' % (page))
            pagination_links.append(domain_adress + link)
        return pagination_links

    def _get_items_links(self, url):
        '''
        Extract items links
        :param url: str
        :return: list
        '''
        payments = list()
        domain_adress = 'https://www.avito.ru'
        time.sleep(self.DOWNLOAD_DELAY)
        request = self.get_html(url)
        tree = html.fromstring(request.content)
        items_links = tree.xpath('//a[@class="item-description-title-link"]/@href')
        items_links = [domain_adress + item_link for item_link in items_links]
        for item in items_links:
            if 'redirect' in item:
                items_links.remove(item)
        payments.append(self._get_ad_payments(tree))
        return items_links, payments

    def _get_ad_payments(self, tree):
        '''
        Extract payments from ad's
        :param tree: object lxml
        :return: dict
        '''
        res = list()
        # Don't format, this string for xpath
        self.before_google_ads_items_xhs = '''//div[@class="js-catalog_before-ads"]//div[(@class="item item_table clearfix js-catalog-item-enum
    c-b-0   ") or (@class="item item_table clearfix js-catalog-item-enum
    item-highlight   ") or (@class="item item_table clearfix js-catalog-item-enum
 js-item-trackable js-item-extended item_table_extended  item-highlight   ") or 
 (@class="item item_table clearfix js-catalog-item-enum item-highlight") or 
 (@class="item item_table clearfix js-catalog-item-enum c-b-0") or 
 (@class="item item_table clearfix js-catalog-item-enum js-item-trackable js-item-extended item_table_extended item-highlight")]'''
        before_google_ads_items = tree.xpath(self.before_google_ads_items_xhs)
        for num_ad in range(1, len(before_google_ads_items) + 1):
            url = 'https://www.avito.ru' + \
                  tree.xpath(self.before_google_ads_items_xhs +
                             '[%s]//a[@class="item-description-title-link"]/@href' % (num_ad))[0]
            payments = tree.xpath(self.before_google_ads_items_xhs + '[%s]//div[@class="vas-applied"]/a/@title' % (num_ad))
            for item in payments:
                if 'сегодня' in item:
                    item_data = payments.pop(payments.index(item))
                    today_date = str(date.today())
                    payments.append(item_data.replace('сегодня', today_date))
                elif 'вчера' in item:
                    item_data = payments.pop(payments.index(item))
                    yesterday_date = str(date.today() - timedelta(days=1))
                    payments.append(item_data.replace('вчера', yesterday_date))
            res.append({'url': url, 'payments': payments})
        self.after_google_ads_items_xhs = self.before_google_ads_items_xhs.replace('before', 'after')
        self.after_google_ads_items = tree.xpath(self.after_google_ads_items_xhs)
        for num_ad in range(1, len(self.after_google_ads_items) + 1):
            url = 'https://www.avito.ru' + \
                  tree.xpath(self.after_google_ads_items_xhs +
                             '[%s]//a[@class="item-description-title-link"]/@href' % (num_ad))[0]
            payments = tree.xpath(self.after_google_ads_items_xhs + '[%s]//div[@class="vas-applied"]/a/@title' % (num_ad))
            for item in payments:
                if 'сегодня' in item:
                    item_data = payments.pop(payments.index(item))
                    today_date = str(date.today())
                    payments.append(item_data.replace('сегодня', today_date))
                elif 'вчера' in item:
                    item_data = payments.pop(payments.index(item))
                    yesterday_date = str(date.today() - timedelta(days=1))
                    payments.append(item_data.replace('вчера', yesterday_date))
            res.append({'url': url, 'payments': payments})
        return res

    def _prettify_items_data(self, item_data):
        '''
        Nomalize data structure
        :param item_data: list
        :return: tuple
        '''
        item_links = list()
        payment_list = list()
        for item in item_data:
            item_links.append(item[0])
            for payment_item in item[1]:
                for payment in payment_item:
                    payment_list.append(payment)
        item_links = self.prettify_result(item_links)
        return item_links, payment_list

    def _get_item_props(self, tree):
        '''
        Extract item props
        :param tree: object xpath tree
        :return: dict
        '''
        values = tree.xpath('//ul[@class="item-params-list"]/li/text()')
        attrs = tree.xpath('//ul[@class="item-params-list"]/li/span/text()')
        values = list(filter(None, [value.strip().replace('\xa0м²', '') for value in values]))
        attrs = [attr.strip().replace(':', '') for attr in attrs]
        res = dict(zip(attrs, values))
        return res

    def _get_adress(self, tree):
        '''
        Extract adress of item
        :param tree: object xpath tree
        :return: dict
        '''
        keys = ['region', 'city', 'district', 'street', 'house']
        data = tree.xpath('//div[@class="item-map-location"]//span[@itemprop="name"]/text()')
        data += tree.xpath('//div[@class="item-map-location"]/span[@itemprop="address"]/span/text()')
        data += tree.xpath('//div[@class="item-map-location"]//span[@itemprop="streetAddress"]/text()')
        data = [item.strip() for item in data]
        adress = dict(zip(keys, data))
        if (adress.get('district')) and ',' in adress['district']:
            adress['district'] = adress['district'].split(',')[1].strip()
        try:
            if 'д.' in adress['street']:
                adress.update({'house': adress['street'].split('д.')[1].strip()})
            elif ',' in adress['street']:
                adress.update({'house': adress['street'].split(',')[1].strip()})
            else:
                adress.update({'house': None})
        except KeyError:
            adress.update({'street': None, 'house': None})
        return adress

    def _get_phone_publish_date(self, browser):
        '''
        Extract phone number and publish date via Chrome
        :param url: str
        :return: dict
        '''
        while True:
            try:
                browser.find_element_by_xpath('//div[@class="item-phone-number js-item-phone-number"]').click()
            except NoSuchElementException:
                print('err')
                time.sleep(3)
            else:
                break
        while True:
            try:
                phone_img = browser.find_element_by_xpath(
                    '//div[@class="item-phone-number js-item-phone-number"]/button/img'
                ).get_property('src').split(',')[1]
            except NoSuchElementException:
                time.sleep(3)
            else:
                break
        phone_img = bytes(phone_img, encoding='utf-8')
        tesser_config = '--tessdata-dir "C:\\Program Files (x86)\\Tesseract-OCR\\tessdata"'
        with open(os.path.join(os.path.abspath(os.curdir), 'phonenum.png'), 'wb') as phone_file:
            phone_file.write(base64.decodebytes(phone_img))
        img_to_convert = Image.open(os.path.join(os.path.abspath(os.curdir), 'phonenum.png'))
        if sys.platform == 'linux' or 'darwin':
            res = image_to_string(img_to_convert).replace('O', '0').replace('-', '').replace(' ', '')
        else:
            res = image_to_string(img_to_convert, config=tesser_config).replace('O', '0').replace('-', '').replace(' ',
                                                                                                                   '')
        browser.refresh()
        try:
            browser.find_element_by_xpath('//a[@class="js-show-stat pseudo-link"]').click()
            time.sleep(2)
            pub_date = browser.find_element_by_xpath('//div[@class="item-stats__date"]/strong').text
            monhts_dict = {'января': '01', 'февраля': '02', 'марта': '03', 'апреля': '04', 'мая': '05', 'июня': '06',
                           'июля': '07', 'августа': '08', 'сентября': '09', 'октября': '10', 'ноября': '11',
                           'декабря': '12'}
            pub_date_list = pub_date.strip().split(' ')
            pub_date = '%s-%s-%s' % (pub_date_list[2], monhts_dict[pub_date_list[1]], pub_date_list[0])
        except NoSuchElementException:
            pub_date = date.today()
        data = {'phone': res, 'publish_date': pub_date}
        return data


if __name__ == '__main__':
    spider = AvitoSpider()
    spider.parse()
    # spider.browser_exractor('https://www.avito.ru/sochi/kvartiry/prodam')
    # spider._get_items_links('https://www.avito.ru/sochi/kvartiry/prodam')
    # spider.parse_item('https://www.avito.ru/sochi/kvartiry/1-k_kvartira_29_m_24_et._1213229919')
    # print(spider._get_phone_publish_date('https://www.avito.ru/sochi/kvartiry/1-k_kvartira_27.6_m_44_et._1081765938'))
