__author__ = 'buremba'
from django.views.generic import TemplateView

from django.conf.urls import patterns, url, include

urlpatterns = patterns('',
                       url(r'^$', 'shop.views.homepage', name="shop_homepage"),
                       url(r'^list/?$', 'shop.views.search_page', name="shop_list_page"),
                       url(r'^account/', include('shop.customer.urls')),
                       url(r'^p/(.+)$', 'shop.views.page', name="shop_page"),
                       url(r'^t/(.+)$', 'shop.views.tag_page', name="shop_tag_page"),
                       url(r'^c/(.+)$', 'shop.views.category', name="shop_category_page"),
                       url(
                           r'^v/(?P<vehicle_tree>[a-zA-Z0-9_-]+)/?(?:/(?P<motor>[a-zA-Z0-9_-]+))?(?:/(?P<fuel>[a-zA-Z0-9_-]+))?$',
                           'shop.views.vehicle_page', name="shop_vehicle_page"),
                       url(r'(.+)/(.+)-([0-9]+)$', 'shop.views.product_page', name="shop_product"),
                       url(r'^payment/', include('shop.payment.urls')),
                       url(r'^api/', include('shop.api.urls')),
                       url(r'^kullanim-sozlesmesi$', 'shop.views.tos_page', name="shop_page_tos"),
                       url(r'^hakkimizda$', 'shop.views.about_us', name="shop_page_about_us"),
                       url(r'^iletisim', 'shop.views.contact_us', name="shop_page_contact_us"),
                       url(r'^anlasmali-sirketler', 'shop.views.affiliates', name="shop_page_affiliates"),
                       url(r'^module/pricedropalert/', include('shop.modules.pricedropalert.urls')),
                       url(r'^module/stockalert/', include('shop.modules.stockalert.urls')),
                       url(r'^ajax/main_menu/$', 'shop.views.main_menu_ajax', name='shop_ajax_main_menu'),
                       url(r'^module/messaging/', include('shop.modules.messaging.urls')),
                       url(r'^robots.txt$', TemplateView.as_view(template_name="shop/robots.txt", content_type= 'text/plain')),
)


def register(_url):
    urlpatterns.append(_url)
