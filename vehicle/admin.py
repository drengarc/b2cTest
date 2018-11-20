import json

from django.conf.urls import patterns, url
from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.forms import ModelForm
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseServerError
from django.utils.translation import ugettext_lazy as _

from shop.widgets import TreeSelect
from shop.admin import ProductAdminForm, ProductAdmin, CategoryAdmin, CategoryAdminForm
from shop.models import Product, Category
from vehicle.models import VehicleBrand, VehicleBrandModel, VehicleBrandModelType, VehicleOther, FirmParameter, TaxRate, \
    ProductOriginal, Vehicle, VehicleTree, FuelType, MotorType, Currency


class SlugFillerModelAdmin(ModelAdmin):
    def save_model_(self, request, obj, form, change):
        if not change:
            obj.slug = "%s-%s" % (obj.parent.slug, obj.slug)
        obj.save()


class VehicleTreeAdminForm(ModelForm):
    model = VehicleTree

    class Meta:
        widgets = {
            'parent': TreeSelect(add_link=('vehicle', 'vehicle'))
        }


class VehicleTreeAdmin(ModelAdmin):
    list_filter = ()
    list_display = ('name',)
    search_fields = ('name', 'slug')
    form = VehicleTreeAdminForm
    prepopulated_fields = {'slug': ('name',), }

    def get_form(self, request, obj=None, **kwargs):
        form = super(VehicleTreeAdmin, self).get_form(request, obj, **kwargs)
        if "parent" in form.base_fields:
            form.base_fields['parent'].widget.can_add_related = False
        return form

    def get_urls(self):
        urls = super(VehicleTreeAdmin, self).get_urls()
        my_urls = patterns('', url(r'^fetch/?$', self.admin_site.admin_view(self.fetch),
                                   name="vehicle_%s_fetch" % self.model._meta.model_name)
        )
        return my_urls + urls

    def fetch(self, request):
        if "parent" not in request.GET:
            return HttpResponseServerError("this endpoint needs parent GET parameter")

        categories = VehicleTree.objects.filter(parent=request.GET['parent'])
        return HttpResponse(json.dumps([{'name': o.name, 'id': o.id} for o in categories]),
                            content_type='application/json')

    def __unicode__(self):
        return self.name


class VehicleBrandAdmin(VehicleTreeAdmin):
    inlines = []
    exclude = ("type", "parent")


    def add_view(self, request, form_url='', extra_context=None):
        parent = request.GET.get('parent')
        if parent:
            obj = VehicleTree.objects.get(pk=parent)
        if parent is not None:
            str = '?parent=%s&_popup=1' % parent
            if obj.level == 0:
                return HttpResponseRedirect(reverse("admin:vehicle_vehiclebrandmodel_add") + str)
            if obj.level == 1:
                return HttpResponseRedirect(reverse("admin:vehicle_vehiclebrandmodeltype_add") + str)
        else:
            return super(VehicleBrandAdmin, self).add_view(request, form_url, extra_context)


class VehicleBrandModelAdminForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(VehicleBrandModelAdminForm, self).__init__(*args, **kwargs)
        self.fields['parent'].queryset = VehicleBrand.objects.all()
        self.fields['parent'].required = True
        self.fields['parent'].widget.can_add_related = False
        self.fields['parent'].label = _('brand')

    class Meta:
        widgets = {
            'parent': TreeSelect(q=Q(type='BRAND'), proxy_model=False, max_depth=1,
                                 add_link=('vehicle', 'vehiclebrand'))
        }


def filter_generator(_title, _parameter_name, _model):
    class VehicleBrandFilter(admin.SimpleListFilter):
        title = _title
        parameter_name = _parameter_name

        def lookups(self, request, model_admin):
            b = []
            brands = _model.objects.all()
            for brand in brands:
                b.append((brand.id, brand))

            return b

        def queryset(self, request, queryset):
            if self.value() is not None:
                return queryset.filter(parent_id=self.value())

    return VehicleBrandFilter


class VehicleBrandModelAdmin(VehicleTreeAdmin, SlugFillerModelAdmin):
    inlines = []
    form = VehicleBrandModelAdminForm
    exclude = ("type",)
    list_display = ('name',)
    prepopulated_fields = {'slug': ('name',), }
    list_filter = (filter_generator(_('brand'), 'parent', VehicleBrand),)


class VehicleBrandModelTypeAdminForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(VehicleBrandModelTypeAdminForm, self).__init__(*args, **kwargs)
        self.fields['parent'].queryset = VehicleBrandModel.objects.all()
        self.fields['parent'].required = True
        self.fields['parent'].label = _('brand model')
        self.fields['parent'].widget.can_add_related = False

    class Meta:
        widgets = {
            'parent': TreeSelect(proxy_model=False, max_depth=2, add_link=('vehicle', 'vehiclebrand'))
        }


class VehicleBrandModelTypeAdmin(VehicleTreeAdmin, SlugFillerModelAdmin):
    inlines = []
    form = VehicleBrandModelTypeAdminForm
    exclude = ("type",)
    prepopulated_fields = {'slug': ('name',), }
    list_display = ('name',)
    list_filter = (filter_generator(_('brand model'), 'parent', VehicleBrandModel),)
    search_fields = ('name',)


class VehicleAdminForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(VehicleAdminForm, self).__init__(*args, **kwargs)
        self.fields['model_type'].queryset = VehicleBrandModelType.objects.all()
        self.fields['model_type'].label = _('model type')
        self.fields['model_type'].widget.can_add_related = False

    class Meta:
        widgets = {
            'vehicle_model_type': TreeSelect(proxy_model=False, max_depth=3, add_link=('vehicle', 'vehiclebrand'))
        }


class VehicleAdmin(ModelAdmin):
    form = VehicleAdminForm

    def get_urls(self):
        urls = super(VehicleAdmin, self).get_urls()
        my_urls = patterns('', url(r'^fetch/?$', self.admin_site.admin_view(self.fetch))
        )
        return my_urls + urls

    def fetch(self, request):
        if any(i not in request.GET for i in ["motortype", "fueltype", "modeltype"]):
            return HttpResponseServerError("this endpoint needs modeltype GET parameters")

        vehicles = Vehicle.objects.filter(vehicle_model_type=request.GET.get('modeltype'),
                                          motor_type_id=request.GET.get('motortype'),
                                          fuel_type_id=request.GET.get('fueltype')).values('id', 'begin_year',
                                                                                           'end_year')
        return HttpResponse(json.dumps(list(vehicles)), content_type='application/json')


class VehicleOtherAdminForm(CategoryAdminForm):
    def __init__(self, *args, **kwargs):
        super(VehicleOtherAdminForm, self).__init__(*args, **kwargs)
        self.fields['parent'].queryset = VehicleOther.objects.all()


class VehicleOtherAdmin(CategoryAdmin):
    exclude = ('vehicle_category',)
    form = VehicleOtherAdminForm

    def fetch(self, request):
        if "parent" not in request.GET:
            return HttpResponseServerError("this endpoint needs parent GET parameter")

        categories = VehicleOther.objects.filter(parent=request.GET['parent'])
        return HttpResponse(json.dumps([{'name': o.name, 'id': o.id} for o in categories]),
                            content_type='application/json')


class CustomProductAdminForm(ProductAdminForm):
    class Meta:
        widgets = {
            # 'vehicle': VehicleSelect(),
            'category': TreeSelect(add_link=('shop', 'category')),
        }


class CustomProductAdmin(ProductAdmin):
    form = CustomProductAdminForm

    fieldsets = (
        ('Information', {
            'fields': ('name', 'category', 'price', 'manufacturer', 'weight', 'partner_code', 'volume', 'attr')
        }),
        ('Purchasing', {
            'fields': ('active', 'quantity', 'discount_price', 'cargo_price')
        }),
        ('Page', {
            'fields': ('description',)
        }),
        ('Tags', {
            'fields': ('tags',)
        }),
    )


    def category_edit(self, arg):
        # return '<a href="%s">%s</a>' % (reverse('admin:shop_category_change', args=(arg.category_id,)), arg.category.name)
        return arg.category.name

    def get_form(self, request, obj=None, **kwargs):
        form = super(CustomProductAdmin, self).get_form(request, obj, **kwargs)
        # form.base_fields['vehicle'].widget.can_add_related = False
        return form

    class Media(ProductAdmin.Media):
        js = ProductAdmin.Media.js  # + ('admin/js/vehicle_admin.js', 'admin/vehicle/js/product_admin.js')


class CustomCategoryAdminForm(CategoryAdminForm):
    class Meta:
        widgets = {
            'parent': TreeSelect(add_link=('shop', 'category'), q=~Q(vehicle_category=True))
        }


class CustomCategoryAdmin(CategoryAdmin):
    exclude = ('vehicle_category', )
    form = CustomCategoryAdminForm

    def get_queryset(self, request):
        qs = super(CustomCategoryAdmin, self).get_queryset(request)
        return qs.exclude(vehicle_category=True)

    def fetch(self, request):
        if "parent" not in request.GET:
            return HttpResponseServerError("this endpoint needs parent GET parameter")

        categories = self.model.objects.filter(parent=request.GET['parent'])
        return HttpResponse(
            json.dumps([{'name': o.name, 'id': o.id, 'vehicle_category': o.vehicle_category} for o in categories]),
            content_type='application/json')

    def get_urls(self):
        urls = super(CustomCategoryAdmin, self).get_urls()
        my_urls = patterns('', url(r'^get/?$', self.admin_site.admin_view(self.get),
                                   name="%s_%s_get" % (self.model._meta.app_label, self.model._meta.model_name)))
        return my_urls + urls

    def get(self, request):
        if "id" not in request.GET:
            return HttpResponseServerError("this endpoint needs id GET parameter")

        category = self.model.objects.get(id=request.GET['id'])
        return HttpResponse(
            json.dumps({'name': category.name, 'id': category.id, 'vehicle_category': category.vehicle_category}),
            content_type='application/json')


class ProductOriginalAdmin(ModelAdmin):
    search_fields = ('oem_no', 'oem_no_original')
    list_display = ('get_product', 'oem_no', 'oem_no_original')
    raw_id_fields = ('product',)

    def get_product(self, obj):
        return obj.product


class TaxRateAdminForm(ModelForm):
    model = TaxRate

    def __init__(self, *args, **kwargs):
        super(TaxRateAdminForm, self).__init__(*args, **kwargs)
        self.fields['category'].widget.can_add_related = False

    class Meta:
        widgets = {
            'category': TreeSelect(add_link=('shop', 'category')),
        }


class TaxRateAdmin(ModelAdmin):
    list_display = ('get_category', 'tax_rate')
    form = TaxRateAdminForm

    def get_category(self, obj):
        return obj.category


class FuelTypeAdmin(ModelAdmin):
    def get_urls(self):
        urls = super(FuelTypeAdmin, self).get_urls()
        my_urls = patterns('', url(r'^fetch/?$', self.admin_site.admin_view(self.fetch))
        )
        return my_urls + urls

    def fetch(self, request):
        if any(i not in request.GET for i in ["motortype", "modeltype"]):
            return HttpResponseServerError("this endpoint needs motortype and modeltype GET parameters")
        fuel_type_ids = Vehicle.objects.filter(vehicle_model_type=request.GET.get('modeltype'),
                                               motor_type=request.GET.get('motortype')).distinct('fuel_type').values(
            'fuel_type')
        fuel_types = FuelType.objects.filter(id__in=[i['fuel_type'] for i in fuel_type_ids]).values('id', 'name')
        return HttpResponse(json.dumps(list(fuel_types)), content_type='application/json')


class MotorTypeAdmin(ModelAdmin):
    def get_urls(self):
        urls = super(MotorTypeAdmin, self).get_urls()
        my_urls = patterns('', url(r'^fetch/?$', self.admin_site.admin_view(self.fetch))
        )
        return my_urls + urls

    def fetch(self, request):
        if "modeltype" not in request.GET:
            return HttpResponseServerError("this endpoint needs modeltype GET parameters")

        motor_type_ids = Vehicle.objects.filter(vehicle_model_type=request.GET.get('modeltype')).distinct(
            'motor_type').values('motor_type')
        motor_types = MotorType.objects.filter(id__in=[i['motor_type'] for i in motor_type_ids]).values('id', 'name')
        return HttpResponse(json.dumps(list(motor_types)), content_type='application/json')


class CurrencyAdmin(ModelAdmin):
    pass


admin.site.unregister(Product)
admin.site.unregister(Category)
admin.site.register(Product, CustomProductAdmin)
admin.site.register(Category, CustomCategoryAdmin)
admin.site.register(VehicleBrand, VehicleBrandAdmin)
admin.site.register(VehicleBrandModel, VehicleBrandModelAdmin)
admin.site.register(VehicleBrandModelType, VehicleBrandModelTypeAdmin)
admin.site.register(Vehicle, VehicleAdmin)
admin.site.register(VehicleOther, VehicleOtherAdmin)
admin.site.register(FirmParameter)
admin.site.register(FuelType, FuelTypeAdmin)
admin.site.register(MotorType, MotorTypeAdmin)
admin.site.register(TaxRate, TaxRateAdmin)
admin.site.register(ProductOriginal, ProductOriginalAdmin)
admin.site.register(Currency, CurrencyAdmin)