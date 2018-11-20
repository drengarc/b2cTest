# coding: utf-8

from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from django.db import models
from django.utils.translation import ugettext as _
from django.conf import settings

from shop.models import Product, Language, User, Ilce, City
from shop.newsletter.models import MAILS
from shop.shipment.models import ShipmentAlternative
from vehicle.models import Toptanci

MAILS['order_status_change'] = {'order': ''}
MAILS['user_welcome'] = {'customer': 'Kullanıcı öğesi'}
MAILS['new_order'] = {'order': ''}
MAILS['pending_money_order'] = {'customer': 'Kullanıcı öğesi', 'orders_url': '', 'order_time': '', 'message_url':''}

RATING_CHOICES = (
    (1, '★'),
    (2, '★★'),
    (3, '★★★'),
    (4, '★★★★'),
    (5, '★★★★★'),
)

ORDER_STATUS_CHOICES = (
    (1, 'Sipariş alındı / Ödeme bekleniyor'),
    (2, 'Ödeme işlemi tamamlandı.'),
    (3, 'Siparişiniz tedarik sürecinde.'),
    (4, 'Siparişiniz hazırlandı.'),
    (5, 'Siparişiniz gönderildi.'),
    (6, 'Siparişiniz iptal edildi.'),
    (7, 'Geri ödeme tamamlandı.'),
)

ORDER_PAYMENT_TYPES = (
    (1, _('credit card')),
    (2, _('money order')),
    (3, _('3d pay')),
)


class CustomerGroup(models.Model):
    name = models.CharField(_('name'), max_length=255)

    class Meta:
        db_table = 'customer_group'
        verbose_name_plural = _("customer groups")
        verbose_name = _("customer group")

    def __unicode__(self):
        return self.name


class CustomerAddress(models.Model):
    customer = models.ForeignKey(User)
    address_name = models.CharField(_('address name'), max_length=100)
    first_name = models.CharField(_('first name'), max_length=255)
    last_name = models.CharField(_('last name'), max_length=150)
    address = models.TextField(_('address'), max_length=255)
    postcode = models.IntegerField(_('post code'), blank=True, null=True)
    land_line = models.CharField(_('land line'), max_length=50, blank=True, null=True)
    cell_phone = models.CharField(_('cell phone'), max_length=50)
    ilce = models.ForeignKey(Ilce, blank=True, null=True)
    identity_number = models.CharField(_('identity number'), max_length=50, blank=True, null=True)
    tax_authority = models.CharField(_('tax authority'), max_length=100, blank=True, null=True)
    tax_no = models.CharField(_('tax no'), max_length=100, blank=True, null=True)

    class Meta:
        db_table = 'customer_address'
        verbose_name_plural = _("customer addresses")
        verbose_name = _("customer address")

    def __unicode__(self):
        return "%s %s (%s)" % (self.first_name, self.last_name, self.address[:100])


class CustomerBasket(models.Model):
    customer = models.ForeignKey(User)
    product = models.ForeignKey(Product)
    quantity = models.IntegerField(_('quantity'), )
    date_added = models.DateTimeField(_('added date'), auto_now=True)
    sase_code = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'customer_basket'
        unique_together = ('customer', 'product')


class Order(models.Model):
    receipt_id = models.CharField(unique=True, max_length=25, editable=False)
    customer = models.ForeignKey(User, editable=False)
    discount = models.DecimalField(max_digits=17, decimal_places=2, editable=False)
    delivery_name = models.CharField(_('delivery name'), max_length=200, editable=False)
    delivery_address = models.TextField(_('delivery address'), editable=False)
    delivery_city = models.ForeignKey(City, related_name="OrderDelivery_City", editable=False)
    delivery_phone = models.CharField(_('delivery address phone number'), max_length=250, editable=False)
    billing_name = models.CharField(_('billing name'), max_length=250, blank=True, null=True, editable=False)
    billing_address = models.TextField(_('billing address'), blank=True, null=True, editable=False)
    billing_city = models.ForeignKey(City, related_name="OrderBilling_City", blank=True, null=True, editable=False)
    billing_phone = models.CharField(_('billing address phone number'), max_length=40, blank=True, null=True,
                                     editable=False)
    products = models.ManyToManyField(Product, through="OrderProduct", editable=False)
    cc_owner = models.CharField(_('credit card owner'), max_length=40, blank=True, editable=False)
    cc_number_last = models.CharField(_('credit card number'), max_length=4L, blank=True, editable=False)
    date_processed = models.DateTimeField(_('purchased date'), null=True, blank=True, auto_created=True, auto_now=True,
                                          editable=False)
    final_price = models.DecimalField(_('final price'), max_digits=10, decimal_places=2, editable=False)
    final_kdv = models.DecimalField(_('final kdv'), max_digits=10, decimal_places=2, editable=False)
    shipment_price = models.DecimalField(_('shipment price'), max_digits=10, decimal_places=2, editable=False)
    shipment_alternative = models.ForeignKey(ShipmentAlternative)
    comment = models.TextField(_('comment'), blank=True, null=True, editable=False)
    cargo_no = models.CharField(_('cargo tracking number'), max_length=100, blank=True, null=True)
    payment_type = models.PositiveSmallIntegerField(_('payment type'), choices=ORDER_PAYMENT_TYPES)

    class Meta:
        db_table = 'order'
        verbose_name_plural = _("orders")
        verbose_name = _("order")

    def total_basket(self):
        return self.final_price - self.shipment_price

    def final_net_basket(self):
        return self.total_basket() - self.final_kdv

    def total_net_basket(self):
        return (self.total_basket() - self.final_kdv) + self.discount

    def get_url(self):
        return settings.SITE_URL + self.get_absolute_url()

    def get_absolute_url(self):
        return reverse('shop_customer_order', self.receipt_id)

    @models.permalink
    def get_absolute_url(self):
        return 'shop_customer_order', [self.receipt_id]

    def __unicode__(self):
        return self.receipt_id


class OrderStatus(models.Model):
    order = models.ForeignKey(Order, related_name="statutes")
    order_status_type_id = models.IntegerField(choices=ORDER_STATUS_CHOICES)
    time = models.DateTimeField(_('added date'), auto_created=True, auto_now=True)
    comments = models.TextField(_('comment'), blank=True, null=True)

    class Meta:
        db_table = 'order_status'
        verbose_name_plural = _("order status histories")
        verbose_name = _("order status history")

    def __unicode__(self):
        return self.get_order_status_type_id_display()

    def to_dict(self):
        return {"order_id": self.order_id, "status": self.get_order_status_type_id_display(), "time": str(self.time),
                "comments": self.comments}


class OrderProduct(models.Model):
    order = models.ForeignKey(Order)
    product = models.ForeignKey(Product)
    quantity = models.IntegerField(_('quantity'), null=False, blank=True)
    price = models.DecimalField(_('price'), max_digits=9, decimal_places=2)
    discount = models.DecimalField(_('discount'), max_digits=9, decimal_places=2)
    vehicle_toptanci = models.ForeignKey(Toptanci, null=True, blank=True)
    sase_code = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        db_table = 'order_product'
        verbose_name = _('ordered product')
        verbose_name_plural = _('ordered products')


class ProductReview(models.Model):
    product = models.ForeignKey(Product)
    user = models.ForeignKey(User)
    rating = models.SmallIntegerField(_('rating'), null=True, choices=RATING_CHOICES)
    date_added = models.DateTimeField(_('added date'), null=True, blank=True)
    status = models.IntegerField(_('status'), )
    language = models.ForeignKey(Language)
    text = models.TextField(_('review'), )

    class Meta:
        db_table = 'product_review'
        verbose_name_plural = _("product reviews")
        verbose_name = _("product review")