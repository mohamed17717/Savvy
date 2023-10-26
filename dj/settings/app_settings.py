import os


DEBUG = os.getenv('DEBUG', '1') == '1'
ALLOWED_HOSTS = []

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # apps
    'App',
    'Users',

    # Third Party
    'rest_framework',
    'knox',
    'drf_yasg',
    'django_filters',
    'django_celery_results',
    'django_celery_beat',
    'django_extensions',
    'debug_toolbar',

]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    'debug_toolbar.middleware.DebugToolbarMiddleware',

]

ROOT_URLCONF = 'dj.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'dj.wsgi.application'

AUTH_USER_MODEL = 'Users.User'


SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'api_key': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization',
            'value': 'Token 54da3defde81841587f99f04e3d6e7b2e56c69e077e9d4f5bcb853d551763935'
        }
    },
    'USE_SESSION_AUTH': False,
    'JSON_EDITOR': True,
}

INTERNAL_IPS = [
    # ...
    "127.0.0.1",
    # ...
]