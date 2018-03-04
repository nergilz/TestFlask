import re
import time
from datetime import datetime, date, timedelta
from random import randint

from lxml import html
from selenium.common.exceptions import ElementNotVisibleException

from realty_parser.models import ItemsDB
from realty_parser.spiders.spider import Spider


class CianSpider(Spider):
    start_urls = [
        'https://sochi.cian.ru/kupit-kvartiru-studiu/',
        'https://sochi.cian.ru/kupit-1-komnatnuyu-kvartiru/',
        'https://sochi.cian.ru/kupit-2-komnatnuyu-kvartiru/',
        'https://sochi.cian.ru/kupit-4-komnatnuyu-kvartiru/',
        'https://sochi.cian.ru/kupit-5-komnatnuyu-kvartiru/',
        'https://sochi.cian.ru/kupit-mnogkomnatnuyu-kvartiru/',
        'https://sochi.cian.ru/kupit-kvartiru-svobodnoy-planirovki/'
    ]

    # Server failures occur at 0
    DOWNLOAD_DELAY = randint(3, 6)

    def __init__(self):
        super().__init__()
        self.database = ItemsDB()
        self.database.create_db()

    def parse(self):
        '''
        Main parse method
        :return: None
        '''
        self.extractor_pool(func=self.browser_exractor, iterable=self.start_urls)
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
        pages_links = tree.xpath('//ul[@class="list--35Suf"]/li/a/text()')
        pages_num_list = list()
        pages_num_list.append('1')
        if '..' not in pages_links:
            item_list = browser.find_elements_by_xpath('//a[@class="headerLink--1HdU8"]')
            for item in item_list:
                try:
                    item.click()
                except ElementNotVisibleException:
                    browser.find_elements_by_xpath('//div[@class="button--3JzvW"]')[0].click()
                    item.click()
                pages_num_list.append(item.text)
                self.parse_item(browser)
            pages = browser.find_elements_by_xpath('//ul[@class="list--35Suf"]/li/a')
            for page in pages:
                pages = browser.find_elements_by_xpath('//ul[@class="list--35Suf"]/li/a')
                if page.text not in pages_num_list:
                    pages.remove(page)
                    page.click()
                    time.sleep(self.DOWNLOAD_DELAY)
                    item_list = browser.find_elements_by_xpath('//a[@class="headerLink--1HdU8"]')
                    for item in item_list:
                        try:
                            item.click()
                        except ElementNotVisibleException:
                            browser.find_elements_by_xpath('//div[@class="button--3JzvW"]')[0].click()
                            item.click()
                        pages_num_list.append(item.text)
                        self.parse_item(browser)
                    time.sleep(self.DOWNLOAD_DELAY)
        else:
            while '..' in pages_links[-1]:
                time.sleep(self.DOWNLOAD_DELAY)
                tree = html.fromstring(browser.page_source)
                pages_links = tree.xpath('//ul[@class="list--35Suf"]/li/a/text()')
                for elem in browser.find_elements_by_xpath('//ul[@class="list--35Suf"]/li/a'):
                    if (elem.text != '..') and (elem.text not in pages_num_list):
                        item_list = browser.find_elements_by_xpath('//a[@class="headerLink--1HdU8"]')
                        for item in item_list:
                            try:
                                item.click()
                            except ElementNotVisibleException:
                                browser.find_elements_by_xpath('//div[@class="button--3JzvW"]')[0].click()
                                item.click()
                            pages_num_list.append(item.text)
                            self.parse_item(browser)
                        elem.click()
                        time.sleep(self.DOWNLOAD_DELAY)
        browser.close()
        return True

    def parse_item(self, browser):
        '''
        Parse realty URL
        :param item_link: str
        :return: dict
        '''
        time.sleep(self.DOWNLOAD_DELAY)
        browser.switch_to_window(browser.window_handles[-1])
        tree = html.fromstring(browser.page_source)
        url = browser.current_url
        site = 'cian'
        obj_desc_prop = self._get_object_desc_props(tree)
        try:
            total_square = re.search(r'([0-9,-]+)', obj_desc_prop['Общая площадь']).group(0).replace(',', '.')
        except KeyError:
            total_square = tree.xpath(
                '//div[@class="info--2dqct"][1]/div[@class="info-text--3GGPV"]/text()'
            )[0].replace(' м²', '').replace(',', '.').replace(' ', '')
        try:
            price = tree.xpath('//*[@id="price_rur"]/text()')[0].split(',')[0]
        except IndexError:
            price = re.search('"offerPrice":(\d+)', browser.page_source).group(0).split(':')[1]
        price_per_meter = int(float(price) // float(total_square))
        rooms_square = self.extract_with_exception(obj_desc_prop, 'Площадь комнат')
        living_square = self.extract_with_exception(obj_desc_prop, 'Жилая площадь')
        kitchen_square = self.extract_with_exception(obj_desc_prop, 'Площадь кухни')
        if 'Санузел' in obj_desc_prop.keys():
            wc = obj_desc_prop['Санузел']
        elif 'Совмещенных санузлов' in obj_desc_prop.keys():
            wc = obj_desc_prop['Совмещенных санузлов']
        elif 'Совмещённый санузел' in obj_desc_prop.keys():
            wc = obj_desc_prop['Совмещённый санузел']
        elif 'Раздельных санузлов' in obj_desc_prop.keys():
            wc = obj_desc_prop['Раздельных санузлов']
        else:
            wc = None
        balcony = self.extract_with_exception(obj_desc_prop, 'Балкон')
        elevator = self.extract_with_exception(obj_desc_prop, 'Лифт')
        parking = self.extract_with_exception(obj_desc_prop, 'Парковка')
        window_look = self.extract_with_exception(obj_desc_prop, 'Вид из окна')
        issue_date = self.extract_with_exception(obj_desc_prop, 'Сдача ГК')
        try:
            house_type = obj_desc_prop['Тип дома'].split(',')[0]
            matherial_type = obj_desc_prop['Тип дома'].split(',')
            matherial_type = matherial_type[1].strip() if len(matherial_type) == 2 else matherial_type[0].strip()
        except KeyError:
            house_type = self.extract_with_exception(obj_desc_prop, 'Тип жилья')
            matherial_type = None
        try:
            floor = obj_desc_prop['Этаж'].split('/')[0]
            floors = obj_desc_prop['Этаж'].split('/')[1].replace(')', '').strip()
        except KeyError:
            floor = '-'
            floors = '-'
        except IndexError:
            floor = self.extract_with_exception(obj_desc_prop, 'Этаж')
            floors = self.extract_with_exception(obj_desc_prop, 'Этажей в доме')
        type_salary = self.extract_with_exception(obj_desc_prop, 'Тип продажи')
        adress_dict = self._get_adress(tree)
        region = adress_dict['region']
        city = adress_dict['city']
        district = self.extract_with_exception(adress_dict, 'district')
        microdistrict = self.extract_with_exception(adress_dict, 'microdistrict')
        street = self.extract_with_exception(adress_dict, 'street')
        house_num = self.extract_with_exception(adress_dict, 'house')
        JK_name = tree.xpath('*//div[@class="object_descr_title"]/a/text()')
        try:
            JK_name = JK_name[0] if JK_name else tree.xpath('//a[@class="link--36RM5 link--2izPK"]/text()')[0]
        except IndexError:
            JK_name = None
        try:
            seller_phone = re.search('(\W\d+ \d+ \d+-\d+-\d+)',
                                     tree.xpath('//div[@class="cf_offer_show_phone-number"]/a/text()')[0]).group(0)
        except IndexError:
            seller_phone = tree.xpath('//div[@class="print_phones--2T2Pz"]/a/text()')
            seller_phone = [phone.strip() for phone in seller_phone]
            seller_phone = seller_phone[0] if len(seller_phone) == 1 else ', '.join(seller_phone)
        offer_statuses = tree.xpath('//ul[@class="offerStatuses"]/li/a/text()')
        offer_statuses = [item.strip() for item in list(filter(None, offer_statuses))]
        premium_status = offer_statuses[0] if len(offer_statuses) == 1 else ', '.join(offer_statuses)
        try:
            up_date = tree.xpath('//span[@class="object_descr_dt_added"]/text()')[-1]
            if 'вчера' in up_date:
                up_date = str(date.today() - timedelta(days=1))
            elif 'сегодня' in up_date:
                up_date = str(date.today())
            else:
                up_date_list = up_date.split(' ')
                if len(up_date_list) > 1:
                    monhts_dict = {
                        'янв': '01', 'фев': '02', 'мар': '03', 'апр': '04', 'май': '05', 'июн': '06',
                        'июл': '07', 'авг': '08', 'сен': '09', 'окт': '10', 'ноя': '11', 'дек': '12'
                    }
                    up_date_list[1] = up_date_list[1].replace(',', '')
                    up_date = '%s-%s-%s' % (datetime.now().year, monhts_dict[up_date_list[1]], up_date_list[0])
        except IndexError:
            up_date = tree.xpath('//div[@class="container--3Y9rb"]/text()')
            if up_date:
                up_date = up_date[0].split(',')[0]
                up_date = date.today() if 'сегодня' in up_date else up_date
                up_date = str(date.today() - timedelta(days=1)) if 'вчера' == up_date else up_date
                try:
                    up_date_list = up_date.split(' ')
                except AttributeError:
                    pass
                else:
                    if len(up_date_list) > 1:
                        up_date_list[1] = up_date_list[1].replace(',', '')
                        monhts_dict = {
                            'янв': '01', 'фев': '02', 'мар': '03', 'апр': '04', 'май': '05', 'июн': '06',
                            'июл': '07', 'авг': '08', 'сен': '09', 'окт': '10', 'ноя': '11', 'дек': '12'
                        }
                        up_date = '%s-%s-%s' % (datetime.now().year, monhts_dict[up_date_list[1]], up_date_list[0])
            else:
                up_date = None
        decoration = self.extract_with_exception(obj_desc_prop, 'Отделка')
        try:
            publish_date = re.search(r'\"publication_date\": (\d+)', browser.page_source).group(0).split(' ')[1]
            publish_date = datetime.fromtimestamp(int(publish_date)).strftime('%Y-%m-%d')
        except AttributeError:
            try:
                publish_date = re.search(r'\"publicationDate\":(\d+)', browser.page_source).group(0).split(':')[1]
                publish_date = datetime.fromtimestamp(int(publish_date)).strftime('%Y-%m-%d')
            except AttributeError:
                publish_date = datetime.now().date()
        try:
            ad_text = tree.xpath('//div[@class="object_descr_text"]/text()')[0].strip()
        except IndexError:
            ad_text = tree.xpath('//p[@class="description-text--3SshI"]/text()')
            if ad_text:
                ad_text = ad_text[0].strip()
            else:
                ad_text = None
        rooms = self._get_rooms(tree)
        try:
            views = tree.xpath('//div[@class="container--3kg1i"]/text()')[0].strip()
        except IndexError:
            views = None

        browser.close()
        browser.switch_to_window(browser.window_handles[-1])
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
        print(kwargs)
        return kwargs

    def _get_object_desc_props(self, selector):
        '''
        Parse object description properties
        :param selector: lxml selector
        :return: dict
        '''
        object_dict = dict()
        lenght = len(selector.xpath('//*[@class="object_descr_props flat sale"]//td'))
        if lenght != 0:
            for i in range(2, lenght + 2):
                option = selector.xpath('//*[@class="object_descr_props flat sale"]'
                                        '//tr[%s]/th/text()' % (i))[0].strip().replace(':', '')
                value = selector.xpath('//*[@class="object_descr_props flat sale"]//tr[%s]/td/text()' % (i))
                if value:
                    value = [item.strip().replace('\xa0', ' ') for item in value]
                    value = list(filter(None, value))[0].strip()
                else:
                    value = '-'
                object_dict.update([(option, value)])
        else:
            keys = selector.xpath('//span[@class="name--2EeYd"]/text()')
            values = selector.xpath('//span[@class="value--14qS3"]/text()')
            object_dict = dict(zip(keys, values))
        return object_dict

    def _get_rooms(self, selector):
        '''
        Type of realty
        :param selector: lxml selector
        :return: str
        '''
        rooms_text = None
        try:
            rooms_text = selector.xpath('//*[@class="object_descr_title"]/text()')[0].strip()
            room = re.search(r'(\d+)', rooms_text).group(0)
            return room
        except AttributeError:
            if 'Студия' in rooms_text:
                return 'Студия'
            else:
                return 'Свобоной планировки'
        except IndexError:
            room = selector.xpath('//h1[@class="title--2oO4e"]/text()')[0].split(',')[0]
            try:
                room = re.search(r'(\d+)', room).group(0)
                return room
            except AttributeError:
                return room

    def _get_adress(self, selector):
        '''
        Extract adress of realty
        :param selector: lxml selector
        :return: dict
        '''
        keys = ['region', 'city', 'district']
        values = selector.xpath('*//h1/a/text()')
        if len(values) == 0:
            values = selector.xpath('//a[@class="link--36RM5 address-item--1jDfG"]/text()')
        object_dict = dict(zip(keys, values[:3]))
        if len(values) == 6:
            object_dict.update([('microdistrict', values[3])])
            object_dict.update([('street', values[4])])
            object_dict.update([('house', values[5])])
        elif len(values) == 5:
            if 'ул' in values[3]:
                object_dict.update([('microdistrict', None)])
                object_dict.update([('street', values[3])])
                object_dict.update([('house', values[4])])
            else:
                object_dict.update([('microdistrict', values[3])])
                object_dict.update([('street', values[4])])
        else:
            if 'мкр' in values[3]:
                object_dict.update([('district', values[3])])
            else:
                object_dict.update([('street', values[3])])
        return object_dict


if __name__ == '__main__':
    spider = CianSpider()
    spider.parse()
