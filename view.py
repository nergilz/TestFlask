from app import app
from flask import render_template

from tasks import hello, start_parsing

from realty_parser_req.realty_peeewee import ItemsDB


@app.route('/')
def index():
    task = start_parsing.delay('cian')
    # database = ItemsDB()
    # item = database.get(id=2)
    return render_template(template_name_or_list='index.html', task_id=task.id, status=task.status)
