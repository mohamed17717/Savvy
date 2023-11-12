#!/usr/bin/sh

celery -A dj worker -l INFO -n scrapy_worker -Q scrapy -E --concurrency=3
celery -A dj worker -l INFO -n email_worker -Q email -E --concurrency=4

celery -A dj beat -l INFO

autocannon -c 100 -d 5 -p 10 -H Authorization="Token 54da3defde81841587f99f04e3d6e7b2e56c69e077e9d4f5bcb853d551763935"  http://127.0.0.1:8000/bm/bookmark/list/
# django.db.utils.OperationalError: connection to server at "127.0.0.1", port 5432 failed: FATAL:  sorry, too many clients already
# connection to server at "127.0.0.1", port 5432 failed: FATAL:  sorry, too many clients already


# Testing for API
python manage.py test --parallel auto --keepdb --settings=dj.settings.settings_test App.tests.apis_tests

export DJANGO_SETTINGS_MODULE=dj.settings.settings_test && celery -A dj worker -l INFO -n scrapy_worker -Q scrapy -E --concurrency=4
