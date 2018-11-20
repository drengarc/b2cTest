from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.template import Library
from shop.modules.stockalert.models import StockAlertCustomer

register = Library()


@register.filter
def is_following_product(product, user):
    if isinstance(user, get_user_model()):
        try:
            StockAlertCustomer.objects.get(customer=user, product_id=product['id'])
        except ObjectDoesNotExist:
            return False
        return True
    else:
        return False

