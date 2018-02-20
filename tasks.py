from app import celery

from realty_parser_req.terrarium.avito_spider import AvitoSpider
from realty_parser_req.terrarium.cian_spider import CianSpider


@celery.task()
def start_parsing(site):
    if site == 'avito':
        avito_parser = AvitoSpider()
        avito_parser.parse()
    elif site == 'cian':
        cian_spider = CianSpider()
        cian_spider.browser_exractor('https://sochi.cian.ru/kupit-kvartiru-studiu/')
    return True


@celery.task()
def hello(text):
    return 'Hello %s' % (text)
