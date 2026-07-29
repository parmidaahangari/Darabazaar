from .base import *
import os
import environ
DEBUG = True

SECRET_KEY = os.environ.get('SECRET_KEY')

ALLOWED_HOSTS = ['darabazaar.com', 'www.darabazaar.com', '127.0.0.1', 'localhost', "192.168.100.7"]

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # اختیاری (یک سال)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

BLUPAL_API_KEY = env("BLUPAL_API_KEY")
BLUPAL_BASE_URL = env("BLUPAL_BASE_URL", default="https://blupal.net/api")
BLUPAL_WEBHOOK_SECRET = None