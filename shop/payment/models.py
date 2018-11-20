# coding: utf-8

from __future__ import unicode_literals
from django.utils.translation import ugettext_lazy as _
from django.db import models
from filebrowser.fields import FileBrowseField
from shop.fields import IntegerRangeField


class PaymentPackage(models.Model):
    money_order_amount = models.DecimalField(max_digits=17, decimal_places=2, blank=True, null=True,
                                             verbose_name=_('money order discount amount'))
    money_order_percentage = IntegerRangeField(min_value=-100, max_value=+100, blank=True, null=True,
                                               verbose_name=_('money order discount percentage'))
    name = models.CharField(max_length=255, verbose_name=_('name'))

    class Meta:
        db_table = 'payment_package'
        verbose_name_plural = _("payment packages")
        verbose_name = _("payment package")

    def __unicode__(self):
        return self.name