__author__ = 'buremba'

from django.conf.urls import patterns, url, include

urlpatterns = patterns('',
                       url(r'^est/', include('shop.payment.est.urls')),
)
