from flask import Blueprint
from flask import render_template

admin = Blueprint('admin', __name__, template_folder='templates')


@admin.route('/')
def index():
    return render_template('admin/index.html')


@admin.route('/run-task/')
def run_task(site):
    pass
