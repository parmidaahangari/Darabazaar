from pathlib import Path
import os
import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    POSTGRES_DB=(str, 'firstgame'),
    POSTGRES_USER=(str, 'firstgame'),
    POSTGRES_PASSWORD=(str, 'firstgame'),
    POSTGRES_HOST=(str, '127.0.0.1'),
    POSTGRES_PORT=(int, 5432),
)
# فقط KEY=value — خطوطی مثل ALLOWED_HOSTS = [...] را از .env حذف کنید
environ.Env.read_env(BASE_DIR / '.env', overwrite=False)

SECRET_KEY =  os.environ.get('SECRET_KEY')

DEBUG = True

ALLOWED_HOSTS = ['darabazaar.com', 'www.darabazaar.com', '127.0.0.1', 'localhost', "192.168.100.7"]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django_celery_beat',
    'CustomerAccount',
    'HomePage',
    'Products',
]


CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

MAX_USER_ADDRESSES = 5

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',   
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'FirstGame.middleware.AdminIPWhitelistMiddleware',
]


ROOT_URLCONF = 'FirstGame.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'CustomerAccount.context_processors.user_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'FirstGame.wsgi.application'


# Database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('POSTGRES_DB', default='firstgame'),
        'USER': env('POSTGRES_USER', default='firstgame'),
        'PASSWORD': env('POSTGRES_PASSWORD', default=''),
        'HOST': env('POSTGRES_HOST', default='db'),
        'PORT': env('POSTGRES_PORT', default='5432'),
    }
}

DATABASES['default']['ATOMIC_REQUESTS'] = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Media files (User uploaded files)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
        "OPTIONS": {
            "location": MEDIA_ROOT,
            "base_url": MEDIA_URL,
        },
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}


AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

AUTH_USER_MODEL = 'CustomerAccount.User'

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

LOGIN_URL = '/login/'

# در prod می‌تونیم این‌ها رو override کنیم
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0

csrf_trusted = os.environ.get('CSRF_TRUSTED_ORIGINS')
if csrf_trusted:
    CSRF_TRUSTED_ORIGINS = csrf_trusted.split(',')
else:
    CSRF_TRUSTED_ORIGINS = []
