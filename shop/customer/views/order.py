# -*- coding: utf-8 -*-
import json
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import SuspiciousOperation
from django.core.urlresolvers import reverse, reverse_lazy
from django.db import IntegrityError
from django.db.models import F, Q
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext, Template, Context
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from shop.customer.forms import RegisterForm
from shop.customer.models import CustomerBasket, CustomerAddress, Order, OrderProduct
from shop.helpers import get_custom_variable
from shop.middleware import BasketExceptionMiddleware
from shop.models import Config
from shop.newsletter.models import Mail
from shop.payment.est.actions import ProcessOrder
from shop.payment.est.forms import PaymentInformation
from shop.payment.models import PaymentPackage
from shop.shipment.models import ShipmentAlternative
from shop.utils.mail import send_html_mail
from shop.utils.request import get_client_ip, secure_required_cloudflare, required_parameters, optional_parameters
from vehicle import query
from vehicle.models import VehicleBrand


LOGIN_URL = reverse_lazy('shop_customer_login')

logger = logging.getLogger(__name__)


@login_required(login_url=LOGIN_URL)
@required_parameters(GET={'action': unicode})
@optional_parameters(GET={'quantity': int})
def basket_action(request):
    action = request.GET.get('action')
    quantity = request.GET.get('quantity')
    sase = request.GET.get('sase')
    product = request.GET.get('product')
    if action == "add" and int(quantity) > 0:
        item = CustomerBasket(customer=request.user, quantity=quantity,
                              product_id=product, sase_code=sase)
        try:
            item.save()
        except IntegrityError:
            item = CustomerBasket.objects.get(customer=request.user, product_id=product)
            item.quantity = F('quantity') + quantity
            item.sase_code = sase
            item.save()
    elif action == "remove" or (action == "change-quantity" and int(quantity) == 0):
        item = CustomerBasket.objects.filter(customer=request.user, product_id=product)
        item.delete()
    elif action == "change-quantity":
        item = get_object_or_404(CustomerBasket, customer=request.user, product_id=product)
        item.quantity = quantity
        try:
            item.save()
        except:
            pass
    elif action == "add-sase-code":
        item = get_object_or_404(CustomerBasket, customer=request.user, product_id=product)
        item.sase_code = sase
        item.save()
    else:
        raise Http404("The page couldn't found")

    if request.is_ajax():
        return HttpResponse(json.dumps({"status": 200}), content_type="application/json")
    else:
        return HttpResponseRedirect(reverse('shop_customer_basket_page'))


def basket_page(request):
    if request.user.is_authenticated():
        ct = query.get_basket(customer=request.user, fail_silently=True)
        for e in ct['errors']:
            BasketExceptionMiddleware.process_exception(request, e)
    else:
        try:
            items = json.loads(request.COOKIES.get('basket-items'))
            ct = query.get_basket(items=items)
        except TypeError:
            ct = {}

    if request.is_ajax() and request.method == 'POST':
        return render_to_response(('shop/' + settings.SHOP_TEMPLATE + '/customer/ajax/basket.html', 'shop/default/customer/ajax/basket.html'), ct, context_instance=RequestContext(request))
    else:
        ct['levels'] = [VehicleBrand.objects.all()]
        return render_to_response(('shop/' + settings.SHOP_TEMPLATE + '/customer/order/basket.html', 'shop/default/customer/order/basket.html'), ct, context_instance=RequestContext(request))


@secure_required_cloudflare
@login_required(login_url=LOGIN_URL)
def order_address(request):
    ct = {}
    basket = query.get_basket(customer=request.user)
    if len(basket['basket']) == 0:
        return redirect("shop_customer_basket_page")
    ct['addresses'] = addresses = CustomerAddress.objects.filter(customer=request.user)
    if addresses.count() == 0:
        messages.add_message(request, messages.INFO, "Lütfen devam etmek için bir adres girin")
        return HttpResponseRedirect(reverse("shop_customer_address_add") + "?redirect_order")
    if request.method == 'POST':
        if request.POST.get('shipment') is None or request.POST.get('invoice') is None:
            messages.add_message(request, messages.ERROR, "Lütfen teslimat ve fatura adresini girin")
        else:
            request.session['orderAddress'] = {'shipment': request.POST.get('shipment'),
                                               'invoice': request.POST.get('invoice')}
            return HttpResponseRedirect(reverse("shop_order_shipment"))
    if 'orderAddress' in request.session:
        ct['selected_shipment'] = long(request.session['orderAddress']['shipment'])
        ct['selected_invoice'] = long(request.session['orderAddress']['invoice'])
    else:
        ct['selected_shipment'] = request.user.default_shipment_address_id
        ct['selected_invoice'] = request.user.default_invoice_address_id
    return render_to_response(('shop/' + settings.SHOP_TEMPLATE + '/customer/order/address.html', 'shop/default/customer/order/address.html'), ct, context_instance=RequestContext(request))


@secure_required_cloudflare
@login_required(login_url=LOGIN_URL)
def order_shipment(request):
    ct = {}
    basket = query.get_basket(request.user)
    ct['shipments'] = shipments = ShipmentAlternative.objects.filter(
        Q(minimum_price__lte=basket.get('total_basket')) | Q(minimum_price__isnull=True))
    if request.method == 'POST':
        if request.POST.get('shipment_alternative') is None:
            messages.add_message(request, messages.ERROR,
                                 'Lütfen devam etmek için postalama alternatiflerinden birini seçiniz.')
        else:
            request.session['orderShipment'] = request.POST.get('shipment_alternative')
            return HttpResponseRedirect(reverse("shop_order_payment"))

    if 'orderShipment' in request.session:
        ct['shipment_alternative'] = long(request.session['orderShipment'])

    if len(basket['basket']) == 0:
        return redirect("shop_customer_basket_page")
    # pointless models, another workaround.
    # most probably i'll forget what this shit does so this is the explanation:
    # it does NOTHING. the only point of ShipmentAlternative is to determine
    # whether the use can take advantage of free cargo alternative or not.
    # if at least one of the cargo price of the products in the basket exceeds the fixed price,
    # than the shipment price is the maximum cargo price of the basket.
    for i in shipments:
        i.price = query.calculate_cargo_price(i, basket)

    if shipments.count() == 0:
        ct['shipments'] = shipment_alternative = ShipmentAlternative.objects.filter(pk=1)
        for i in shipment_alternative:
            max_cargo_price = 0
            for item in basket['basket']:
                if item['product'].cargo_price > max_cargo_price:
                    max_cargo_price = item['product'].cargo_price
            i.price = max_cargo_price

    return render_to_response(('shop/' + settings.SHOP_TEMPLATE + '/customer/order/shipment.html', 'shop/default/customer/order/shipment.html'), ct, context_instance=RequestContext(request))

@csrf_exempt
@secure_required_cloudflare
@login_required(login_url=LOGIN_URL)
def order_payment(request):
    basket = query.get_basket(customer=request.user)
    ct = {"basket": basket}

    address_ids = request.session.get('orderAddress')
    shipment_id = request.session.get('orderShipment')

    def after_success(_order, _message):
        del request.session['orderAddress']
        del request.session['orderShipment']
        CustomerBasket.objects.filter(customer=request.user).delete()
        messages.add_message(request, messages.SUCCESS, _message)
        mail = Mail.objects.get(slug="new_order")

        title = Template(mail.title).render(Context({"order": _order}))
        content = Template(mail.content).render(Context({"order": _order}))
        send_html_mail(title, content, [request.user.email], fail_silently=True)

        mail = get_custom_variable("NOTIFICATION_EMAIL")
        if not settings.DEBUG and mail:
            send_html_mail(u'Yeni Sipariş: %s' % _order.receipt_id,
                           u'Sisteme yeni sipariş düştü. Sipariş no: %s' % _order.receipt_id, [mail],
                           fail_silently=True)

        return HttpResponseRedirect(reverse("shop_customer_order", args=(_order.receipt_id,)))

    if address_ids is None:
        return redirect('shop_order_address')
    if shipment_id is None:
        return redirect('shop_order_shipment')

    shipment = ShipmentAlternative.objects.get(pk=shipment_id)

    ct['shipment_price'] = query.calculate_cargo_price(shipment, ct['basket'])
    ct['price'] = ct['shipment_price'] + ct['basket']['total_basket']

    ct["3d_javascript_template"] = "shop/default/customer/order/3d_est.html"

    if request.method == 'POST':
        payment_type = request.POST.get("payment_type")
        if payment_type is None:
            return redirect('shop_customer_basket_page')

        payment = ProcessOrder(request.user, query.get_basket(request.user), shipment, address_ids,
                               PaymentPackage.objects.get(pk=Config.objects.conf("ACTIVE_PAYMENTPACKAGE")),
                               ip=get_client_ip(request))

        if payment_type == 'credit_card':
            ct['form'] = form = PaymentInformation(request.POST)
            if form.is_valid():
                order, message = payment.pay(form.cleaned_data)
                if order:
                    return after_success(order, message)
                else:
                    ct['form'] = form
                    ct['error_message'] = message
            else:
                ct['form'] = form
        elif payment_type == 'money_order':
            order, message = payment.pay({'payment_type': payment_type})
            if order:
                return after_success(order, message)
            else:
                ct['error_message'] = message
        elif payment_type == '3d_pay':
            try:
                result, order_id, message = payment.verify_and_process_3d(request)
                if result:
                    after_success(order_id, message)
                else:
                    ct['error_message'] = message
            except SuspiciousOperation, e:
                return HttpResponseRedirect(reverse("shop_customer_basket_page"))
    else:
        ct['form'] = RegisterForm()

    min_payment = get_custom_variable("MINIMUM_PAYMENT_AMOUNT")
    if min_payment.isdigit() and not settings.DEBUG and ct['basket']['final_price'] < float(min_payment):
        raise SuspiciousOperation("Sepetteki ürünlerin fiyatının toplamı %d lirayı aşmıyor." % min_payment)

    ct['methods'], ct['alternatives'] = query.get_active_payment_alternatives()

    return render_to_response(('shop/' + settings.SHOP_TEMPLATE + '/customer/order/payment.html', 'shop/default/customer/order/payment.html'), ct, context_instance=RequestContext(request))

@secure_required_cloudflare
@login_required(login_url=LOGIN_URL)
def order_page(request, order_id):
    order = get_object_or_404(Order, receipt_id=order_id, customer=request.user)
    products = OrderProduct.objects.filter(order=order)
    return render_to_response(('shop/' + settings.SHOP_TEMPLATE + '/customer/order/order_success.html', 'shop/default/customer/order/order_success.html'), locals(),
                              context_instance=RequestContext(request))