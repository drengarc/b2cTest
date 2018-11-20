from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.template import Library
from shop.modules.pricedropalert.models import PriceDropAlertCustomer, PriceDropAlertEmail

register = Library()


@register.filter
def is_following_price(product, user):
    if isinstance(user, get_user_model()):
        try:
            PriceDropAlertCustomer.objects.get(customer=user, product_id=product['id'])
        except ObjectDoesNotExist:
            return False
        return True
    else:
        try:
            PriceDropAlertEmail.objects.get(email=user, product_id=product['id'])
        except ObjectDoesNotExist:
            return False
        return True

