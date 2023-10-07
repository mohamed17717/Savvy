
# Celery SETTINGS
CELERY_BROKER_URL = 'redis://localhost:6379'
CELERY_RESULT_BACKEND = 'redis://localhost:6379'
CELERY_TASK_SERIALIZER = 'pickle'
CELERY_RESULT_SERIALIZER = 'pickle'
CELERY_TIMEZONE = 'UTC'
CELERY_ACCEPT_CONTENT = ['pickle']
CELERY_BROKER_TRANSPORT_OPTIONS = {'visibility_timeout': 12 * 60 * 60}
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
