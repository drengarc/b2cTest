# -*- coding: utf-8 -*-
import base64
import hashlib
import json
import random
import string
from decimal import Decimal

from django.core.exceptions import ObjectDoesNotExist, SuspiciousOperation
from django.core.urlresolvers import reverse
from django.forms import model_to_dict
from django.http import HttpResponse

from shop.helpers import get_custom_variable
from shop.payment.est import deniz_bank
from shop.payment.est.actions import random_order_id, get_est_account, get_installments_for_order
from shop.shipment.models import ShipmentAlternative
from shop.utils.conversion import DecimalEncoder
from shop.utils.request import get_client_ip, required_parameters, secure_required_cloudflare
from shop.payment.est.models import Bank, Transaction
from vehicle import query


@secure_required_cloudflare
@required_parameters(POST={'bin': int})
def check_bin(request):
    basket = query.get_basket(request.user)

    try:
        bank = Bank.objects.get(creditcardtype__bin=request.POST.get('bin'))
        bank_dict = model_to_dict(bank, fields=['id', 'name', 'image'])
        if bank_dict.get('image'):
            bank_dict["image"] = bank_dict["image"].url_full
    except ObjectDoesNotExist:
        bank_dict = {}

    shipment_id = request.session.get('orderShipment')
    if shipment_id is None:
        return HttpResponse("0")

    shipment_price = query.calculate_cargo_price(ShipmentAlternative.objects.get(pk=shipment_id), basket)
    installments = list(get_installments_for_order(request.POST.get('bin'), basket).values())

    for installment in installments:
        if installment['discount_percentage'] is not None:
            final_price = basket["final_price"] * Decimal((100 - installment['discount_percentage']) / 100)
        elif installment['discount_amount'] is not None:
            final_price = (basket["final_price"] - installment['discount_amount']).min(0)
        else:
            final_price = basket["final_price"]
        installment['price'] = final_price + shipment_price

    if len(installments) == 0:
        installments = {"installments": {"installment": 1, "price": basket["final_price"] + shipment_price}}

    return HttpResponse(
        json.dumps({'installments': installments, 'bank': bank_dict},
                   cls=DecimalEncoder),
        content_type="application/json")


@required_parameters(POST={'installment': int, 'credit_card': string, 'expire': string, "cvv": int})
@secure_required_cloudflare
def action_3d(request):
    installment = int(request.POST.get("installment"))
    bin_number = request.POST.get("credit_card")[:6]
    basket = query.get_basket(request.user)
    order_id = random_order_id()

    shipment_id = request.session['orderShipment']

    if shipment_id is None:
        return HttpResponse("0")

    shipment = ShipmentAlternative.objects.get(pk=shipment_id)
    if shipment.minimum_price is not None and basket.get("total_price") < shipment.minimum_price:
        return HttpResponse("0")

    est = get_est_account(bin_number, installment, basket)

    Transaction(ip=get_client_ip(request), order_id=order_id, customer=request.user, type=2,
                amount=basket['final_price'], est=est).save()

    rnd = "".join([random.choice(string.letters + string.digits) for _ in range(20)])

    request.session["est_3d:%s" % (request.user.id, )] = order_id

    # okUrl = request.build_absolute_uri(reverse('shop_customer_order', args=(order_id,)))
    okUrl = failUrl = request.build_absolute_uri(reverse('shop_order_payment'))
    islemtipi = 'Auth'
    taksit = str(installment)
    price = query.calculate_cargo_price(shipment, basket) + basket['total_basket']
    hash = base64.b64encode(hashlib.sha1(est.client_id + order_id + str(
        price) + okUrl + failUrl + islemtipi + taksit + rnd + est.secret_key).hexdigest().decode('hex'))

    if est.gateway == 'est':
        return HttpResponse(json.dumps({
            "submit_url": "https://" + est.bank_url('SubmitPost3D'),
            "parameters": {
                "oid": order_id,
                "clientid": est.client_id,
                "okUrl": okUrl,
                "failUrl": failUrl,
                "islemtipi": islemtipi,
                "cardType": deniz_bank.credit_card_type(request.POST.get("credit_card")),
                "amount": str(price),
                "taksit": taksit,
                "hash": hash,
                "currency": 949,
                "storetype": "3d_pay",
                "firmaadi": get_custom_variable("EST_COMPANY_NAME"),
                "rnd": rnd,
                "pan": request.POST.get("credit_card"),
                "cv2": request.POST.get("cvv"),
                "Ecom_Payment_Card_ExpDate_Year": request.POST.get("expire").split("/")[1],
                "Ecom_Payment_Card_ExpDate_Month": request.POST.get("expire").split("/")[0]
            }
        }), content_type="application/json")
    elif est.gateway == 'denizbank':
        txn_type = "Auth"
        hash_code = base64.b64encode(
            hashlib.sha1(est.client_id + order_id + str(price) + okUrl + failUrl + txn_type + str(
                taksit) + rnd + est.password).hexdigest().decode('hex'))

        return HttpResponse(json.dumps({
            "submit_url": "https://inter-vpos.com.tr/MPI/Default.aspx",
            "parameters": {
                "OkUrl": okUrl,
                "FailUrl": failUrl,
                "TxnType": txn_type,
                "PurchAmount": str(price),
                "InstallmentCount": taksit,
                "Hash": hash_code,
                "Currency": "949",
                "Rnd": rnd,
                "OrderId": order_id,
                "Lang": "tr",
                "SecureType": "3DPay",
                "ShopCode": est.client_id,
                "Pan": request.POST.get("credit_card"),
                "Cvv2": request.POST.get("cvv"),
                "Expiry": request.POST.get("expire")
            }
        }), content_type="application/json")
    else:
        raise SuspiciousOperation("gateway is invalid")