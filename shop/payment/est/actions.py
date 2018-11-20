#!/usr/bin/env python
# -*- coding: utf-8 -*-
import base64
import hashlib
import logging
import random
import string
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ImproperlyConfigured, SuspiciousOperation
from django.db.models import Q
from django.views.decorators.debug import sensitive_variables
from django.utils.translation import ugettext as _
from shop.models import Config

from shop.payment.est import deniz_bank
from shop.payment.est import yapi_kredi
from shop.payment.est import vakifbank
from vehicle import query
from shop.payment.est.est import EST
from shop.payment.est.models import InstallmentAlternative
from settings import DEBUG
from shop.customer.models import Order, CustomerAddress, OrderProduct, OrderStatus, ORDER_STATUS_CHOICES, CustomerBasket
from shop.helpers import get_custom_variable
from shop.payment.est.models import Transaction, CreditCardESTRelation, ESTCredential,CreditCardType
from shop.utils.request import get_client_ip


logger = logging.getLogger(__name__)


def random_order_id():
    return "".join([random.choice(string.letters + string.digits) for _ in range(12)])


def get_est_account(bin_number, installment, basket):
    try:
        est_rel = CreditCardType.objects.get(pk=bin_number)
        est_account = ESTCredential.objects.get(bank=est_rel.bank.name)
        #est_rel = CreditCardESTRelation.objects.get(bin=bin_number)
        #est_account = est_rel.est_cash if installment == 1 else est_rel.est_installment
    except ObjectDoesNotExist:
        try:
            est_account = ESTCredential.objects.get(pk=Config.objects.conf("DEFAULT_ESTPACKAGE"))
            # est_account = ESTCredential.objects.get(pk=23)
        except ObjectDoesNotExist:
            raise ImproperlyConfigured("The system is not configured yet")

    if settings.DEBUG:
        if est_account.gateway == 'est':
            user = est_account.bank_prop('test_user')
            est_account.client_id = user['company']
            est_account.username = user['username']
            est_account.password = user['password']
            est_account.secret_key = user['secret_key']
        elif est_account.gateway == 'denizbank':
            est_account.client_id = "12345"
            est_account.username = "vpos1"
            est_account.password = "1"
        elif est_account.gateway == 'vpos':
            est_account.client_id = "VP000302"
            est_account.username = "000000000011858"
            est_account.password = "ORSAN"
        elif est_account.gateway == 'yapi_kredi':
            est_account.client_id = "67000067"
            est_account.username = "6700000067"
            est_account.password = ""

    return est_account


def get_installments_for_order(bin_number, basket):
    try:
        return InstallmentAlternative.objects.filter(
            Q(bank__creditcardtype__bin=bin_number),
            Q(Q(maximum_price__isnull=True) | Q(maximum_price__gte=basket["final_price"])),
            Q(Q(minimum_price__isnull=True) | Q(minimum_price__lte=basket["final_price"]))).order_by('installment')
    except ObjectDoesNotExist:
        # default_pos = Config.objects.conf("DEFAULT_ESTPACKAGE")
        return None


class InvalidPaymentMethod(Exception):
    pass


class ProcessOrder:
    def __init__(self, user, basket, shipment, address, package, ip=None, debug=DEBUG):
        self.gateway = get_custom_variable("PAYMENT_GATEWAY")
        self.debug = debug
        self.user = user
        self.basket = basket
        self.shipment = shipment
        self.address = address
        self.package = package
        self.ip = ip

    @sensitive_variables('form')
    def pay(self, form_data, order_id=None):
        if order_id is None:
            order_id = random_order_id()

        order = Order(receipt_id=order_id)

        cargo_price = query.calculate_cargo_price(self.shipment, self.basket)
        order.final_kdv = self.basket['kdv']
        order.shipment_price = cargo_price
        order.shipment_alternative = self.shipment
        order.payment_alternative_id = 1
        order.customer = self.user

        if form_data.get('payment_type') == 'credit_card':

            discount = 0
            try:
                installment = get_installments_for_order(form_data.get("cc_number")[:6], self.basket) \
                    .get(installment=form_data.get('installment'))

                if installment.discount_percentage is not None:
                    discount = self.basket["final_price"] * Decimal(installment.discount_percentage / 100)
                elif installment.discount_amount is not None:
                    discount = installment.discount_amount
            except ObjectDoesNotExist:
                pass

            order.discount = self.basket['total_discount'] + discount
            order.final_price = price = self.basket['final_price'] + cargo_price - discount

            month, year = form_data.get('cc_exp')
            order.payment_type = 1

            est_account = get_est_account(form_data.get("cc_number")[:6], form_data.get('installment'), self.basket)

            if est_account.gateway == 'est':
                api = EST(est_account.bank, est_account.client_id, est_account.username, est_account.password,
                          debug=self.debug)
                succeed, response = api.pay(form_data.get('cc_number'), form_data.get('cc_cvv'), month.zfill(2), year,
                                            price,
                                            form_data.get('installment'), order_id)
            elif est_account.gateway == 'denizbank':
                api = deniz_bank.DenizBankPay(est_account.client_id, est_account.username, est_account.password,
                                              debug=self.debug)
                succeed, response = api.pay(form_data.get('cc_number'), form_data.get('cc_cvv'), month.zfill(2), year,
                                            price, order_id, deniz_bank.credit_card_type(form_data.get('cc_number')),
                                            InstallmentCount=form_data.get('installment'))
            elif est_account.gateway == 'yapi_kredi':
                api = yapi_kredi.YapiKrediPay(est_account.client_id, est_account.username, est_account.password,
                                              debug=self.debug)
                succeed, response = api.pay(form_data.get('cc_number'), form_data.get('cc_cvv'), month.zfill(2), year,
                                            price, order_id, deniz_bank.credit_card_type(form_data.get('cc_number')),
                                            InstallmentCount=form_data.get('installment'))
            elif est_account.gateway == 'vpos':
                api = vakifbank.Pay(est_account.client_id, est_account.username, est_account.password,
                                    debug=self.debug)
                succeed, response = api.pay(form_data.get('cc_number'), form_data.get('cc_cvv'), month.zfill(2), year,
                                            price, order_id, deniz_bank.credit_card_type(form_data.get('cc_number')),
                                            InstallmentCount=form_data.get('installment'))
            else:
                raise Exception("gateway is invalid")

            trans = Transaction(customer=self.user, order_id=order_id, type=1, ip=self.ip,
                                amount=order.final_price)
            if not succeed:
                trans.error_message = response
                trans.save()
                return False, response
            trans.save()

            order.cc_owner = form_data.get("cc_owner")
            order.cc_number_last = form_data.get("cc_number")[-4:]

        elif form_data.get('payment_type') == 'money_order':

            discount = 0
            order.discount = self.basket['total_discount'] + discount
            order.final_price = self.basket['final_price'] + cargo_price - discount

            order.payment_type = 2
        elif form_data.get('payment_type') == '3d_pay' and get_custom_variable("ACTIVATE_3D"):
            discount = 0
            order.discount = self.basket['total_discount'] + discount
            order.final_price = self.basket['final_price'] + cargo_price - discount

            order.payment_type = 3
        else:
            raise InvalidPaymentMethod("payment_type parameter is not valid.")

        ship_addr = CustomerAddress.objects.get(pk=self.address['shipment'])
        order.delivery_name = "%s %s" % (ship_addr.first_name, ship_addr.last_name)
        order.delivery_address = "%s \n %s / %s / %s %s" % (
            ship_addr.address, ship_addr.ilce, ship_addr.ilce.city, ship_addr.ilce.city.country,
            ship_addr.postcode)
        order.delivery_city = ship_addr.ilce.city
        order.delivery_phone = ship_addr.cell_phone if ship_addr.cell_phone is not None else ship_addr.phone

        bill_addr = CustomerAddress.objects.get(pk=self.address['invoice'])
        if bill_addr.id != ship_addr.id:
            order.billing_name = "%s %s" % (bill_addr.first_name, bill_addr.last_name)
            order.billing_address = "%s \n %s / %s / %s %s" % (
                bill_addr.address, bill_addr.ilce, bill_addr.ilce.city, bill_addr.ilce.city.country,
                bill_addr.postcode)
            order.billing_city = bill_addr.ilce.city
            order.billing_phone = bill_addr.cell_phone if bill_addr.cell_phone is not None else bill_addr.phone
            order.tax_authority = bill_addr.tax_authority
            order.tax_no = bill_addr.tax_no

        order.save()
        for item in self.basket['basket']:
            product = item['product']
            OrderProduct(order=order, product_id=item['product_id'], quantity=item['quantity'],
                         price=product['discount_price'], vehicle_toptanci_id=item['product'].toptanci_id,
                         discount=product['price'] - product['discount_price'], sase_code=item['sase_code']).save()
        OrderStatus(order=order, order_status_type_id=ORDER_STATUS_CHOICES[0][0]).save()

        CustomerBasket.objects.filter(customer=self.user).delete()

        return order, "%s %s" % (_("Your order is processed successfully!"), _("Order No: %s") % order_id)

    def verify_and_process_3d(self, request):
        reliable_var = request.session.get("est_3d:%s" % (request.user.id, ), False)
        if not reliable_var or reliable_var != request.POST.get("oid"):
            raise SuspiciousOperation(
                "Suspicious Operation. 3D Pay return method requested but it doesn't have session value.")

        hashparams = request.POST.get('HASHPARAMS')
        paramsval = ""
        for index2 in hashparams.split(":"):
            paramsval += request.POST.get(index2, "")

        est = get_est_account(request.POST.get("MaskedPan")[0:6], request.POST.get('taksit'), self.basket)

        hashval = paramsval + est.secret_key
        hash = base64.b64encode(hashlib.sha1(hashval).hexdigest().decode('hex'))

        approved = False
        if est.gateway == 'denizbank':
            if paramsval != request.POST.get("HASHPARAMSVAL") or request.POST.get('Hash') != hash:
                raise SuspiciousOperation("3d sayısal imza geçerli değil")
            Transaction(ip=get_client_ip(request), type=3, customer=request.user, order_id=request.POST.get("OrderId"),
                        amount=request.POST.get("amount"), error_message=request.POST.get("ErrorMessage")).save()
            approved = request.POST.get("TxnResult") == 'Success'
            error_message = request.POST.get("ErrorMessage")
        elif est.gateway == 'est':
            if paramsval != request.POST.get("HASHPARAMSVAL") or request.POST.get("HASH") != hash:
                raise SuspiciousOperation("3d sayısal imza geçerli değil")
            Transaction(ip=get_client_ip(request), type=3, customer=request.user, order_id=request.POST.get("oid"),
                        amount=request.POST.get("amount"), error_message=request.POST.get("ErrMsg")).save()
            approved = request.POST.get("Response") != 'Approved'
            error_message = request.POST.get("ErrMsg")
        else:
            raise SuspiciousOperation("undefined gateway")

        if not approved:
            return False, reliable_var, error_message
        else:
            order_id, message = self.pay(
                {'payment_type': request.POST.get("payment_type"), 'order_id': reliable_var})
            if order_id:
                return True, order_id, message
            else:
                return False, reliable_var, message