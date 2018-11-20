# coding: utf-8

from __future__ import unicode_literals
from django.utils.translation import ugettext as _
from django.db import models
from shop.customer.models import CustomerGroup
from shop.fields import IntegerRangeField
from shop.models import Category, ProductTag

class Discount(models.Model):
    name = models.CharField(_('name'), max_length=255)
    percentage = IntegerRangeField(_('percentage'), min_value=0, max_value=100, blank=True, null=True, help_text=_("The percentage of discount will be applied to total price"))
    amount = models.DecimalField(_('amount'), max_digits=17, decimal_places=2, blank=True, null=True, help_text=_("The amount of discount will be applied to total price"))
    date_added = models.DateTimeField(_('added date'), auto_now_add=True)
    start_date = models.DateField(_('start date'), null=True, blank=True)
    end_date = models.DateField(_('end date'), null=True, blank=True)
    is_active = models.BooleanField(_('is active'), )
    customer_group = models.ManyToManyField(CustomerGroup, blank=True, null=True)
    category = models.ManyToManyField(Category, blank=True, null=True)
    product_tag = models.ManyToManyField(ProductTag, blank=True, null=True)
    minimum_order_price = models.DecimalField(_('minimum order price'), max_digits=17, decimal_places=2, blank=True, null=True)

    def __unicode__(self):
        return "%s (%s - %s)" % (self.name, self.start_date.strftime("%Y-%m-%d"), self.end_date.strftime("%Y-%m-%d"))

    class Meta:
        db_table = 'discount'
        verbose_name_plural = _("discounts")
        verbose_name = _("discount")