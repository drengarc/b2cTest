from datetime import datetime
from django.core.exceptions import SuspiciousOperation
from django.http import HttpResponse
from django.template import Template, Context
from simit.models import Page
from shop.customer.models import CustomerAddress
from vehicle import query


def satis_sozlesmesi(request):
    basket = query.get_basket(customer=request.user)
    content = Page.objects.get(slug="satis-sozlesmesi_1")

    t = request.GET.get("payment_type")
    if t not in ['havale', 'kredi-karti']:
        raise SuspiciousOperation("?")

    invoice_addr = CustomerAddress.objects.get(customer=request.user, id=request.session.get('orderAddress')['invoice'])
    shipment_addr = CustomerAddress.objects.get(customer=request.user, id=request.session.get('orderAddress')['shipment'])
    ct = {
        "tarih": datetime.now(),
        "odeme_tip": t,
        "kullanici": request.user,
        "urunler": [{"isim": b['product'].name, "miktar": b["quantity"], "fiyat": b['total_price']} for b in
                  basket['basket']],
        "tutar": basket['final_price'],
        "teslim_adresi": shipment_addr,
        "fatura_adresi": invoice_addr,
    }

    return HttpResponse(Template(content.content).render(Context(ct)))