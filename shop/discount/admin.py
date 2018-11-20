import datetime
from django.contrib import admin
from django.utils import timezone
from admin_tools.admin import RichModelAdmin
from shop.discount.models import Discount
from django.utils.translation import ugettext_lazy as _


class DiscountStatusFilter(admin.SimpleListFilter):
    title = _('status')
    parameter_name = 'sent'

    def lookups(self, request, model_admin):
        return ('0', _('scheduled')), ('1', _('past'))

    def queryset(self, request, queryset):
        if self.value() is not None:
            if self.value() == '0':
                return queryset.filter(start_date__gte=timezone.now())
            elif self.value() == '1':
                return queryset.filter(end_date__lte=timezone.now())


class DiscountAdmin(RichModelAdmin):
    #raw_id_fields = ('product',)
    filter_horizontal = ('category', 'product_tag', 'customer_group')
    fieldsets = (
        (None, {'fields': ('name', ('start_date', 'end_date'), 'is_active')}),
        ('Discount', {'fields': ('percentage', 'amount')}),
        ('Section', {'fields': ('category', 'product_tag', 'customer_group')}),
    )
    date_range = ('start_date', 'end_date',)
    require_one_of = ('percentage', 'amount')
    list_filter = (DiscountStatusFilter,)
    list_display = ('name', 'working')
    search_fields = ('name',)

    def working(self, obj):
        return obj.is_active and obj.end_date > datetime.datetime.now().date() > obj.start_date
    working.boolean = True

    def upcoming(self, obj):
        return obj.start_date > timezone.now()

    def pas(self, obj):
        return obj.end_date < timezone.now()


# admin.site.register(Discount, DiscountAdmin)
