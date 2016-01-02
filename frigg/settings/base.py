# -*- coding: utf8 -*-
import os

from django.contrib import messages

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

SECRET_KEY = 'v8aa$cb0knx6)vyo!%tn6k6_g($!n1yq_v+4bg9v4*n@&dpu0w'
DEBUG = True
ALLOWED_HOSTS = []
INTERNAL_IPS = ['127.0.0.1']

MESSAGE_TAGS = {
    messages.ERROR: 'danger'  # Makes messages play nice with bootstrap 3
}


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'social.apps.django_app.default',
    'django_extensions',
    'rest_framework',
    'django_statsd',

    'frigg.authentication',
    'frigg.builds',
    'frigg.helpers',
    'frigg.deployments',
    'frigg.owners',
    'frigg.stats',
    'frigg.utils',
    'frigg.webhooks',
    'frigg.workers',
]

MIDDLEWARE_CLASSES = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # statsd
    'django_statsd.middleware.GraphiteRequestTimingMiddleware',
    'django_statsd.middleware.GraphiteMiddleware',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                'django.core.context_processors.request',
                'social.apps.django_app.context_processors.backends',
                'social.apps.django_app.context_processors.login_redirect',
            ],
        },
    },
]

ROOT_URLCONF = 'frigg.urls'

WSGI_APPLICATION = 'frigg.wsgi.application'

AUTH_USER_MODEL = 'authentication.User'
AUTHENTICATION_BACKENDS = [
    'social.backends.github.GithubOAuth2',
    'django.contrib.auth.backends.ModelBackend',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'frigg',
        'HOST': '127.0.0.1'
    }
}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = False
USE_TZ = True
DATETIME_FORMAT = 'Y-m-d H:i'

STATIC_ROOT = os.path.join(BASE_DIR, '../static')
STATIC_URL = '/static/'
MEDIA_ROOT = os.path.join(BASE_DIR, '../uploads')
MEDIA_URL = '/uploads/'
STATICFILES_DIRS = os.path.join(BASE_DIR, 'files/'),

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

# Social auth
LOGIN_URL = '/auth/login/github'
LOGIN_REDIRECT_URL = '/'
LOGIN_ERROR_URL = '/auth/error/'


# python social auth
SOCIAL_AUTH_URL_NAMESPACE = 'social'
SOCIAL_AUTH_STORAGE = 'social.apps.django_app.default.models.DjangoStorage'
SOCIAL_AUTH_GITHUB_SCOPE = ['repo', 'read:org']


# statsd
STATSD_PATCHES = [
    'django_statsd.patches.db',
    'django_statsd.patches.cache',
]
STATSD_MODEL_SIGNALS = True
STATSD_PREFIX = 'frigg_hq.'
