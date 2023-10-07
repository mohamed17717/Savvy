import os

from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


from .app_settings import *
from .database_settings import *
from .localize_settings import *
from .password_settings import *
from .static_settings import *
from .rest_settings import *
from .knox_settings import *
from .celery_settings import *
from .cache_settings import *
from .log_settings import *
