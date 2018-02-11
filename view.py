from app import app, celery
from flask import render_template
from realty_parser_req.terrarium.avito_spider import AvitoSpider
from realty_parser_req.terrarium.cian_spider import CianSpider
from realty_parser_req.realty_peeewee import ItemsDB


@app.route('/')
def index():
    # start_parsing.delay('cian')
    task = hello.delay()
    result = task.traceback
    # database = ItemsDB()
    # item = database.get(id=2)
    return render_template(template_name_or_list='index.html', item=result)


@celery.task
def start_parsing(site):
    if site == 'avito':
        avito_parser = AvitoSpider()
        avito_parser.parse()
    elif site == 'cian':
        cian_spider = CianSpider()
        cian_spider.parse()
    return True


@celery.task
def hello():
    text = 'task is run!!!'
    return 'Hello %s' % (text)
