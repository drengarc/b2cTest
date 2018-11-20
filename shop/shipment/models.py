from __future__ import unicode_literals

from django.db import models
from django.utils.translation import ugettext_lazy as _

from filebrowser.fields import FileBrowseField


class ShipmentMethod(models.Model):
    name = models.CharField(max_length=50, blank=True, null=True, verbose_name=_('name'))
    is_active = models.BooleanField(verbose_name=_('is active'))
    image = FileBrowseField(_('image'), max_length=200, directory="images/shipment", extensions=[".jpg", ".jpeg", ".png", ".gif"], blank=True, null=True)

    class Meta:
        db_table = 'shipment_method'
        verbose_name = _('shipment method')
        verbose_name_plural = _('shipment methods')

    def __unicode__(self):
        return self.name


class ShipmentAlternative(models.Model):
    shipmentmethod = models.ForeignKey(ShipmentMethod)
    minimum_price = models.DecimalField(max_digits=9, blank=True, null=True, decimal_places=2, verbose_name=_('minimum price'))
    fixed_price = models.DecimalField(max_digits=9, blank=True, null=True, decimal_places=2, verbose_name=_('fixed price'))
    price_by_kg = models.DecimalField(max_digits=9, blank=True, null=True, decimal_places=2, verbose_name=_('price by kg'))

    class Meta:
        db_table = 'shipment_alternative'
        verbose_name = _('shipment alternative')
        verbose_name_plural = _('shipment alternatives')

    def __unicode__(self):
        return "%s (%s)" % (self.shipmentmethod.name, self.fixed_price)