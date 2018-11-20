from django.conf.urls import patterns, url

urlpatterns = patterns('',
                       url(r"([0-9]+)", 'shop.modules.messaging.views.display_message', name='shop_modules_messaging_display'),
                       url(r"^new$", 'shop.modules.messaging.views.new_message', name='shop_modules_messaging_new'),
                       url(r"^$", 'shop.modules.messaging.views.list_messages', name='shop_modules_messaging_list')
                       )