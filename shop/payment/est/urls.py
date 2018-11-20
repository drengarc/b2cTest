__author__ = 'buremba'

from django.conf.urls import patterns, url

urlpatterns = patterns('',
                       url(r'check$', 'shop.payment.est.views.check_bin', name="payment_est_check_bin"),
                       url(r'3d/action$', 'shop.payment.est.views.action_3d', name="payment_est_action_3d"),
)