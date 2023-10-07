import os


DEBUG = os.getenv('DEBUG', '1') == '1'

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
    },

    'loggers': {
        'main': {
            'handlers': ['file', 'console'] if DEBUG else ['file'],
            'propagate': True,
            'level': 'INFO'
        }
    }
}
