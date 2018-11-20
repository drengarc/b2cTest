# coding: utf-8

import json
from django import forms
from django.conf.urls import patterns, url
from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.admin.util import flatten_fieldsets
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm, ReadOnlyPasswordHashField
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseRedirect
from shop.customer.models import CustomerGroup, CustomerAddress, Order, ProductReview, OrderStatus, \
    ORDER_STATUS_CHOICES, \
    CustomerBasket
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import load_backend, login

from django.core.urlresolvers import reverse_lazy, reverse
from admin_tools.menu import items
from menu import register_menu_item
from shop.models import User
from django.conf import settings

class CustomerGroupAdmin(ModelAdmin):
    pass


class OrderStatusFilter(admin.SimpleListFilter):
    title = _('current status')

    parameter_name = 'status'

    def lookups(self, request, model_admin):
        return ORDER_STATUS_CHOICES

    def queryset(self, request, queryset):
        if self.value() is not None:
            ids = []
            value = int(self.value())
            for q in queryset:
                model = q.orderstatus_set.order_by('time').last()
                if model is None or model.status_id != value:
                    ids.append(q.pk)
            return queryset.exclude(pk__in=ids)


class OrderAdmin(ModelAdmin):
    list_display = ('id', 'customer', 'final_price', 'date_processed', 'status', 'process', 'cancel')
    list_filter = ('customer', 'date_processed', 'final_price', OrderStatusFilter)

    class Media:
        css = {
            'all': ('admin/order/order_page.css',)
        }
        js = ('admin/order/order_page.js',)

    def get_urls(self):
        urls = super(OrderAdmin, self).get_urls()
        my_urls = patterns('',
                           url(r'^status/([0-9A-Za-z]+)?$', self.admin_site.admin_view(self.get_status),
                               name="customer_order_status"),
                           url(r'^change_status/([0-9A-Za-z]+)?$', self.admin_site.admin_view(self.change_status),
                               name="customer_order_changestatus")
        )
        return my_urls + urls

    def change_status(self, request, order_id):
        if request.method == 'POST':
            try:
                order = Order.objects.get(receipt_id=order_id)
            except ObjectDoesNotExist:
                return HttpResponse(_("Order does not exist"))
            order.cargo_no = request.POST.get("cargo_no")
            order.save()
            try:
                OrderStatus.objects.get(order=order, status_id=2)
            except ObjectDoesNotExist:
                return HttpResponse(_("Order status is not suitable for this operation"))
            OrderStatus(order=order, status_id=3).save()
            return HttpResponse(_('Order successfully marked as shipped.'))

        return HttpResponse("1")

    def get_status(self, request, id):
        return HttpResponse(
            json.dumps([model.to_dict() for model in OrderStatus.objects.filter(order_id__receipt_id=id)]),
            content_type="application/json")

    def process(self, model):
        status = OrderStatus.objects.filter(order_id=model.id).order_by('time').last()
        if status is not None:
            if status.order_status_type_id == 6:
                return '<button class="red approveRefund" data-href="%s">İptal işlemi tamamlandı olarak işaretle</button>' % reverse(
                    "admin:customer_order_changestatus", args=(model.id,))
            elif status.order_status_type_id == 4:
                return '<button class="red markShipped" data-href="%s">Sipariş kargo numarasını gir</button>' % reverse(
                    "admin:customer_order_changestatus", args=(model.id,))
            else:
                return ''

    def cancel(self, model):
        status = OrderStatus.objects.filter(order_id=model.id).order_by('time').last()
        if status is not None:
            if status.order_status_type_id < 6:
                return '<button class="red refund" data-href="%s">Siparişi iptal et</button>' % reverse(
                    "admin:customer_order_changestatus", args=(model.id,))

    process.allow_tags = True
    cancel.allow_tags = True

    def status(self, model):
        status = OrderStatus.objects.filter(order_id=model.id).order_by('time').last()

        if status is not None:
            '''return '<select class="status">%s</select><div class="order-history"></div>' % "".join(
                ["<option value='%s' %s>%s</option>" % (
                    choice[0], "selected" if status.status_id == choice[0] else "", choice[1].encode('utf-8')) for choice in
                 ORDER_TYPE_CHOICES])'''
            return '<p class="status">%s</p><div data-href="%s" class="order-history"></div>' % (
                status.get_order_status_type_id_display(),
                reverse('admin:customer_order_status', args=(model.id,)))
        else:
            return None

    status.allow_tags = True

    def has_add_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return True

    def change_view_(self, request, object_id, form_url='', extra_context=None):
        extra_context = {''}
        return HttpResponse('Unauthorized', status=401)

    def get_readonly_fields(self, request, obj=None):
        if self.declared_fieldsets:
            return flatten_fieldsets(self.declared_fieldsets)
        else:
            return list(set(
                [field.name for field in self.opts.local_fields if field.name != 'cargo_no'] +
                [field.name for field in self.opts.local_many_to_many if field.name != 'cargo_no']
            ))


class UserChangeForm(forms.ModelForm):
    """A form for updating users. Includes all the fields on
    the user, but replaces the password field with admin's
    password hash display field.
    """
    password = ReadOnlyPasswordHashField(label=_("Password"),
                                         help_text=_("Raw passwords are not stored, so there is no way to see "
                                                     "this user's password, but you can change the password "
                                                     "using <a href=\"password/\">this form</a>."))

    class Meta:
        model = get_user_model()
        #fields = ['email', 'password', 'date_of_birth', 'is_active', 'is_admin']

    def clean_password(self):
        # Regardless of what the user provides, return the initial value.
        # This is done here, rather than on the field, because the
        # field does not have access to the initial value
        return self.initial["password"]


class UserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = get_user_model()

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super(UserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class CustomerAdmin(UserAdmin):
    # The forms to add and change user instances
    form = UserChangeForm
    add_form = UserCreationForm
    ordering = ('email',)

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    filter_horizontal = ()
    list_filter = ('is_active', 'group')
    list_display = ('email', 'is_active', 'get_full_name', 'last_login', 'group')
    search_fields = ('first_name', 'last_name', 'email')
    ordering = ('email',)
    fieldsets = (
        (None, {'fields': ('email', 'password', 'is_active', 'group')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'is_active', 'last_name', 'password1', 'password2', 'group')}
        ),
    )

    def get_urls(self):
        urls = super(CustomerAdmin, self).get_urls()
        my_urls = patterns('', url(r'^login_as/([0-9]+)?$', self.admin_site.admin_view(self.login_as),
                                   name="customer_login_as")
        )
        return my_urls + urls

    def login_as(self, request, user_id):
        user = User.objects.get(pk=user_id)

        if not hasattr(user, 'backend'):
            for backend in settings.AUTHENTICATION_BACKENDS:
                if user == load_backend(backend).get_user(user.pk):
                    user.backend = backend
                    break

        # Save the original user pk before it is replaced in the login method
        original_user_pk = request.user.pk

        # Log the user in.
        if hasattr(user, 'backend'):
            login(request, user)

        # Set a flag on the session
        session_flag = getattr(settings, "LOGINAS_FROM_USER_SESSION_FLAG", "loginas_from_user")
        request.session[session_flag] = original_user_pk

        return HttpResponseRedirect(reverse("shop_homepage"))


class AdminProductReview(ModelAdmin):
    def has_add_permission(self, request):
        return False


class CustomerBasketAdmin(ModelAdmin):
    list_display = ('customer', 'product', 'quantity', 'date_added')


admin.site.register(CustomerGroup, CustomerGroupAdmin)
admin.site.register(CustomerAddress)
admin.site.register(User, CustomerAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(ProductReview, AdminProductReview)
admin.site.register(CustomerBasket, CustomerBasketAdmin)


@register_menu_item
def menu_items():
    return items.ModelList(
        title=_('Customer'),
        models=('shop.customer.*', ),
        url=reverse_lazy('admin:app_list', kwargs={'app_label': 'customer'}),
        exclude=('shop.customer.models.CustomerAddress', 'shop.customer.models.CustomerGroup',)
    )