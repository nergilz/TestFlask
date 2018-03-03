import tasks

from flask import Blueprint, jsonify
from flask import render_template


admin = Blueprint('admin', __name__, template_folder='templates')


@admin.route('/')
def index():
    return render_template('admin/index.html')


@admin.route('/run-task/<site>', methods=['GET'])
def run_task(site):
    task = tasks.start_parsing.delay(site)
    return jsonify(task_id=task.id, task_status=task.state)


@admin.route('/task-status/<id>')
def check_staus(id):
    task = tasks.start_parsing.AsyncResult(id)
    # info = tasks.start_parsing.get(id)
    response = {'status': task.state, 'result': task.result}
    return jsonify(response)
