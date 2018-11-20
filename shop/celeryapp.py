#from __future__ import absolute_import

import os

from celery import Celery
from django.conf import settings
from raven import Client
from raven.contrib.celery import register_signal, register_logger_signal
import settings_local

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')

app = Celery('shop')

app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# if hasattr(settings, "RAVEN_CONFIG"):
#     client = Client(settings_local.RAVEN_CONFIG.get("dsn"))
# else:
#     client = Client()

# register a custom filter to filter out duplicate logs
# register_logger_signal(client)

# hook into the Celery error handler
# register_signal(client)