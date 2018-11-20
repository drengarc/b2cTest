import os

from shop.utils.lazy import LazyWrapper


DEBUG = False
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
    }
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'eps1',
        'PORT': '5432',
        'HOST': '46.101.246.85',
        'USER': 'mfelek',
        'PASSWORD': 'Mf06051979'
    }
}


# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'Europe/Istanbul'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'tr_TR'

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = os.path.join(os.path.dirname(__file__), 'media/')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = os.path.join(os.path.dirname(__file__), 'static/')

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
    #'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'u#n$q#q1ay&f1__5wygljknfskjnfsznv@q)uy=4sx6ho@)lafsdnfjksnd6kyyvv0h1kj'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
    'django.core.context_processors.static',
    'django.contrib.messages.context_processors.messages',
    'shop.views.template_context_processor',
)

MIDDLEWARE_CLASSES = (
    'shop.middleware.BasketExceptionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'urls'

WSGI_APPLICATION = 'wsgi.application'

TEMPLATE_DIRS = (os.path.join(os.path.dirname(__file__), '', 'templates').replace('\\', '/'),)

INSTALLED_APPS = (
    'admin_tools',
    'admin_tools.theming',
    'admin_tools.menu',
    'admin_tools.dashboard',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'shop',
    'shop.api',
    'shop.banner',
    'shop.customer',
    'shop.discount',
    'shop.newsletter',
    'shop.payment.est',
    'shop.payment',
    'shop.shipment',
    'shop.modules.pricedropalert',
    'shop.modules.stockalert',
    'shop.modules.messaging',
    'vehicle.ege_integration',
    'vehicle',
    'simit',
    "compressor",
    'mptt',
    'django_hstore',
    'filebrowser',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'widget_tweaks',
    'tinymce',
    'django.contrib.sitemaps',
    'raven.contrib.django.raven_compat',
    'captcha',
)

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'root': {
        'level': 'WARNING',
        'handlers': ['sentry'],
    },
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
    },
    'handlers': {
        'sentry': {
            'level': 'ERROR',
            'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        }
    },
    'loggers': {
        'django.db.backends': {
            'level': 'ERROR',
            'handlers': ['sentry'],
            'propagate': False,
        },
        'raven': {
            'level': 'DEBUG',
            'handlers': ['sentry'],
            'propagate': False,
        },
        'celery': {
            'level': 'WARNING',
            'handlers': ['sentry'],
            'propagate': False,
        },
        'sentry.errors': {
            'level': 'DEBUG',
            'handlers': ['sentry'],
            'propagate': False,
        },
    },
}

CELERYD_HIJACK_ROOT_LOGGER = False

SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'

FILEBROWSER_VERSIONS = {
    'fb_thumb': {'verbose_name': 'Medium (400px * 250px)', 'width': 400, 'height': 250, 'opts': 'upscale'},
    'thumbnail': {'verbose_name': 'Thumbnail (140px)', 'width': 140, 'height': '', 'opts': ''},
    'product_list_square': {'verbose_name': 'Small (300px)', 'width': 210, 'height': 175, 'opts': ''},
    'product_page': {'verbose_name': 'Medium (400px * 250px)', 'width': 400, 'height': 250, 'opts': 'upscale'},
    'medium': {'verbose_name': 'Medium (460px)', 'width': 460, 'height': '', 'opts': ''},
    'big': {'verbose_name': 'Big (620px)', 'width': 620, 'height': '', 'opts': ''},
    'big_banner': {'verbose_name': 'Big Banner (790px * 298px)', 'width': 790, 'height': 298, 'opts': 'upscale'},
    'cropped': {'verbose_name': 'Cropped (60x60px)', 'width': 60, 'height': 60, 'opts': 'crop'},
    'croppedthumbnail': {'verbose_name': 'Cropped Thumbnail (140x140px)', 'width': 140, 'height': 140, 'opts': 'crop'},
}
FILEBROWSER_ADMIN_VERSIONS = ['fb_thumb', 'medium', 'big']

RAVEN_CONFIG = {
    'dsn': '',
    #'dsn': 'https://13ff024976e64688b097536d93caf2cd:9ae87f8e796e424c91466c9d5cde9574@app.getsentry.com/54436',
    # If you are using git, you can also automatically configure the
    # release based on the git info.
    #'release': raven.fetch_git_sha(os.path.dirname(__file__)),
}

# Cache key prefix
KEY_PREFIX = ''

PROJECT_VERSION = LazyWrapper("fabfile.get_version")

INTERNAL_IPS = ('127.0.0.1',)

RECAPTCHA_PUBLIC_KEY = '6LcrJesSAAAAAJMsqE27B1r0hGMgZYEU6UoRYnbY'
RECAPTCHA_PRIVATE_KEY = '6LcrJesSAAAAANtqkxhOXE_pV2P8D3yx_M69qUQ9'
RECAPTCHA_USE_SSL = True

ADMIN_TOOLS_MENU = 'menu.CustomMenu'
ADMIN_TOOLS_INDEX_DASHBOARD = 'dashboard.CustomIndexDashboard'
ADMIN_TOOLS_APP_INDEX_DASHBOARD = 'dashboard.CustomAppIndexDashboard'

AUTH_USER_MODEL = 'shop.User'

BROKER_URL = 'amqp://guest:guest@localhost:5672//'

CELERY_TIMEZONE = 'Europe/Istanbul'

CELERYBEAT_SCHEDULE = {}

NOTIFICATION_BACKENDS = [
    ("email", "notification.backends.email.EmailBackend"),
    ("message", "shop.modules.messaging.backends.MessageBackend"),
]

TINYMCE_JS_URL = STATIC_URL + 'tinymce/tinymce.min.js'
TINYMCE_DEFAULT_CONFIG = {
    'theme': "modern",
    "plugins": [
        "advlist autolink lists link image charmap print preview hr anchor pagebreak",
        "searchreplace wordcount visualblocks visualchars code fullscreen",
        "insertdatetime media nonbreaking save table contextmenu directionality",
        "emoticons template paste textcolor"
    ],
    'width': 700,
    "close_previous": "no",
    "toolbar1": "insertfile undo redo | styleselect | bold italic | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent | link image",
    "toolbar2": "print preview media | forecolor backcolor emoticons",
    "templates": [
        {"title": 'Test template 1', "content": 'Test 1'},
        {"title": 'Test template 2', "content": 'Test 2'}
    ]
}
ALLOWED_HOSTS = ['*']
TINYMCE_FILEBROWSER = True
FILEBROWSER_SAVE_FULL_URL = True
SIMIT_MENU_URLPATTERNS_MODULE = 'shop.urls'
SIMIT_PAGE_URL_NAME = 'shop_page'
COMPRESS_OUTPUT_DIR = 'compressed'

COMPRESS_CSS_FILTERS = [
    'compressor.filters.css_default.CssAbsoluteFilter',
    'compressor.filters.cssmin.CSSMinFilter'
]

SENTRY_AUTO_LOG_STACKS = True

SHOP_TEMPLATE = 'default'

ADMINS = (('Burak Emre', 'emrekabakci@gmail.com'),)

CELERY_RESULT_BACKEND = 'amqp'

DISABLE_DEBUG_TOOLBAR = False

try:
    config_module = __import__('settings_local')

    for setting in dir(config_module):
        if setting == 'CUSTOM_INSTALLED_APPS':
            INSTALLED_APPS += getattr(config_module, setting)
        elif setting == setting.upper():
            locals()[setting] = getattr(config_module, setting)
except ImportError:
    pass

if DEBUG and not DISABLE_DEBUG_TOOLBAR:
    TEMPLATE_CONTEXT_PROCESSORS += ('django.core.context_processors.debug', )
    MIDDLEWARE_CLASSES += ('debug_toolbar.middleware.DebugToolbarMiddleware',)
    INSTALLED_APPS += ('debug_toolbar',)
else:
    SESSION_COOKIE_SECURE = False
