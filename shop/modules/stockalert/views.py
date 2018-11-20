import base64
import hashlib
import hmac
import json

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.http import HttpResponse
from django.shortcuts import redirect, render_to_response
from django.template import Context, RequestContext
from django.template.loader import get_template
from django.conf import settings
from django.core.validators import validate_email
from django.utils.translation import ugettext as _

from shop.customer.views.user import LOGIN_URL
from shop.models import Product
from shop.modules.stockalert.models import StockAlertCustomer
from shop.utils.mail import send_html_mail


def add(request):
    if request.user.is_authenticated() and request.method == 'POST' and request.POST.get('product'):
        try:
            product = Product.objects.get(pk=request.POST.get("product"))
        except ObjectDoesNotExist:
            return HttpResponse(json.dumps(_("Product does not exist.")), content_type="application/json")
        try:
            StockAlertCustomer(customer=request.user, product=product).save()
        except IntegrityError:
            return HttpResponse(json.dumps(_("The product is already in your following list.")),
                                content_type="application/json")

        return HttpResponse(json.dumps(_("Succesfully saved.")), content_type="application/json")
    elif not request.user.is_authenticated() and request.method == 'POST' and request.POST.get(
            'product') and request.POST.get('email'):
        try:
            validate_email(request.POST.get("email"))
            product = Product.objects.get(pk=request.POST.get('product'))
        except (ValidationError, ObjectDoesNotExist):
            return HttpResponse(json.dumps("System Error"), content_type="application/json")
        hash_str = hmac.new(settings.SECRET_KEY, request.POST.get("email") + request.POST.get("product"),
                            hashlib.sha256).hexdigest()
        h = base64.b64encode(
            json.dumps({"hash": hash_str, "email": request.POST.get("email"), "product": request.POST.get("product")}))
        content = get_template('shop/modules/stockalert/confirm_alert.html').render(
            Context({'hash': h, 'product': product}))
        try:
            send_html_mail(_('Price drop alert confirmation e-mail'), content, [request.POST.get("email")],
                           fail_silently=False)
        except:
            return HttpResponse("System Error:", content_type="application/json")

        return HttpResponse(json.dumps(_("Verification email is sent.")), content_type="application/json")

    return HttpResponse(json.dumps("Bad request"), content_type="application/json", status=400)


@login_required(login_url=LOGIN_URL)
def list_followings(request):
    followings = Product.objects.filter(stock_customer__customer=request.user)
    return render_to_response('shop/modules/stockalert/list_followings.html', locals(),
                              context_instance=RequestContext(request))


@login_required(login_url=LOGIN_URL)
def remove(request):
    try:
        StockAlertCustomer.objects.get(customer=request.user, product=request.POST.get("product")).delete()
    except Exception:
        if request.is_ajax():
            return HttpResponse("The item is already in your following list")

    if request.is_ajax():
        return HttpResponse("Successfully removed")
    else:
        return redirect("shop_modules_stockalert_list")