from .base import *

DEBUG = True

SECRET_KEY = 'django-insecure-LOKAL_TEST_KEY_ONLY'  # مهم نیست چون روی سیستم خودته

ALLOWED_HOSTS = ['darabazaar.com', 'www.darabazaar.com', '127.0.0.1', 'localhost', "192.168.100.7"]

# در لوکال معمولاً SSL نداریم:
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
