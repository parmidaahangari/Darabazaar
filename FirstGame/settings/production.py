from .base import *

DEBUG = False

ALLOWED_HOSTS = ['darabazaar.com', 'www.darabazaar.com', '127.0.0.1', 'localhost', 'web'] # 'web' is the service name in docker-compose

# Security settings - uncomment and configure for production
# SECURE_SSL_REDIRECT = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True
# SECURE_HSTS_SECONDS = 31536000 # 1 year
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True
# X_FRAME_OPTIONS = 'DENY'
# SECURE_BROWSER_XSS_FILTER = True
# SECURE_CONTENT_TYPE_NOSNIFF = True

# Database
# DATABASES is already configured in base.py to use env.db() with a default for 'db' service

# Cache (Redis)
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': env('REDIS_URL', default='redis://redis:6379/1'), # 'redis' is the service name
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# Celery (Redis as broker and result backend)
CELERY_BROKER_URL = env('REDIS_URL', default='redis://redis:6379/0')
CELERY_RESULT_BACKEND = env('REDIS_URL', default='redis://redis:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Tehran' # Based on previous settings in production.py
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 300
CELERY_TASK_SOFT_TIME_LIMIT = 240
CELERY_WORKER_MAX_TASKS_PER_CHILD = 200
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1

# Sentry configuration (if applicable, from previous production.py)
# import sentry_sdk
# from sentry_sdk.integrations.django import DjangoIntegration
# from sentry_sdk.integrations.celery import CeleryIntegration
# from sentry_sdk.integrations.redis import RedisIntegration

# def filter_sensitive_data(event, hint):
#     # ... (your existing filter_sensitive_data function)
#     return event

# sentry_sdk.init(
#     dsn=env('SENTRY_DSN', default=None),
#     integrations=[
#         DjangoIntegration(),
#         CeleryIntegration(),
#         RedisIntegration(),
#     ],
#     traces_sample_rate=0.2,
#     profiles_sample_rate=0.1,
#     send_default_pii=True,
#     environment=env('ENVIRONMENT', default='production'),
#     release=env('APP_VERSION', default='unknown'),
#     before_send=filter_sensitive_data,
# )

# Logging - basic example for production
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'celery': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}

# CSRF trusted origins for production
csrf_trusted = env('CSRF_TRUSTED_ORIGINS', default='').split(',')
if '' in csrf_trusted:
    csrf_trusted.remove('')
if csrf_trusted:
    CSRF_TRUSTED_ORIGINS = csrf_trusted
else:
    # Fallback for development if not explicitly set
    CSRF_TRUSTED_ORIGINS = ALLOWED_HOSTS