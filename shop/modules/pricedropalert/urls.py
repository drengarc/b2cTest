from django.conf.urls import patterns, url

urlpatterns = patterns('',
                       url(r"add", 'shop.modules.pricedropalert.views.add', name="shop_modules_pricedropalert_add"),
                       url(r"remove", 'shop.modules.pricedropalert.views.remove', name="shop_modules_pricedropalert_remove"),
                       url(r"list", 'shop.modules.pricedropalert.views.list_followings', name="shop_modules_pricedropalert_list"),
                       url(r"confirm/([0-9A-Za-z]+)", 'shop.modules.pricedropalert.views.confirm_page', name="shop_pricedropalert_confirm")
                       )