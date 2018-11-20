from django.contrib import admin

from django.contrib.admin import ModelAdmin
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from shop.models import Config
from shop.payment.models import PaymentPackage


class PaymentPackageAdmin(ModelAdmin):
    fieldsets = (
        (None, {'fields': ('name', )}),
        (_('money order'), {'fields': ('money_order_amount', 'money_order_percentage')}),
    )
    list_display = ('name', 'money_order_amount', 'money_order_percentage', 'active')

    def active(self, r):
        active = Config.objects.conf("ACTIVE_PAYMENTPACKAGE")
        return mark_safe("<input type='radio' name='use' %s>" % ("checked" if str(r.id) == active else ""))
    active.allow_tags = True


admin.site.register(PaymentPackage, PaymentPackageAdmin)
