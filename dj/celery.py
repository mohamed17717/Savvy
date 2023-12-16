from __future__ import absolute_import, unicode_literals

import os
from celery import Celery
from datetime import timedelta
from kombu import Queue

# TODO check testing command and change the settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dj.settings')

app = Celery('dj')

app.conf.enable_utc = False
app.conf.broker_connection_retry_on_startup = True

app.conf.tasks_queues = (
    Queue('default', exchange='default', routing_key='default'),
    Queue('scrapy', exchange='scrapy', routing_key='scrapy'),
    Queue('email', exchange='email', routing_key='email'),
    Queue('orm', exchange='orm', routing_key='orm'),
)
app.conf.update(
    worker_heartbeat=120,  # Send a heartbeat every 120 seconds
)
app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

app.conf.beat_schedule = {
    # 'delete_temp_files_after_day': {
    #     'task': 'Applicants.tasks.delete_temp_files_after_day',
    #     'schedule': timedelta(days=1),
    #     'args': ()
    # },
}