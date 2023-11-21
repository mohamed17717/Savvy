from . import *

# import logging
# logging.disable(logging.CRITICAL)
# DEBUG = False
TEMPLATE_DEBUG = False
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory'
    }
}

CELERY_BROKER_URL = 'redis://localhost:6379/1'

os.environ['DJANGO_TEST_MODE'] = 'True'
