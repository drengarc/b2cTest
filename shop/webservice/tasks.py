# -*- coding: utf-8 -*-
from datetime import timedelta
from xml.etree import ElementTree

from lxml import etree
from celery.task import task
import requests
from django.conf import settings

from shop.importer.views import process, COLUMNS


TAGS = {
    '{http://tempuri.org/}STOK_KOD': 'stok_kodu',
    '{http://tempuri.org/}STOK_AD': 'stok_ad',
    '{http://tempuri.org/}TEDARIKCI': 'tedarikci',
    '{http://tempuri.org/}MARKA': 'marka',
    '{http://tempuri.org/}MODEL': 'arac_model',
    '{http://tempuri.org/}MODEL_TIP': 'arac_model_tip',
    '{http://tempuri.org/}MOTOR_TIP': 'motor_tip',
    '{http://tempuri.org/}YAKIT_TIP': 'yakit_tip',
    '{http://tempuri.org/}BASLANGIC_YIL': 'arac_baslangic_yil',
    '{http://tempuri.org/}BITIS_YIL': 'arac_bitis_yil',
    '{http://tempuri.org/}KIRILIM1': 'kirilim1',
    '{http://tempuri.org/}KIRILIM2': 'kirilim2',
    '{http://tempuri.org/}KIRILIM3': 'kirilim3',
    '{http://tempuri.org/}DEPO_MIKTAR': 'depo_miktar',
    '{http://tempuri.org/}LISTE_FIYAT': 'liste_fiyat',
    '{http://tempuri.org/}LISTE_FIYAT_DOVIZ': 'liste_fiyat_doviz',
    '{http://tempuri.org/}ISKONTO': 'iskonto',
    '{http://tempuri.org/}ISKONTO2': 'iskonto2',
    '{http://tempuri.org/}ISKONTO3': 'iskonto3',
    '{http://tempuri.org/}KAMPANYA_FIYAT': 'kampanya_fiyat',
    '{http://tempuri.org/}KAMPANYA_FIYAT_DOVIZ': 'kampanya_fiyat_doviz',
    '{http://tempuri.org/}KDV': 'kdv',
    '{http://tempuri.org/}KARGO_BEDELI': 'kargo_fiyat',
    '{http://tempuri.org/}YENI_URUN_E_H': 'yeni_urun'
}


@task(name='import-products-webservice')
def import_products_webservice():
    content = requests.get("http://212.156.123.190:81/WebPaylasim/Service1.asmx/GetAllStok").content
    parser = etree.XMLParser(encoding="utf-8")
    tree = ElementTree.fromstring(unicode(content, 'utf-8'), parser=parser)
    columns = None
    rows = []
    for row in tree:
        if columns is None:
            columns = []
            for col in row:
                columns.append(COLUMNS[TAGS[col.tag]])
        r = []
        for col in row:
            r.append(col.text)
        rows.append(r)
    process(columns, rows)


settings.CELERYBEAT_SCHEDULE['import-products-webservice-per-3hours'] = {
    'task': 'import-products-webservice',
    'schedule': timedelta(hours=3),
}