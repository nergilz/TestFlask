from flask import Flask
from celery import Celery
from config import Configuration

app = Flask(__name__)
app.config.from_object(Configuration)

celery = Celery('tasks', broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

from admin.blueprint import admin

app.register_blueprint(admin, url_prefix='/admin')
