from app import app
from flask import render_template
from realty_parser_req.terrarium.avito_spider import AvitoSpider
from realty_parser_req.terrarium.cian_spider import CianSpider
from realty_parser_req.realty_peeewee import ItemsDB

@app.route('/')
def index():
    # avito_parser = AvitoSpider()
    # avito_parser.parse()
    # cian_spider = CianSpider()
    # cian_spider.parse()
    database = ItemsDB()
    item = database.get(id=2)
    return render_template(template_name_or_list='index.html', item=item)