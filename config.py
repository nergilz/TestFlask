class Configuration(object):
    DEBUG = True
    CELERY_BROKER_URL = 'redis://localhost:32768/0'
    CELERY_RESULT_BACKEND = 'redis://localhost:32768/0'