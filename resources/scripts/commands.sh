#!/usr/bin/sh

celery -A dj worker -l INFO -n email_worker -Q email -E --concurrency=4
celery -A dj worker -l INFO -n scrapy_worker -Q scrapy -E --concurrency=10
celery -A dj worker -l INFO -n orm_worker -Q orm -E --concurrency=10


celery -A dj beat -l INFO

autocannon -c 100 -d 5 -p 10 -H Authorization="Token 97b7d1e9eb169fef28dd168b6479907f676975c85ec70153553732017ec7bed8"  http://127.0.0.1:8000/bm/bookmark/list/
wrk -t12 -c400 -d30s -H "Authorization: Token 97b7d1e9eb169fef28dd168b6479907f676975c85ec70153553732017ec7bed8"  http://localhost/bm/bookmark/list/
# django.db.utils.OperationalError: connection to server at "127.0.0.1", port 5432 failed: FATAL:  sorry, too many clients already
# connection to server at "127.0.0.1", port 5432 failed: FATAL:  sorry, too many clients already


# Testing for API
python manage.py test --parallel auto --keepdb --settings=dj.settings.settings_test App.tests.apis_tests

export DJANGO_SETTINGS_MODULE=dj.settings.settings_test && celery -A dj worker -l INFO -n scrapy_worker -Q scrapy -E --concurrency=2
export DJANGO_SETTINGS_MODULE=dj.settings.settings_test && celery -A dj worker -l INFO -n orm_worker -Q orm -E --concurrency=2

python manage.py test --parallel auto --settings=dj.settings.settings_test

# Latest test commands run one by one
DJANGO_SETTINGS_MODULE=dj.settings.settings_test python manage.py test
DJANGO_SETTINGS_MODULE=dj.settings.settings_test python manage.py test App.tests.scrapy_tests
