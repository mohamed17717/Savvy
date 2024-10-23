fullmigrate:
	python manage.py makemigrations && python manage.py migrate

loadtest:
	autocannon -c 100 -d 10 -p 10 -H Authorization="Token 132" http://localhost:8000/bm/bookmark/list/

runtests:
	python manage.py test --parallel auto --keepdb --settings=dj.settings.settings_test $(args)

runcelery:
	celery -A dj worker -l INFO -n email_worker -Q email -E --concurrency=4

update-requirements:
	pip install --upgrade -r requirements.txt && pip freeze | sed 's/==/~=/' > requirements.txt

pre-commit-all:
	pre-commit run --all-files


.PHONY: fullmigrate loadtest runtests runcelery update-requirements pre-commit-all


# export DJANGO_SETTINGS_MODULE=dj.settings.settings_test && celery -A dj worker -l INFO -n scrapy_worker -Q scrapy -E --concurrency=2
# export DJANGO_SETTINGS_MODULE=dj.settings.settings_test && celery -A dj worker -l INFO -n orm_worker -Q orm -E --concurrency=2

# # Latest test commands run one by one
# DJANGO_SETTINGS_MODULE=dj.settings.settings_test python manage.py test
# DJANGO_SETTINGS_MODULE=dj.settings.settings_test python manage.py test App.tests.scrapy_tests

# celery -A dj worker -l INFO -n scrapy_worker -Q scrapy -E --concurrency=10
# celery -A dj worker -l INFO -n orm_worker -Q orm -E --concurrency=10
# celery -A dj beat -l INFO
