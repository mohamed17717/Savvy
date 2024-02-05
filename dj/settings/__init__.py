import os

from pathlib import Path
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY')

DEBUG = os.getenv('DEBUG', '1') == '1'
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    'django',
]

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
    'silk',
    'django_prometheus',
    'corsheaders',

]

MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    'corsheaders.middleware.CorsMiddleware',

    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',

    'silk.middleware.SilkyMiddleware',

    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django_prometheus.middleware.PrometheusAfterMiddleware',

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


DATABASES = {
    'default': {
        # 'ENGINE': 'django.db.backends.postgresql',
        # 'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'ENGINE': "django_prometheus.db.backends.postgresql",
        'NAME': os.getenv("POSTGRES_DB"),
        'USER': os.getenv("POSTGRES_USER"),
        'PASSWORD': os.getenv("POSTGRES_PASSWORD"),
        'HOST': os.getenv("POSTGRES_HOST"),
        'PORT': os.getenv("POSTGRES_PORT", '5432'),
        'CONN_MAX_AGE': 600,
        'ATOMIC_REQUESTS': True,
    }
}

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ('knox.auth.TokenAuthentication',),
    'DEFAULT_PERMISSION_CLASSES': (
        # make sure user who make action is authenticated and authorized for it
        'rest_framework.permissions.IsAuthenticated',
        # 'rest_framework.permissions.DjangoModelPermissions',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 20,

    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
        'drf_excel.renderers.XLSXRenderer',
    ),
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
    'EXCEPTION_HANDLER': 'common.utils.drf.exceptions.custom_exception_handler',
}

REST_KNOX = {
    'SECURE_HASH_ALGORITHM': 'cryptography.hazmat.primitives.hashes.SHA512',
    'AUTH_TOKEN_CHARACTER_LENGTH': 64,
    'TOKEN_TTL': timedelta(days=45),
    'USER_SERIALIZER': 'knox.serializers.UserSerializer',
    'TOKEN_LIMIT_PER_USER': None,
    'AUTO_REFRESH': False,
}

REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = os.getenv('REDIS_PORT', '6379')
# Celery SETTINGS
CELERY_BROKER_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/0'
CELERY_RESULT_BACKEND = f'redis://{REDIS_HOST}:{REDIS_PORT}/0'
CELERY_TASK_SERIALIZER = 'pickle'
CELERY_RESULT_SERIALIZER = 'pickle'
CELERY_TIMEZONE = 'UTC'
CELERY_ACCEPT_CONTENT = ['pickle']
CELERY_BROKER_TRANSPORT_OPTIONS = {'visibility_timeout': 12 * 60 * 60}
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
CELERY_IGNORE_RESULT = True


# Caches
CACHES = {
    "default": {
        # "BACKEND": "django_redis.cache.RedisCache",
        "BACKEND": "django_prometheus.cache.backends.redis.RedisCache",
        "LOCATION": f"redis://{REDIS_HOST}:{REDIS_PORT}/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient"
        },
        "KEY_PREFIX": "dj_cache"
    }
}

# Log Setup
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,

    'formatters': {
        'main_formatter': {
            'format': '{asctime} - {levelname} - {module} - {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'main_formatter',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'logs/info.log',
            'formatter': 'main_formatter',
        },
        'celery_file': {
            'class': 'logging.FileHandler',
            'filename': 'logs/celery.log',
            'formatter': 'main_formatter',
        },
    },

    'loggers': {
        'main': {
            'handlers': ['file', 'console'] if DEBUG else ['file'],
            'propagate': True,
            'level': 'INFO'
        },
        
        'celery': {
            'handlers': ['celery_file', 'console'],
            'propagate': True,
            'level': 'INFO'
        }
    }
}


EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')


STATIC_URL = 'static/'
MEDIA_URL = 'media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')


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

INTERNAL_IPS = ['127.0.0.1', 'django']
def show_toolbar(request):
    return True


DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': show_toolbar,
}

PROMETHEUS_EXPORT_MIGRATIONS = True

SILKY_PYTHON_PROFILER = True
SILKY_META = True

CORS_ORIGIN_ALLOW_ALL = False
CORS_ORIGIN_WHITELIST = (
    'http://localhost:8000',
    'http://localhost:8080',
    'http://localhost:5173'
)
