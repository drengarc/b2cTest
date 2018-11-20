DEBUG = True
TEMPLATE_DEBUG = DEBUG
DISABLE_DEBUG_TOOLBAR = True
LANGUAGE_CODE = 'en_EN'

MEDIA_URL = '/media/'
STATIC_URL = '/static/'
SECRET_KEY = 'u#n$q#q1ay&f1__5wygljknfskjnfsznv@q)uy=4sx6ho@)lafsdnfjksnd6kyyvv0h1kj'

DEFAULT_FROM_EMAIL = 'info@parca1.com'
DEFAULT_MAIL_FROM_NAME = "parca1.com"

NOTIFICATION_MAIL = "info@parca1.com"

EMAIL_HOST = 'localhost'
EMAIL_PORT = 1025
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
EMAIL_USE_TLS = False

LANGUAGE_CODE = 'tr_TR'
SITE_URL = 'http://www.parca1.com'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'eps',
        'PORT': '5432',
        'HOST': '46.101.246.85',
        'USER': 'mfelek',
        'PASSWORD': 'Mf06051979'
    }
}

LOGGING = {
    'version': 1,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(asctime)s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

RAVEN_CONFIG = {}