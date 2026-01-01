

from datetime import timedelta

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent



# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "django-insecure-$se+uyp*bh$iyda9$-(&gci$)_tgghy%p4$m=io3&&gdkkbfuv",  # fallback for dev only
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DJANGO_DEBUG", "True").lower() == "true"

# Allow all hosts - set to * to allow all
ALLOWED_HOSTS = ["*"]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'accounts',
    'corsheaders',
    'documents',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # Must be first
    'dcs_backend.cors_middleware.CustomCorsMiddleware',  # Backup CORS middleware
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'dcs_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'dcs_backend.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST"),
        "PORT": os.getenv("DB_PORT"),
    }
}


# Using default Django User model (django.contrib.auth.models.User)
# AUTH_USER_MODEL is not set, so Django will use the default User model

APPEND_SLASH = False

# ============================================
# CORS SETTINGS - ALLOW ALL ORIGINS
# ============================================
# Backend is configured for HTTP now. Will work perfectly when moved to HTTPS later.
#
# Current Setup: HTTP Backend (http://34.93.251.200)
# - CORS is fully configured and ready
# - All origins allowed
# - Works with HTTP frontends
#
# For Testing with HTTP Frontend:
# - Use http://34.93.251.200/api/ as your API URL
# - Works perfectly for local development or HTTP-hosted frontends
#
# When Moving to HTTPS Later:
# - Just set up SSL certificate (Let's Encrypt, Cloudflare, etc.)
# - Change backend URL to https://yourdomain.com
# - No code changes needed - CORS settings work for both HTTP and HTTPS
#
# Note: HTTPS frontend (Netlify) cannot call HTTP backend due to browser security.
# This is expected and will be resolved when backend moves to HTTPS.
#
# Note: When CORS_ALLOW_ALL_ORIGINS is True, CORS_ALLOW_CREDENTIALS should be False
# for browser compatibility. JWT tokens work fine without credentials.
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = False  # Set to False when allowing all origins

# Comprehensive list of allowed headers
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'content-disposition',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'x-forwarded-for',
    'x-forwarded-proto',
]

# Allow all HTTP methods including OPTIONS for preflight
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
    'HEAD',
]

# Expose headers that frontend might need
CORS_EXPOSE_HEADERS = [
    'content-type',
    'content-length',
    'authorization',
]

# Preflight cache duration (24 hours)
CORS_PREFLIGHT_MAX_AGE = 86400





# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = 'static/'

# MEDIA (for file uploads)
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"



REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}
# ---------------CELERY-SETTINGS-----------------
CELERY_BEAT_SCHEDULER = 'Optick.celery_custom.scheduler.NaiveTimezoneScheduler'
# Other Celery settings

CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
BROKER_URL = 'redis://localhost:6379'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TASK_TRACK_STARTED = True
CELERY_BROKER_URL = 'redis://localhost:6379/0'           # Use DB 0 for broker
CELERY_RESULT_BACKEND = 'redis://localhost:6379/1'       # U
CELERY_TIMEZONE = 'Asia/Kolkata' 
DJANGO_CELERY_BEAT_TZ_AWARE = False


SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

AUTH_USER_MODEL = "accounts.User"

# ---------------------smtp settings for email OTP ---------------------
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"


EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"   # e.g., smtp.gmail.com
EMAIL_PORT = 587                          # 465 for SSL, 587 for TLS
EMAIL_USE_TLS = True                       # True for TLS
EMAIL_USE_SSL = False                      # Only if using SSL port
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL")