from app import app
from flask import render_template

from tasks import hello, start_parsing

from realty_parser.models import ItemsDB
from realty_parser.spiders.cian_spider import CianSpider


@app.route('/')
def index():
    task = start_parsing.delay('cian')
    return render_template(template_name_or_list='index.html', task_id=task.id, status=task.status)
