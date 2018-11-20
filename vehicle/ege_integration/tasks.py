# -*- coding: utf-8 -*-
import decimal
import json
import logging
import urllib
import urllib2
from celery.task import task
from datetime import timedelta
from django.conf import settings
import xml.etree.ElementTree as ET
from raven.contrib.django.models import get_client
from shop import helpers
from shop.models import Config
from vehicle.models import Currency, KarMarji

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())


def normalize_name(name):
    if len(name) > 2:
        return name.title()
    else:
        return name.upper()


def fetch_rakip_kodlar(product_id):
    cursor = helpers.Connection()
    return cursor.fetchall("select rakip.rakip_firma_kodu, rakip_firma_kodu_orjinal_yazilisi, rakip_tedarikci_adi \
                            from ege.tb_kart_stok_rakip_kodlar rakip \
                             join public.product on (product.grup_id = rakip.grup_id) where product.id = %s",
                           [product_id])


def fetch_oem_codes(product_id):
    cursor = helpers.Connection()
    return cursor.fetchall("select oem.oem_no, oem_no_orjinal, oem.arac_marka \
                            from ege.tb_kart_stok_oem oem \
                            join public.product on (product.grup_id = oem.grup_id) where product.id = %s", [product_id])


@task(name='update-parities')
def fetch_parities():
    tree = ET.fromstring(urllib.urlopen("http://www.tcmb.gov.tr/kurlar/today.xml").read())

    for currency in Currency.objects.all():
        data = tree.find('Currency[@CurrencyCode="%s"]/BanknoteSelling' % currency.code)
        if data is not None:
            currency.parity = decimal.Decimal(data.text)
            currency.save()


settings.CELERYBEAT_SCHEDULE['egeintegration-fetch-parities'] = {
    'task': 'update-parities',
    'schedule': timedelta(hours=8),
}