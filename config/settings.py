import os

import environ
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

BASE_DIR = environ.Path(__file__) - 2

env = environ.Env()

env_file = str(BASE_DIR.path('.env'))
if os.path.exists(env_file):
    env.read_env(env_file)

DEBUG = env.bool('DJANGO_DEBUG', False)
# In DEBUG mode (local dev) fall back to an insecure placeholder so
# `manage.py check/test` work with no env vars set. In production
# (DEBUG=False) SECRET_KEY is required and startup fails without it.
SECRET_KEY = env.str('SECRET_KEY', default='insecure-dev-key') if DEBUG else env.str('SECRET_KEY')
ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])
REDIS_URL = env.str('REDIS_URL', 'redis://localhost:6379/4')

INSTALLED_APPS = [
    'admin_actions',
    'bootstrap4',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'users',
    'app',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [str(BASE_DIR.path('templates'))],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'config.utils.turbolinks',
                'config.utils.media_count',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': env.db('DATABASE_URL', default='sqlite:///db.sqlite3'),
}
# DATABASES['default']['ATOMIC_REQUESTS'] = True

# Django 3.2+: keep the pre-3.2 implicit AutoField for auto-created PKs.
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

STATICFILES_DIRS = [
    str(BASE_DIR.path('static')),
]

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

PUBLIC_ROOT = BASE_DIR.path('public')
STATIC_URL = '/static/'
STATIC_ROOT = str(PUBLIC_ROOT.path('static'))
MEDIA_URL = '/uploads/'
MEDIA_ROOT = str(PUBLIC_ROOT.path('uploads'))

AUTH_USER_MODEL = 'users.User'
SESSION_COOKIE_AGE = 60 * 60 * 24 * 365
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'destination_list'
LOGOUT_REDIRECT_URL = 'index'

DATA_UPLOAD_MAX_MEMORY_SIZE = 50000000

if not DEBUG:
    SECURE_SSL_REDIRECT = env.bool('DJANGO_SECURE_SSL_REDIRECT', default=True)
    if SECURE_SSL_REDIRECT:
        SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
        SECURE_REDIRECT_EXEMPT = [r'^upload/.*']

USE_S3 = env.bool('DJANGO_USE_S3', default=not DEBUG)
if USE_S3:
    DEFAULT_STORAGE_BACKEND = 'storages.backends.s3boto3.S3Boto3Storage'
    # S3 credentials are required in production; in DEBUG mode they fall
    # back to '' so `manage.py check/test` work without env vars.
    AWS_ACCESS_KEY_ID = env.str('AWS_ACCESS_KEY_ID', default='') if DEBUG else env.str('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = env.str('AWS_SECRET_ACCESS_KEY', default='') if DEBUG else env.str('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = env.str('AWS_STORAGE_BUCKET_NAME', default='screenuploader')
    AWS_AUTO_CREATE_BUCKET = True
    AWS_S3_REGION_NAME = env.str('AWS_S3_REGION_NAME', default='eu-west-3')
    AWS_DEFAULT_ACL = 'public-read'
else:
    DEFAULT_STORAGE_BACKEND = 'django.core.files.storage.FileSystemStorage'

STORAGES = {
    'default': {'BACKEND': DEFAULT_STORAGE_BACKEND},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}

# Third-party integration credentials: required in production
# (DEBUG=False); fall back to '' in DEBUG mode so local check/test
# runs without env vars set.
DISCORD_BOT_TOKEN = env.str('DISCORD_BOT_TOKEN', default='') if DEBUG else env.str('DISCORD_BOT_TOKEN')

sentry_sdk.init(
    dsn=env.str('SENTRY_DSN', None),
    integrations=[DjangoIntegration()],
)
