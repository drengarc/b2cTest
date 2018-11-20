import logging

from django.contrib import messages
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse, reverse_lazy
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.conf import settings

from shop.customer.forms import CustomerAddressForm, ProfileUpdateForm
from shop.customer.models import CustomerAddress, Order
from shop.utils.request import secure_required_cloudflare

LOGIN_URL = reverse_lazy('shop_customer_login')
logger = logging.getLogger(__name__)


@secure_required_cloudflare
@login_required(login_url=LOGIN_URL)
def orders(request):
    ct = {'_page': 'order', 'orders': Order.objects.filter(customer=request.user)}

    return render_to_response('shop/default/customer/account/orders.html', ct, context_instance=RequestContext(request))


@secure_required_cloudflare
@login_required(login_url=LOGIN_URL)
def profile(request):
    ct = {'_page': 'profile'}

    if request.method == 'POST':
        ct['form'] = form = ProfileUpdateForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            messages.add_message(request, messages.SUCCESS, _('Your profile successfully updated'))
    else:
        ct['form'] = ProfileUpdateForm(request.user)

    return render_to_response('shop/default/customer/account/profile.html', ct,
                              context_instance=RequestContext(request))


@secure_required_cloudflare
@login_required(login_url=LOGIN_URL)
def customer_address_modify(request, address_id=None):
    ct = {'_page': 'address'}
    if request.method == 'POST':
        if address_id is not None:
            q = Q(pk=address_id) if address_id is not None else Q()
            ct['form'] = form = CustomerAddressForm(request.POST,
                                                    instance=CustomerAddress.objects.get(Q(customer=request.user) & q))
        else:
            ct['form'] = form = CustomerAddressForm(request.POST, instance=CustomerAddress(customer=request.user))
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(
                reverse("shop_order_address") if request.GET.get("redirect_order") is not None else reverse(
                    "shop_customer_address"))
    else:
        if address_id is not None:
            ct['form'] = CustomerAddressForm(instance=CustomerAddress.objects.get(pk=address_id, customer=request.user))
        else:
            ct['form'] = CustomerAddressForm()

    return render_to_response('shop/default/customer/account/address_add.html', ct,
                              context_instance=RequestContext(request))


@secure_required_cloudflare
@login_required(login_url=LOGIN_URL)
def customer_address(request):
    ct = {'_page': 'address'}
    if request.method == 'POST':
        try:
            customer = request.user
            customer.default_invoice_address = CustomerAddress.objects.get(pk=request.POST.get("invoice"),
                                                                           customer=request.user)
            customer.default_shipment_address = CustomerAddress.objects.get(pk=request.POST.get("shipment"),
                                                                            customer=request.user)
            customer.save()
            messages.add_message(request, messages.SUCCESS, 'The address successfully saved')
        except Exception as e:
            logger.exception(e)
            messages.add_message(request, messages.ERROR, 'An error occured while saving the address.')

    ct['addresses'] = CustomerAddress.objects.filter(customer=request.user)
    return render_to_response(
        ('shop/'+settings.SHOP_TEMPLATE+'/customer/account/address.htm', 'shop/default/customer/account/address.html'), ct,
        context_instance=RequestContext(request))

