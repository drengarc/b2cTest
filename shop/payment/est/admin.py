from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.forms import PasswordInput, ModelForm
from django.utils.safestring import mark_safe
from admin_tools.admin import RichModelAdmin
from filebrowser.functions import path_to_url, version_generator, url_to_path
from filebrowser.settings import ADMIN_THUMBNAIL
from shop.models import Config
from shop.payment.est.models import Bank, InstallmentAlternative, ESTCredential, CreditCardESTRelation, Transaction, \
    CreditCardType


class BankAdmin(ModelAdmin):
    list_display = ('name', 'image_thumbnail')
    search_fields = ('name',)

    def image_thumbnail(self, obj):
        if obj.image and obj.image.filetype == "image":
            return '<img src="%s" />' % path_to_url(version_generator(url_to_path(unicode(obj.Image)), ADMIN_THUMBNAIL))
        else:
            return ""

    image_thumbnail.allow_tags = True


class InstallmentAlternativeAdmin(RichModelAdmin):
    list_filter = ('installment', 'package')
    only_one_of = ('discount_percentage', 'discount_amount')
    list_display = ('bank', 'installment', 'discount_percentage', 'discount_amount', 'minimum_price', 'maximum_price')


class ESTCredentialAdminForm(ModelForm):
    class Meta:
        model = ESTCredential
        widgets = {
            'password': PasswordInput(),
        }


class ESTCredentialAdmin(ModelAdmin):
    form = ESTCredentialAdminForm
    list_display = ('username', 'bank', 'client_id', 'default_choice')
    list_filter = ('bank',)
    search_fields = ('client_id', 'bank', 'username')

    def default_choice(self, model):
        active = Config.objects.conf("DEFAULT_ESTPACKAGE")
        return mark_safe('<input type="radio" name="default_choice" value="%s" %s>' % (
            model.id, ("checked" if str(model.id) == active else "")))

    default_choice.allow_tags = True


class CreditCardESTRelationAdmin(ModelAdmin):
    list_display = ('bin', 'est_cash', 'est_installment')
    search_fields = ('bin__bank__name', 'bin__bin')


class TransactionAdmin(ModelAdmin):
    list_display = ('ip', 'type', 'customer', 'order_id', 'est', 'amount', 'error_message', 'date')
    list_filter = ('type', 'date')


class CreditCardTypeAdmin(ModelAdmin):
    pass


admin.site.register(Bank, BankAdmin)
admin.site.register(CreditCardType, CreditCardTypeAdmin)
admin.site.register(CreditCardESTRelation, CreditCardESTRelationAdmin)
admin.site.register(ESTCredential, ESTCredentialAdmin)
admin.site.register(InstallmentAlternative, InstallmentAlternativeAdmin)
admin.site.register(Transaction, TransactionAdmin)