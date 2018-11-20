import importlib

from django import test

from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.conf import settings
from django.db import connection
from django.test import Client
from django.test.utils import override_settings


logout_url = '/admin/logout/'

URL_NAMES = []

visitor = Client()
user = Client()


def load_url_pattern_names(patterns, prefix=''):
    """Retrieve a list of urlpattern names"""
    global URL_NAMES
    for pat in patterns:
        if pat.__class__.__name__ == 'RegexURLResolver':
            new_prefix = (prefix if prefix else "") + (pat.namespace if pat.namespace else '')
            load_url_pattern_names(pat.url_patterns, new_prefix)
        elif pat.__class__.__name__ == 'RegexURLPattern':  # load name from this RegexURLPattern
            if pat.name is not None and pat.name not in URL_NAMES:
                fullname = (prefix + ':' + pat.name) if prefix else pat.name
                try:
                    URL_NAMES.append((reverse(fullname, args=['1' for i in range(pat.regex.groups)]), prefix))
                except:
                    pass
    return URL_NAMES


@override_settings(PASSWORD_HASHERS=('django.contrib.auth.hashers.SHA1PasswordHasher',))
class UrlsTest(test.TestCase):
    def setUp(self):
        cursor = connection.cursor()
        db_name = cursor.db.settings_dict['NAME']


def test_request_generator(url, login_required=False, simulate=False, namespace=None):
    def test_method(self):
        response = None
        client = user if login_required else visitor
        try:
            response = client.get(url)
        except ObjectDoesNotExist:
            pass
        except Exception as e:
            self.fail("Error while fetching '%s' in rule with GET : %s" % (url, str(e)))
        finally:
            is_staff = False
            try:
                is_staff = response.context['request'].user.is_staff
            except:
                pass
            if namespace == 'admin' and response is not None and url != logout_url and login_required is False and getattr(
                    response, 'template_name', None) != 'admin/login.html':
                self.fail("SECURITY PROBLEM: '%s' is reachable even if the client is not staff." % (url,))
            if url == logout_url and login_required:
                self.client.login(username='buremba', password='lok651')

    return test_method


module = importlib.import_module(settings.ROOT_URLCONF)
cases = load_url_pattern_names(__import__(settings.ROOT_URLCONF).urlpatterns)
for i, case in enumerate(cases):
    test_name = 'test_{0}'.format(i)
    setattr(UrlsTest, test_name, test_request_generator(case[0], namespace=case[1]))

    test_name = 'test_{0}_user'.format(i)
    setattr(UrlsTest, test_name, test_request_generator(case[0], namespace=case[1], login_required=True))