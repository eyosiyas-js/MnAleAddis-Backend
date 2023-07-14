from pathlib import Path
from datetime import timedelta

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-$^rr^$(-$z8hyk&--r=&csi91tck=w3ok&l(8+)zu(@bl$)!1^'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [
    '167.235.30.159',
    'https://backend-mnale.herokuapp.com/',
    'backend-mnale.herokuapp.com',
    'localhost',
    '127.0.0.1'
    ]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'app',

    # installed apps
    'rest_framework',
    'corsheaders',
    'django_filters',
    'rest_framework_simplejwt',
    'channels',
    'drf_yasg'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',

    # corsheaders middleware
    # 'corsheaders.middleware.CorsMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# CORS_ALLOWED_ORIGINS = [
#     "http://localhost:3000",
# ]

ROOT_URLCONF = 'mnaleaddis.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR/"templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

ASGI_APPLICATION = 'mnaleaddis.asgi.application'


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    )
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=12),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}
# CELERY STUFF
BROKER_URL = 'redis://localhost:6379'
CELERY_RESULT_BACKEND = 'redis://localhost:6379'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Africa/Nairobi'

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }

# mongodb+srv://mnaleuser:<password>@minaleaddisdb.qt949.mongodb.net/myFirstDatabase?retryWrites=true&w=majority
# mongodb+srv://mnaleuser:<password>@minaleaddisdb.qt949.mongodb.net/myFirstDatabase?retryWrites=true&w=majority
DATABASES = {
    'default': {
        'ENGINE': 'djongo',
        # 'NAME': 'MnAleAddis',
        'ENFORCE_SCHEMA': False,
        'CLIENT': {
            'name':'MnAleAddis',
            'host':'mongodb+srv://mnaleuser:mnaleaddis123@minaleaddisdb.qt949.mongodb.net/myFirstDatabase?retryWrites=true&w=majority',
            'username':'mnaleuser',
            'password':'mnaleaddis123'
                # 'host': 'mongodb+srv://mnaleuser:mnaleaddis123@minaleaddisdb.qt949.mongodb.net/myFirstDatabase?retryWrites=true&w=majority'
            }
    }
    # mongodb+srv://HHMS:HHMS@HHMSdb.emczm.mongodb.net/HHMS?retryWrites=true&w=majority"
}


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

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

CLOUDINARY = {
  'cloud_name': 'dyvvsnnxx',  
  'api_key': '976241263465395',  
  'api_secret': 'Uayoe0HACiYi8rYU-Ou5NgW6Zh0',  
}

# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR  / 'staticfiles'
# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'app.ExtendedUser'

CORS_ORIGIN_ALLOW_ALL = True


# setup for sending email 
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_HOST_USER = 'mnaleaddis1@gmail.com'
EMAIL_HOST_PASSWORD = 'qlasuzptiksktmhe'