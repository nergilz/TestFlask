class Configuration(object):
    DEBUG = True
    CELERY_BROKER_URL = 'redis://redis:6379/0'
    CELERY_RESULT_BACKEND = 'redis://redis:6379/0'
    CELERY_TASK_SERIALIZER = 'json'
