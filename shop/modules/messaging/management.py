# coding: utf-8
from django.db.models.signals import post_syncdb
import notification


def create_notice_types(app, created_models, verbosity, **kwargs):
    notification.create_notice_type("product_price_change_in_basket", "Fiyat Güncellemesi", "Sepetinizdeki ürünlerden birinin fiyatı değişti.")

post_syncdb.connect(create_notice_types, sender=notification)