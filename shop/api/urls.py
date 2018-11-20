__author__ = 'buremba'

from django.conf.urls import patterns, url

urlpatterns = patterns('',
                       url(r'^product/([0-9]+)/similar$', 'shop.api.views.product.similar', name="shop_api_product_similar"),
                       url(r'^product/([0-9]+)/vehicles', 'shop.api.views.product.vehicles', name="shop_api_product_vehicles"),
                       url(r'^product/([0-9]+)/information', 'shop.api.views.product.information', name="shop_api_product_information"),
                       url(r'^product/([0-9]+)/oem', 'shop.api.views.product.oem', name="shop_api_product_oem"),
                       url(r'^search/product_code', 'shop.api.views.product.search_product_code', name="shop_api_search_product_code"),
                       url(r'^search/manufacturer', 'shop.api.views.product.search_manufacturer', name="shop_api_search_manufacturer"),
                       url(r'^search/oem_code', 'shop.api.views.product.search_oem_code', name="shop_api_search_oem_code"),
                       url(r'^quicksearch', 'shop.api.views.product.product_quick_search', name="shop_api_quick_search"),
                       url(r'^search/product', 'shop.api.views.product.product_search', name="shop_api_search_product"),
                       url(r'^search/vehicle_tree', 'shop.api.views.product.search_vehicle_tree', name="shop_api_search_vehicle_tree"),
                       url(r'^search/category', 'shop.api.views.product.search_category', name="shop_api_search_vehicle_category"),
                       url(r'^city/?', 'shop.api.views.location.city', name="shop_api_city"),
                       url(r'^ilce/?', 'shop.api.views.location.ilce', name="shop_api_ilce"),
                       url(r'^category', 'shop.api.views.product.category_search', name="shop_api_product_category_search"),
                       url(r'^vehicle/tree', 'shop.api.views.vehicles.vehicle_path', name="shop_api_vehicle_tree"),
                       url(r'^vehicle/motor', 'shop.api.views.vehicles.motor_type', name="shop_api_vehicle_motor"),
                       url(r'^order/agreement', 'shop.api.views.order.satis_sozlesmesi', name="shop_api_order_satis_sozlesmesi"),
                       url(r'^vehicle/fuel', 'shop.api.views.vehicles.fuel_type', name="shop_api_vehicle_fuel"),
                       url(r'^vehicle/years', 'shop.api.views.vehicles.vehicle_years', name="shop_api_vehicle_years"),
                       url(r'^vehicle/product_support', 'shop.api.views.vehicles.product_supports_vehicle', name="shop_api_vehicle_product_support"),
)