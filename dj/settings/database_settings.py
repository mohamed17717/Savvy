import os


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