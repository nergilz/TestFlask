from app import app
from flask import render_template

from realty_parser.models import ItemsDB


@app.route('/')
def index():
    database = ItemsDB()
    records = database.select().order_by(ItemsDB.id)
    return render_template(template_name_or_list='index.html', records=records)
