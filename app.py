from flask import Flask
from celery import Celery
from config import Configuration

from admin.blueprint import admin

app = Flask(__name__)

app.config.from_object(Configuration)
app.register_blueprint(admin, url_prefix='/admin')

app.config['CELERY_BROKER_URL'] = 'redis://localhost:32768/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:32768/0'

celery = Celery('tasks', broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)
