# coding: utf-8

from django.db import models
from shop.models import Product, User
from django.utils.translation import ugettext as _
from shop.newsletter.models import MAILS


MAILS['stock_alert_customer'] = {'customer': 'Kullanıcı öğesi', 'product': 'Ürün'}


class StockAlertCustomer(models.Model):
    customer = models.ForeignKey(User)
    product = models.ForeignKey(Product, related_name="stockalert_customer")
    saved_time = models.DateTimeField(auto_created=True, auto_now=True)

    class Meta:
        db_table = 'module_stockalert_customer'
        verbose_name = _('Stock Alert Customer List')
        unique_together = ('customer', 'product')

    def __unicode__(self):
        return "%s is tracking %s" % (self.customer, self.product)