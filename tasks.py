import time

from app import celery

from realty_parser.spiders.avito_spider import AvitoSpider
from realty_parser.spiders.cian_spider import CianSpider
from realty_parser.spiders.yandex_spider import YandexSpider


@celery.task()
def start_parsing(site):
    if site == 'avito':
        avito_parser = AvitoSpider()
        avito_parser.parse()
    elif site == 'cian':
        cian_spider = CianSpider()
        cian_spider.parse()
    elif site == 'yandex':
        yandex_spider = YandexSpider()
        yandex_spider.parse()


@celery.task()
def hello(text):
    time.sleep(5)
    return 'Hello %s' % (text)
