from django.contrib import admin

from shop.shipment.models import ShipmentMethod, ShipmentAlternative


admin.site.register(ShipmentMethod)
admin.site.register(ShipmentAlternative)