# -*- coding: utf-8 -*-
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from shop.utils.exception import BasketItemInsufficientStock, BasketItemNotExist


class BasketExceptionMiddleware(object):
    @staticmethod
    def process_exception(request, exception):
        if isinstance(exception, BasketItemNotExist):
            message = u"Sepetinizdeki %s ürünü mağazamızdan kalkmıştır." % exception.product.name
            if message not in messages.get_messages(request):
                messages.add_message(request, messages.ERROR, message)
            request.user.customerbasket_set.filter(product=exception.product).delete()
            if request.resolver_match.url_name != "shop_customer_basket_page":
                return HttpResponseRedirect(reverse("shop_customer_basket_page"))
        if isinstance(exception, BasketItemInsufficientStock):
            if exception.product.quantity > 0:
                message = u"Sepetinizdeki <a href='%s'>%s</a> ürününün miktarı stoklarımızdaki sayıdan fazladır. Maksimum sipariş edebileceğiz miktar: %s" % (exception.product.get_absolute_url(), exception.product.name, exception.product.quantity)
                if message not in messages.get_messages(request):
                    messages.add_message(request, messages.ERROR, message)
            else:
                message = u"Sepetinizdeki <a href='%s'>%s</a> ürünü stoklarımızda tükenmiştir." % (exception.product.get_absolute_url(), exception.product.name)
                if message not in messages.get_messages(request):
                    messages.add_message(request, messages.ERROR, message)
            if request.resolver_match.url_name != "shop_customer_basket_page":
                return HttpResponseRedirect(reverse("shop_customer_basket_page"))
