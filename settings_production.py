
# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = [
    #'.example.com',
]

SECRET_KEY = 'u#n$q#q1ay&f1__5wygljknfskjnfsznv@q)uy=4sx6ho@)lafsdnfjksnd6kyyvv0h1kj'
MEDIA_URL = '/media/'
STATIC_URL = '/static/'
LANGUAGE_CODE = 'en_EN'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': '',
        'PORT': 0,
        'HOST': '',
        'USER': '',
        'PASSWORD': '',
        'TEST_CHARSET': "utf8",
        'TEST_COLLATION': "utf8_unicode_ci"
    }
}