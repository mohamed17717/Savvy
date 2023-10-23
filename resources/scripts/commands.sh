#!/usr/bin/sh

celery -A dj worker -l INFO -n scrapy_worker -Q scrapy -E --concurrency=3
celery -A dj worker -l INFO -n email_worker -Q email -E --concurrency=4

celery -A dj beat -l INFO

