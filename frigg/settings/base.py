"""
Django settings for frigg project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
from django.conf.global_settings import TEMPLATE_CONTEXT_PROCESSORS as DJANGO_TEMPLATE_CONTEXT_PROCESSORS

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'v8aa$cb0knx6)vyo!%tn6k6_g($!n1yq_v+4bg9v4*n@&dpu0w'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []
INTERNAL_IPS = ('127.0.0.1:8000')


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'social_auth',

    'frigg.builds'
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)
TEMPLATE_CONTEXT_PROCESSORS = DJANGO_TEMPLATE_CONTEXT_PROCESSORS +\
                              ('django.core.context_processors.debug',)

ROOT_URLCONF = 'frigg.urls'

WSGI_APPLICATION = 'frigg.wsgi.application'

AUTHENTICATION_BACKENDS = (
    'social_auth.backends.contrib.github.GithubBackend',
    'django.contrib.auth.backends.ModelBackend',
)

# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

TEMPLATE_DIRS = (
    os.path.join(BASE_DIR, 'templates'),
)

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATIC_URL = '/static/'

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'files/'),
)

PROJECT_TMP_DIRECTORY = "/home/ubuntu/builds/frigg_working_dir/"
SERVER_ADDRESS = '127.0.0.1:8000'

# Available options:
# assigned, unassigned, labeled, unlabeled, opened, closed, reopened, or synchronized.
IGNORED_PULL_REQUEST_ACTIONS = ['closed', 'assigned', 'unassigned', 'labeled',
                                'unlabeled']

DOCKER_SOCKET = "unix://var/run/docker.sock"
DOCKER_IP = "127.0.0.1"

# Social auth
LOGIN_URL = '/auth/login/github'
LOGIN_REDIRECT_URL = '/'
LOGIN_ERROR_URL = '/auth/error/'

SOCIAL_AUTH_DEFAULT_USERNAME = 'new_social_auth_user'
SOCIAL_AUTH_UID_LENGTH = 16
SOCIAL_AUTH_ASSOCIATION_HANDLE_LENGTH = 16
SOCIAL_AUTH_NONCE_SERVER_URL_LENGTH = 16
SOCIAL_AUTH_ASSOCIATION_SERVER_URL_LENGTH = 16
SOCIAL_AUTH_ENABLED_BACKENDS = 'github',

GITHUB_EXTENDED_PERMISSIONS = ['repo', 'read:org']
