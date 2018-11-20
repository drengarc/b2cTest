from django.contrib import admin
from django.contrib.admin import ModelAdmin
from shop.modules.stockalert.models import StockAlertCustomer


class StockAlertCustomerAdmin(ModelAdmin):
    list_filter = ('saved_time',)
    list_display = ('saved_time', 'product', 'customer')
    search_fields = ('customer', 'product',)

admin.site.register(StockAlertCustomer, StockAlertCustomerAdmin)