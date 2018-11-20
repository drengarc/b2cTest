# -*- coding: utf-8 -*-
import json
from admin_tools.menu import items

from django.conf import settings
from django.conf.urls import patterns, url
from django.contrib.admin.options import ModelAdmin
from django.contrib.admin import StackedInline, TabularInline
from django.contrib import admin
from django.core.urlresolvers import reverse_lazy, reverse
from django.utils.translation import ugettext as _
from django.forms.models import ModelForm
from django import forms

from django.contrib.contenttypes.models import ContentType
from django.db.models import Max
from django.http import HttpResponseServerError, HttpResponse
from django.utils.text import slugify
from django.shortcuts import render_to_response
from feincms.admin.tree_editor import TreeEditor

from admin_tools.admin import SortableModelAdmin
from admin_tools.forms import SortableTabularInline
from filebrowser.functions import path_to_url, version_generator, url_to_path
from filebrowser.settings import ADMIN_THUMBNAIL
from menu import register_last_menu_item, register_menu_item
from shop.webservice.tasks import import_products_webservice
from shop.widgets import TreeSelect
from shop.importer.views import importer
from shop.models import ProductImage, ProductPage, Product, Category, City, Country, Language, \
    Manufacturer, ProductTag, Synonym, ProductAttribute, ProductAttributeChoice, Config
from shop.tasks import import_images


class ProductTagAdmin(ModelAdmin):
    prepopulated_fields = {'slug': ('name',), }
    search_fields = ("name", "slug")
    list_display = ('name',)

    def list_product(self, tag):
        return "<a href="">"

    class Media:
        js = ('js/prepopulate_fieldset.js',)

    def view_on_site(self, obj):
        return reverse('shop_tag_page', args=[obj.slug])


class ProductImagesInline(SortableTabularInline):
    model = ProductImage
    extra = 1
    sortable = 'order'


class ProductSeoInline(StackedInline):
    model = ProductPage
    max_num = 1


class ProductAdminForm(ModelForm):
    model = Product

    class Meta:
        widgets = {
            'category': TreeSelect(add_link=('shop', 'category'))
        }


class ProductPriceFilter(admin.SimpleListFilter):
    title = _('price')
    parameter_name = 'price'

    def lookups(self, request, model_admin):
        model = model_admin.model
        max_value = model.objects.aggregate(Max(self.parameter_name))['price__max']
        if max_value is not None:
            max_value = int(max_value)
            if max_value < 10:
                return ()
        else:
            return ()
        s = 5

        step = max_value / s
        arr = []
        for i in range(s):
            arr.append((("%s-%s" % ((i * step), ((i + 1) * step))), ("%s < %s" % (i * step, (i + 1) * step))))

        return arr

    def queryset(self, request, queryset):
        if self.value() is not None:
            v = self.value().split('-')
            return queryset.filter(price__gte=v[0], price__lte=v[1])


class ProductAdmin(ModelAdmin):
    class Media:
        js = ('js/prepopulate_fieldset.js',)

    filter_horizontal = ('tags',)
    change_form_template = "admin/product/change_form.html"
    form = ProductAdminForm
    list_editable = ('active',)
    search_fields = ('name', 'manufacturer__name', 'category__name')
    list_display = ('name', 'category_edit', 'manufacturer_edit', 'active', 'display_view')
    list_filter = ('active', 'category', ProductPriceFilter, 'tags', 'manufacturer', 'date_added')
    fieldsets = (
        ('Information', {
            'fields': ('name', 'category', 'price', 'manufacturer', 'weight', 'product_code', 'attr')
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
    inlines = [ProductImagesInline]
    save_as = True

    def get_urls(self):
        urls = super(ProductAdmin, self).get_urls()
        my_urls = patterns('',
                           url(r'^import/?$', self.admin_site.admin_view(importer), name="shop_product_import"),
                           url(r'^import_image/?$', self.admin_site.admin_view(self.submit_image_task), name="shop_product_import_image"),
                           url(r'^import_dega/?$', self.admin_site.admin_view(self.import_dega), name="shop_product_import_dega")
        )
        return my_urls + urls

    @staticmethod
    def submit_image_task(request):
        # try:
        return HttpResponse(import_images(request.GET.get('directory')))
            # return HttpResponse("1")
        # except Exception, e:
        #     return HttpResponse("HATA: %s" % e)

    @staticmethod
    def import_dega(request):
        import_products_webservice()
        return HttpResponse("aktarildi")

    def get_form(self, request, obj=None, **kwargs):
        form = super(ProductAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['category'].widget.can_add_related = False
        return form

    def display_view(self, arg):
        return '<a href="%s" target="_blank">view</a>' % self.view_on_site(arg)

    display_view.allow_tags = True

    def manufacturer_edit(self, arg):
        return '<a href="%s">%s</a>' % (
            reverse('admin:shop_manufacturer_change', args=(arg.manufacturer_id,)), arg.manufacturer.name)

    manufacturer_edit.allow_tags = True
    manufacturer_edit.short_description = _('manufacturer')

    def category_edit(self, arg):
        return '<a href="%s">%s</a>' % (
            reverse('admin:shop_category_change', args=(arg.category_id,)), arg.category.name)

    category_edit.allow_tags = True
    category_edit.short_description = _('category')

    @staticmethod
    def view_on_site(obj):
        return reverse('shop_product', args=[slugify(obj.category.name), slugify(obj.name), obj.id])

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = {'attr_url': reverse('admin:shop_productattributechoice_getform'), 'attr_model_id': object_id}
        return super(ProductAdmin, self).change_view(request, object_id, form_url, extra_context)

    def add_view(self, request, form_url='', extra_context=None):
        extra_context = {'attr_url': reverse('admin:shop_productattributechoice_getform'), 'attr_model_id': ''}
        return super(ProductAdmin, self).add_view(request, form_url, extra_context)


class ProductAttributeChoiceAdmin(ModelAdmin):
    def get_urls(self):
        urls = super(ProductAttributeChoiceAdmin, self).get_urls()
        my_urls = patterns('', url(r'^getform/?([0-9]+)?/?([0-9]+)?/?$',
                                   self.admin_site.admin_view(self.get_product_attr_form),
                                   name="shop_productattributechoice_getform")
        )
        return my_urls + urls

    def get_product_attr_form(self, request, category_id, product_id):
        class AttributeForm(forms.Form):
            def __init__(self, fields, *args, **kwargs):
                super(AttributeForm, self).__init__(*args, **kwargs)
                for key, choices in fields.items():
                    self.fields[key] = forms.ChoiceField(choices=choices)

        choice_list = ProductAttributeChoice.objects.filter(attribute__category=category_id)

        attributes = {}
        for c in choice_list:
            if c.attribute.name not in attributes:
                attributes[c.attribute.name] = []
            attributes[c.attribute.name].append((c.choice, c.choice))

        return render_to_response('admin/product/attribute_form.html', {"form": AttributeForm(attributes)})


class CategoryInline(TabularInline):
    model = ProductAttribute


class CategoryAdminForm(ModelForm):
    model = Category

    class Meta:
        widgets = {
            'parent_': TreeSelect(add_link=('shop', 'category'))
        }


class MainCategoryFilter(admin.SimpleListFilter):
    title = _('parent category')
    parameter_name = 'main_cat'

    def lookups(self, request, model_admin):
        model = model_admin.model
        param = request.GET.get(self.parameter_name, None)
        if param is None:
            main_objects = model.objects.filter(level=0)
        else:
            main_objects = model.objects.filter(parent=param)
        arr = []
        for obj in main_objects:
            arr.append((obj.id, obj))

        return arr

    def queryset(self, request, queryset):
        if self.value() is not None:
            children = queryset.model.objects.get(pk=self.value()).get_descendants()
            return children & queryset


class CategoryAdmin(TreeEditor):
    list_filter = ()
    form = CategoryAdminForm
    prepopulated_fields = {'slug': ('name',), }
    list_filter = (MainCategoryFilter,)
    inlines = [
        CategoryInline,
    ]


    def get_urls(self):
        urls = super(CategoryAdmin, self).get_urls()
        my_urls = patterns('', url(r'^fetch/?$', self.admin_site.admin_view(self.fetch),
                                   name="%s_%s_fetch" % (self.model._meta.app_label, self.model._meta.model_name)))
        return my_urls + urls

    def fetch(self, request):
        if "parent" not in request.GET:
            return HttpResponseServerError("this endpoint needs parent GET parameter")

        categories = self.model.objects.filter(parent=request.GET['parent'])
        return HttpResponse(json.dumps([{'name': o.name, 'id': o.id} for o in categories]),
                            content_type='application/json')

    def _actions_column(self, page):
        preview_url = "../../r/%s/%s/" % ( ContentType.objects.get_for_model(self.model).id, page.id)
        actions = super(CategoryAdmin, self)._actions_column(page)
        actions.insert(0,
                       u'<a href="add/?parent=%s" title="%s"><img src="%sfeincms/img/icon_addlink.gif" alt="%s"></a>' % (
                           page.pk, _('Add child page'), settings.STATIC_URL, _('Add child page')))
        actions.insert(0, u'<a href="%s" title="%s"><img src="%sfeincms/img/selector-search.gif" alt="%s" /></a>' % (
            preview_url, _('View on site'), settings.STATIC_URL, _('View on site')))
        return actions

    def save_model(self, request, obj, form, change):
        if not change and hasattr(obj.parent, 'get_ancestors'):
            obj.slug = "-".join(
                list(map(lambda x: x.slug, obj.parent.get_ancestors(include_self=True)))) + "-" + obj.slug
        super(CategoryAdmin, self).save_model(request, obj, form, change)


    def get_form(self, request, obj=None, **kwargs):
        form = super(CategoryAdmin, self).get_form(request, obj, **kwargs)
        if "parent" in form.base_fields:
            form.base_fields['parent'].widget.can_add_related = False
        return form

    def __unicode__(self):
        return self.name


class CurrencyAdmin(ModelAdmin):
    search_fields = ('title', 'code')
    list_display = ('title', 'code', 'value')


class CityAdmin(ModelAdmin):
    search_fields = ('name', 'country__name',)
    list_filter = ('country',)
    list_display = ('name', 'country')


class CountryAdmin(ModelAdmin):
    search_fields = ('name', 'iso_code',)
    list_display = ('name', 'iso_code')


class ManufacturerAdmin(ModelAdmin):
    search_fields = ('name',)
    list_display = ('name', 'image_thumbnail')

    def image_thumbnail(self, obj):
        if obj.image and obj.image.filetype == "Image":
            return '<img src="%s" />' % path_to_url(version_generator(url_to_path(unicode(obj.image)), ADMIN_THUMBNAIL))
        else:
            return ""

    image_thumbnail.allow_tags = True
    image_thumbnail.short_description = "Thumbnail"


class SynonymForm(ModelForm):
    model = Synonym

    class Meta:
        widgets = {
            'from_text': forms.TextInput()
        }


class SynonymAdmin(ModelAdmin):
    form = SynonymForm


class ConfigAdmin(ModelAdmin):
    pass


admin.site.register(Product, ProductAdmin)
admin.site.register(City, CityAdmin)
admin.site.register(Country, CountryAdmin)
admin.site.register(Language, SortableModelAdmin)
admin.site.register(ProductPage)
admin.site.register(Manufacturer, ManufacturerAdmin)
admin.site.register(ProductTag, ProductTagAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(ProductAttribute)
admin.site.register(Config, ConfigAdmin)
admin.site.register(Synonym, SynonymAdmin)
admin.site.register(ProductAttributeChoice, ProductAttributeChoiceAdmin)


@register_menu_item
def menu_items():
    shop = items.ModelList(
        title=_('Shop'),
        url=reverse_lazy('admin:app_list', kwargs={'app_label': 'shop'}),
        models=('shop.models.Product', 'shop.models.Category', 'shop.models.Manufacturer', 'shop.models.Currency', )
    )
    shipment = items.ModelList(
        title=_('Shipment'),
        url=reverse_lazy('admin:app_list', kwargs={'app_label': 'shipment'}),
        models=('shop.shipment.*', ),
    )
    payment = items.ModelList(
        title=_('Payment'),
        url=reverse_lazy('admin:app_list', kwargs={'app_label': 'payment'}),
        models=('shop.payment.*', ),
    )
    shop.children.append(shipment)
    shop.children.append(payment)
    return shop


@register_menu_item
def menu_items():
    shop = items.ModelList(
        title=_('CMS'),
        url=reverse_lazy('admin:app_list', kwargs={'app_label': 'simit'}),
        models=('simit.models.Page', 'simit.models.Menu')
    )
    return shop


@register_last_menu_item
def setting_menu():
    return items.MenuItem(_('Settings'), reverse_lazy('admin:simit_customarea_settings'))