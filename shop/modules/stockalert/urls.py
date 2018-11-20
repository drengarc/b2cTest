from django.conf.urls import patterns, url

urlpatterns = patterns('',
                       url(r"add", 'shop.modules.stockalert.views.add', name="shop_modules_stockalert_add"),
                       url(r"remove", 'shop.modules.stockalert.views.remove', name="shop_modules_stockalert_remove"),
                       url(r"list", 'shop.modules.stockalert.views.list_followings', name="shop_modules_stockalert_list"),
                       )