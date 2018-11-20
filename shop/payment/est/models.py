# coding: utf-8

from django.db import models
from django.utils.translation import ugettext as _
from filebrowser.fields import FileBrowseField
from shop.fields import IntegerRangeField
from shop.models import User
from django.conf import settings
from shop.payment.est.est import BANKS
from shop.payment.models import PaymentPackage

TRANSACTION_TYPES = (
    (1, 'est_pay'),
    (2, 'est_3d_pay_post'),
    (3, 'est_3d_pay_return'),
)

GATEWAYS = (
    'est',
    'denizbank',
    'vpos'
)


class ESTCredential(models.Model):
    bank = models.CharField(choices=[(bank, bank) for bank in BANKS.keys()], max_length=30)
    client_id = models.CharField(max_length=100)
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    secret_key = models.CharField(max_length=100)
    gateway = models.CharField(choices=[(gateway, gateway) for gateway in GATEWAYS], max_length=30)

    def __unicode__(self):
        return "(%s, %s) %s" % (self.client_id, self.username, self.bank)

    def bank_prop(self, prop):
        return BANKS[self.bank].get(prop)

    def bank_url(self, prop):
        return (self.bank_prop('testhost') if settings.DEBUG else self.bank_prop('host')) + self.bank_prop(prop)


class Transaction(models.Model):
    ip = models.IPAddressField(_('client IP address'))
    type = models.PositiveSmallIntegerField(choices=TRANSACTION_TYPES)
    customer = models.ForeignKey(User)

    # It's not ForeignKey because if the result is a failure, we do not create the Order.
    order_id = models.CharField(blank=True, null=True, max_length=15)
    est = models.ForeignKey(ESTCredential, null=True, blank=True)
    date = models.DateTimeField(_('date'), auto_created=True, auto_now=True)
    amount = models.DecimalField(_('amount of transaction'), max_digits=10, decimal_places=2)
    error_message = models.CharField(max_length=200)

    class Meta:
        verbose_name = _('EST transaction')
        verbose_name_plural = _('EST transactions')


class Bank(models.Model):
    name = models.CharField(max_length=100)
    image = FileBrowseField(_('image'), max_length=200, directory="images/bank",
                            extensions=[".jpg", ".jpeg", ".png", ".gif"], blank=True, null=True)

    def __unicode__(self):
        return self.name


class CreditCardType(models.Model):
    bank = models.ForeignKey(Bank)
    image = FileBrowseField(_('image'), max_length=200, directory="images/credit_card_type",
                            extensions=[".jpg", ".jpeg", ".png", ".gif"], blank=True, null=True)
    bin = models.IntegerField(primary_key=True)
    type = models.CharField(max_length=100)
    subtype = models.CharField(max_length=100)

    def __unicode__(self):
        return "%s %s" % (self.bank.name, self.bin)


class CreditCardESTRelation(models.Model):
    bin = models.ForeignKey(CreditCardType,
                            help_text="Kullanıcının girdiği kredi kartı numarasının sahip olduğu BIN numarası")
    est_cash = models.ForeignKey(ESTCredential, related_name="est_cash",
                                 help_text="Kullanıcı ödemeyi peşin yapmak istediğinde kullanılacak EST hesabınız")
    est_installment = models.ForeignKey(ESTCredential, related_name="est_installment",
                                        help_text="Kullanıcı ödemeyi taksitli yapmak istediğinde kullanılacak EST hesabınız")

    class Meta:
        unique_together = ('bin', 'est_cash', 'est_installment')
        verbose_name_plural = _('est relations')
        verbose_name = _('est relation')


class InstallmentAlternative(models.Model):
    package = models.ForeignKey(PaymentPackage)
    bank = models.ForeignKey(Bank)
    discount_percentage = IntegerRangeField(min_value=-100, max_value=+100, blank=True, null=True,
                                            verbose_name=_('percentage'), help_text=_(
            'The percentage of discount will be applied for this payment alternative'))
    discount_amount = models.DecimalField(max_digits=17, decimal_places=2, blank=True, null=True, verbose_name=_('amount'), help_text=_(
        'The amount of discount will be applied for this payment alternative'))
    installment = models.PositiveSmallIntegerField(verbose_name=_('installment'))
    minimum_price = models.DecimalField(max_digits=17, decimal_places=2, blank=True, null=True,
                                        verbose_name=_('minimum price'))
    maximum_price = models.DecimalField(max_digits=17, decimal_places=2, blank=True, null=True,
                                        verbose_name=_('maximum price'))
    description = models.TextField(_('description'), blank=True, null=True)

    class Meta:
        verbose_name_plural = _("installment alternatives")
        verbose_name = _("installment alternative")

    def __unicode__(self):
        return "%s (%s %s)" % (self.bank.name, self.installment, _('installment'))
