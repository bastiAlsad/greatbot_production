"""
Django settings for laxout project.

Generated by 'django-admin startproject' using Django 5.0.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.0/ref/settings/
"""

from pathlib import Path
import os
from environ import environ

env = environ.Env()

BASE_DIR = Path(__file__).resolve().parent.parent

env.read_env(os.path.join(BASE_DIR, ".env"))

SECRET_KEY = env("SECRET_KEY")
AZURE_API_KEY = env("AZURE_API_KEY")
AZURE_END_POINT = env("AZURE_END_POINT")

PRODUCTION = env.bool("PRODUCTION", default=True)

ALLOWED_HOSTS = ["*"]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.TokenAuthentication",
    ),
}
# Application definition

CORS_ALLOW_CREDENTIALS = True

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "crispy_forms",
    "corsheaders",
    'rest_framework',
    'rest_framework.authtoken',
    "chat_bot_app",
]

CRISPY_TEMPLATE_PACK = "bootstrap5"

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # CORS Middleware kommt zuerst
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# CORS_ALLOWED_ORIGINS = [
#     "*",
# ]
CORS_ALLOW_ALL_ORIGINS = True



ROOT_URLCONF = "chat_bot.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "chat_bot.wsgi.application"

# dashboardlaxout
# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

if PRODUCTION:
    print("Production database active")
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": "greatbot$database2",
            "USER": "greatbot",
            "PASSWORD": "gB!%99HtmZ??",
            "HOST": "greatbot.mysql.eu.pythonanywhere-services.com",
            "PORT": "",
        }
    }
    DEBUG = True
else:
    print("Local database active")
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
    DEBUG = True

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

# AUTH_USER_MODEL = 'laxout_app.Physio'
# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = "static/"
# MEDIA_ROOT = '/home/dashboardlaxout/backup_laxout/media'
# STATIC_ROOT = '/home/dashboardlaxout/backup_laxout/static'
# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

STATICFILES_DIRS = [
    BASE_DIR / "static",  # This is the path to your project's static files
]
LOGIN_REDIRECT_URL = "/hub"  # which url the user is getting pushed after logging in
LOGOUT_REDIRECT_URL = "/login"
