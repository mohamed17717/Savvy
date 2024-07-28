import logging
from logging.handlers import RotatingFileHandler

# Gunicorn config variables
loglevel = 'debug'
errorlog = '/usr/src/app/logs/gunicorn-error.log'
accesslog = '/usr/src/app/logs/gunicorn-access.log'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Configure logging
logger = logging.getLogger('main')
handler = RotatingFileHandler(
    '/usr/src/app/logs/gunicorn-error.log', maxBytes=100000, backupCount=10)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)
