from django.core.urlresolvers import reverse_lazy
from django.conf.urls import patterns, url
from shop.customer.forms import PasswordResetForm

urlpatterns = patterns('',
                       url(r'^addresses/?$', 'shop.customer.views.user.customer_address', name="shop_customer_address"),
                       url(r'^addresses/add/?$', 'shop.customer.views.user.customer_address_modify', name="shop_customer_address_add"),
                       url(r'^addresses/([0-9]+)$', 'shop.customer.views.user.customer_address_modify', name="shop_customer_address_edit"),
                       url(r'^orders/?$', 'shop.customer.views.user.orders', name="shop_customer_orders"),
                       url(r'^profile/?$', 'shop.customer.views.user.profile', name="shop_customer_profile"),
                       url(r'^basket-action/?$', 'shop.customer.views.order.basket_action', name="shop_customer_basket"),
                       url(r'^basket/?$', 'shop.customer.views.order.basket_page', name="shop_customer_basket_page"),
                       url(r'^order/shipment$', 'shop.customer.views.order.order_shipment', name="shop_order_shipment"),
                       url(r'^order/address', 'shop.customer.views.order.order_address', name="shop_order_address"),
                       url(r'^order/payment', 'shop.customer.views.order.order_payment', name="shop_order_payment"),
                       url(r'^order/([0-9A-Za-z]+)', 'shop.customer.views.order.order_page', name="shop_customer_order"),
                       url(r'^logout/?$', 'shop.customer.views.membership.logout', name="shop_customer_logout"),
                       url(r'^login/?$', 'shop.customer.views.membership.login', name="shop_customer_login"),
                       url(r'^register/?$', 'shop.customer.views.membership.register', name="shop_customer_register"),
                       url(r'^password/reset/?$', 'shop.customer.views.membership.password_reset', {'password_reset_form': PasswordResetForm, 'post_reset_redirect': reverse_lazy('customer_password_reset_done'), 'template_name': 'customer/registration/password_reset_form.html'}, name="password_reset"),
                       url(r'^password/reset/done/?$', 'django.contrib.auth.views.password_reset_done', {'template_name': 'customer/registration/password_reset_done.html'}, name="customer_password_reset_done"),
                       url(r'^password/reset/(?P<uidb64>[0-9A-Za-z]+)/(?P<token>.+)/?$', 'shop.customer.views.membership.password_reset_confirm', {'template_name': 'customer/registration/password_reset_confirm.html', 'post_reset_redirect': reverse_lazy('customer_password_reset_complete')}, name="password_reset_confirm"),
                       url(r'^password/reset/complete/?$', 'django.contrib.auth.views.password_reset_complete', {'template_name': 'customer/registration/password_reset_complete.html'}, name="customer_password_reset_complete")
)