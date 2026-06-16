from .base import *
import os
import environ
DEBUG = True

SECRET_KEY = os.environ.get('SECRET_KEY')

ALLOWED_HOSTS = ['darabazaar.com', 'www.darabazaar.com', '127.0.0.1', 'localhost', "192.168.100.7"]

# در لوکال معمولاً SSL نداریم:
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
