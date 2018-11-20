# coding: utf-8

from django.db import models
from shop.models import Product, User
from django.utils.translation import ugettext as _
from shop.newsletter.models import MAILS

MAILS['price_drop_alert_customer'] = {'customer': 'Kullanıcı öğesi', 'product': 'Ürün', 'product_url': ''}


class PriceDropAlertEmail(models.Model):
    email = models.EmailField(_('email'))
    product = models.ForeignKey(Product, related_name="pricedrop_email")
    checkpoint_price = models.DecimalField(_('checkpoint price'), decimal_places=2, max_digits=17)
    saved_time = models.DateTimeField(auto_created=True, auto_now=True)

    class Meta:
        db_table = 'module_pricedropalert_email'
        verbose_name = 'Price Drop Alert Email List'
        unique_together = ('email', 'product')


class PriceDropAlertCustomer(models.Model):
    customer = models.ForeignKey(User)
    product = models.ForeignKey(Product, related_name="pricedrop_customer")
    checkpoint_price = models.DecimalField(_('checkpoint price'), decimal_places=2, max_digits=17)
    saved_time = models.DateTimeField(auto_created=True, auto_now=True)


    class Meta:
        db_table = 'module_pricedropalert_customer'
        verbose_name = 'Price Drop Alert Customer List'
        unique_together = ('customer', 'product')