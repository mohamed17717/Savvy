DB_URL=postgresql://postgres:postgres@localhost:5432/nxt?sslmode=disable
API_TOKEN=123


fullmigrate:
	python manage.py makemigrations && python manage.py migrate

loadtest:
	autocannon -c 100 -d 10 -p 10 -H Authorization="Token 132" http://localhost:8000/bm/bookmark/list/

runtests:
	python manage.py test --parallel auto --keepdb --settings=dj.settings.settings_test $(args)

# export DJANGO_SETTINGS_MODULE=dj.settings.settings_test && celery -A dj worker -l INFO -n scrapy_worker -Q scrapy -E --concurrency=2
# export DJANGO_SETTINGS_MODULE=dj.settings.settings_test && celery -A dj worker -l INFO -n orm_worker -Q orm -E --concurrency=2

# # Latest test commands run one by one
# DJANGO_SETTINGS_MODULE=dj.settings.settings_test python manage.py test
# DJANGO_SETTINGS_MODULE=dj.settings.settings_test python manage.py test App.tests.scrapy_tests

runcelery:
	celery -A dj worker -l INFO -n email_worker -Q email -E --concurrency=4
	celery -A dj worker -l INFO -n scrapy_worker -Q scrapy -E --concurrency=10
	celery -A dj worker -l INFO -n orm_worker -Q orm -E --concurrency=10
	celery -A dj beat -l INFO


update-requirements:
	pip freeze | sed 's/==/~=/' > requirements.txt


.PHONY: fullmigrate loadtest runtests runcelery update-requirements
