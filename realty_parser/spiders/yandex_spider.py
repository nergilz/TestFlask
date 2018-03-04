import json
import re
import time
from datetime import date, timedelta
from random import randint

from lxml import html

from realty_parser.models import ItemsDB
from realty_parser.spiders.spider import Spider


class YandexSpider(Spider):
    start_urls = [
        'https://realty.yandex.ru/sochi/kupit/kvartira/'
    ]

    DOWNLOAD_DELAY = randint(5, 10)

    def __init__(self):
        super().__init__()
        self.database = ItemsDB()
        self.database.create_db()
        self.payments_data = list()

    def parse(self):
        self.extractor_pool(self.browser_exractor, self.start_urls)
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
        pages_links = tree.xpath('//div[@class="pager__links"]/a/span/text()')
        while 'Следующая' in pages_links:
            time.sleep(self.DOWNLOAD_DELAY)
            tree = html.fromstring(browser.page_source)
            pages_links = tree.xpath('//div[@class="pager__links"]/a/span/text()')
            self.payments_data += self._get_payments(browser.page_source)
            items_list = tree.xpath('//h3[@class="serp-item__head serp-item__row"]/a/@href')
            for item in range(1, len(items_list) + 1):
                time.sleep(self.DOWNLOAD_DELAY)
                browser.switch_to_window(browser.window_handles[-1])
                browser.find_element_by_xpath(
                    '//div[@class="serp-item stat i-bem serp-item_js_inited '
                    'stat_gate_yes stat_goal_yes stat_js_inited"][%s]//h3' % (item)
                ).click()
                self.parse_item(browser)
            browser.switch_to_window(browser.window_handles[-1])
            browser.find_element_by_xpath('//div[@class="pager__links"]/a[%s]' % (len(pages_links))).click()
            tree = html.fromstring(browser.page_source)
            pages_links = tree.xpath('//div[@class="pager__links"]/a/span/text()')
        browser.close()
        return True

    def parse_item(self, browser):
        '''
        Parse realty URL
        :param browser: object Selenium browser
        :return: dict
        '''
        time.sleep(self.DOWNLOAD_DELAY)
        browser.switch_to_window(browser.window_handles[-1])
        url = browser.current_url
        tree = html.fromstring(browser.page_source)
        site = 'yandex'
        total_square = self.extract_first(
            tree,
            '//div[@class="offer-card__feature offer-card__feature_name_total-area"]/div[1]/text()'
        )
        if total_square:
            total_square = total_square.split(' ')[0]
        total_square = float(total_square.replace(',', '.') if ',' in total_square else total_square)
        data_bem = self.extract_first(
            tree,
            '//div[@class="offer-card stat i-bem offer-card_js_inited stat_'
            'ecommerce_yes stat_gate_yes stat_goal_yes stat_js_inited"]/@data-bem'
        )

        data_bem = json.loads(data_bem) if data_bem else None
        price = self.extract_with_exception(data_bem['stat']['ecommerce']['load']['detail']['products'][0], 'price')
        price_per_meter = self.extract_first(tree, '//span[@class="offer-card__price-detail"]/text()')
        price_per_meter = price_per_meter.replace(' ', '').replace('\xa0', '')
        price_per_meter = int(re.search('(\d+)', price_per_meter).group(0))
        rooms_square = None
        living_square = self.extract_first(tree, '//div[@class="offer-card__feature offer-card'
                                                 '__feature_name_living-area"]/div/text()')
        kitchen_square = None
        wc = self.extract_first(tree, '//div[@class="offer-card__feature offer-card__feature_name_bathroom-unit"]'
                                      '/div/text()')
        balcony = self.extract_first(tree, '//div[@class="offer-card__feature '
                                           'offer-card__feature_name_balcony-type"]/div/text()')
        elevator = self.extract_first(tree, '//div[@class="offer-card__feature offer-card__'
                                            'feature_name_lift offer-card__feature_key_LIFT"]/div/text()')
        parking = self.extract_first(tree, '//div[@class="offer-card__feature offer-card__feature_name'
                                           '_parking-type"]/div/text()')
        window_look = self.extract_first(tree, '//div[@class="offer-card__feature offer-card__'
                                               'feature_name_window-view"]/div/text()')
        issue_date = None
        house_type = self.extract_first(tree, '//div[@class="offer-card__building-type"]/text()')
        if not house_type:
            house_type = 'вторичка'
        matherial_type = self.extract_first(
            tree,
            '//div[@class="offer-card__feature offer-card__feature_name_building-type offer-card__feature_key_'
            'BUILDING_TYPE"]/div/text()'
        )
        floor = self.extract_first(
            tree,
            '//div[@class="offer-card__feature offer-card__feature_name_floors-total-apartment"]/div/text()'
        )
        floor = floor.strip('из')[0] if floor else floor
        floors = self.extract_first(
            tree,
            '//div[@class="offer-card__feature offer-card__feature_name_'
            'floors-total-house offer-card__feature_key_FLOORS_COUNT"]/div/text()'
        )
        type_salary = None
        adress_dict = self._get_adress(tree)
        region = adress_dict['region']
        city = adress_dict['city']
        district = None
        microdistrict = adress_dict['district']
        street = adress_dict['street']
        house_num = adress_dict['house']
        JK_name = None
        data_bem = self.extract_first(
            tree,
            '//div[@class="phones__redirect popup-opener i-bem popup-opener_js_inited"]/@data-bem'
        )
        if not data_bem:
            browser.find_element_by_xpath('//div[@class="offer-card__contacts-phones-timetable"]').click()
            tree = html.fromstring(browser.page_source)
            seller_phone = self.extract_first(
                tree,
                '//div[@class="offer-card__contacts-phones-timetable"]/span/div/span/text()'
            )
        else:
            data_bem = json.loads(data_bem)
            seller_phone = self.extract_with_exception(
                data_bem['popup-opener']['content']['phonesPairs'][0], 'temporary'
            )
        premium_status = self.search_payments(url, self.payments_data)
        premium_status = premium_status.replace(', ', '') if premium_status is not None else premium_status
        up_pub_data = self._get_up_publish_date(tree)
        up_date = up_pub_data[0]
        publish_date = up_pub_data[1]
        views = self.extract_first(
            tree,
            '//div[@class="offer-card__views-count"]/text()'
        ).split(':')[1]
        ad_text = self.extract_first(tree, '//div[@class="offer-card__desc-text"]/text()')
        rooms = self.extract_first(
            tree,
            '//div[@class="offer-card__feature offer-card__feature_name_rooms-total"]/div/text()'
        )
        decoration = self.extract_first(
            tree,
            '//div[@class="offer-card__feature offer-card__feature_name_renovation"]/div/text()'
        )
        browser.close()
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
        print(kwargs)
        self.database.add_item(**kwargs)
        return kwargs

    def _get_payments(self, page_source):
        '''
        Extract payments of realty items
        :param page_source: str
        :return: list
        '''
        payments_list = list()
        tree = html.fromstring(page_source)
        items_links = tree.xpath('//h3[@class="serp-item__head serp-item__row"]/a/@href')
        items_links = ['https://realty.yandex.ru' + link for link in items_links]
        data_bem = tree.xpath('//div[@class="serp-item stat i-bem serp-item_js_inited stat_gate_yes '
                              'stat_goal_yes stat_js_inited"]/@data-bem')
        for item in data_bem:
            item_url = items_links[data_bem.index(item)]
            premium = self.extract_with_exception(json.loads(item)['stat']['gate']['statParams'], 'offer_services')
            premium = 'Премиум' if premium and ('premium' in premium) else None
            payments_list.append({'url': item_url, 'payments': premium})
        return payments_list

    def _get_adress(self, tree):
        '''
        Extract adress from realty item
        :param tree: object lxml tree
        :return: dict
        '''
        region = tree.xpath('//span[@class="breadcrumbs-list__link"]/a[1]/text()')[0]
        adress = tree.xpath('//h2[@class="offer-card__address ellipsis"]/text()')[0].split(',')
        city = adress[0]
        district = None
        street = None
        house = None
        for item in adress:
            if 'микрорайон' in item:
                district = item
            elif 'улица' or 'проспект' in item:
                street = item
            elif re.search('(\d+)', item):
                house = item
        adress_dict = {'region': region, 'city': city, 'district': district, 'street': street, 'house': house}
        return adress_dict

    def _get_up_publish_date(self, tree):
        '''
        Extract date up on top and publish date of ad
        :param tree: object lxlm tree
        :return: tuple
        '''
        pub_str = tree.xpath('//div[@class="offer-card__dates"]/text()')[0].replace('Объявление обновлено ', '')
        up_pub_lst = pub_str.split(',')
        monhts_dict = {'января': '01', 'февраля': '02', 'марта': '03', 'апреля': '04', 'мая': '05', 'июня': '06',
                       'июля': '07', 'августа': '08', 'сентября': '09', 'октября': '10', 'ноября': '11',
                       'декабря': '12'}
        if len(up_pub_lst) == 2:
            up_pub_lst = [item.strip() for item in up_pub_lst]
            up_date = up_pub_lst[0]
            if 'вчера' in up_date:
                up_date = str(date.today() - timedelta(days=1))
            elif ('сегодня' in up_date) or ('часа' in up_date) or ('часов' in up_date) or ('час' in up_date) or \
                    ('минуты' in up_date) or ('минуту' in up_date) or ('минут' in up_date):
                up_date = '%s-%s-%s' % (date.today().year, date.today().month, date.today().day)
            else:
                up_date = up_date.split(' ')
                up_date = '%s-%s-%s' % (date.today().year, monhts_dict[up_date[1]], up_date[0])
            pub_date = up_pub_lst[1] if len(up_pub_lst) == 2 else up_pub_lst[0].replace('Объявление размещено ', '')
            pub_date = pub_date.split(' ')
            if len(pub_date) == 3:
                pub_date = '%s-%s-%s' % (date.today().year, monhts_dict[pub_date[2]], pub_date[1])
            elif len(pub_date) == 2:
                pub_date = '%s-%s-%s' % (date.today().year, monhts_dict[pub_date[1]], pub_date[0])
            elif 'размещено' in pub_date:
                if ('часов' in pub_date) or ('час' in pub_date) or ('минуты' in pub_date) or ('минуту' in pub_date) \
                        or ('минут' in pub_date):
                    pub_date = '%s-%s-%s' % (date.today().year, date.today().month, date.today().day)
                else:
                    pub_date = '%s-%s-%s' % (pub_date[3], monhts_dict[pub_date[2]], pub_date[1])
        else:
            if 'размещено' in up_pub_lst[0]:
                pub_date = up_pub_lst[1] if len(up_pub_lst) == 2 else up_pub_lst[0].replace('Объявление размещено ', '')
                pub_date = pub_date.split(' ')
                if len(pub_date) == 3:
                    if ('сегодня' in pub_date) or ('часа' in pub_date) or ('часов' in pub_date) or ('час' in pub_date) \
                            or ('минуту' in pub_date) or ('минуты' in pub_date):
                        pub_date = '%s-%s-%s' % (date.today().year, date.today().month, date.today().day)
                    else:
                        pub_date = '%s-%s-%s' % (pub_date[2], monhts_dict[pub_date[1]], pub_date[0])
                elif len(pub_date) == 2:
                    pub_date = '%s-%s-%s' % (date.today().year, monhts_dict[pub_date[1]], pub_date[0])
                elif 'размещено' in pub_date:
                    pub_date = '%s-%s-%s' % (pub_date[3], monhts_dict[pub_date[2]], pub_date[1])
            up_date = None
        return up_date, pub_date


if __name__ == '__main__':
    spider = YandexSpider()
    spider.parse()
