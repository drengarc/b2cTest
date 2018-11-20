# -*- coding: utf-8 -*-

import json

from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import Context, RequestContext
from django.template.loader import get_template

from shop import helpers
from shop.models import Category, Product
from shop.utils.request import required_parameters
from django.conf import settings
from shop.views import CATALOG_TYPES
from vehicle.ege_integration.tasks import fetch_oem_codes
import vehicle.query as Query
import re
from unidecode import unidecode


def vehicles(request, product):
    vehicle_list = Query.get_vehicle_tree_from_product(product)

    if request.META.get('CONTENT_TYPE') == 'application/json':
        return HttpResponse(json.dumps(vehicles), content_type="application/json")
    else:
        out = ["<table>"]
        for vehicle in vehicle_list:
            out.append(get_template('shop/default/includes/breadcrumb-table.html').render(
                Context({'items': vehicle, 'render_homepage': False, 'tag': 'link', 'request': request})))
        out.append("</table>")
        return HttpResponse("\n".join(out))


def similar(request, product):
    p = get_object_or_404(Product, id=product)

    products = Query.fetch_similar_products(request.user.id, p.id)

    if request.META.get('CONTENT_TYPE') == 'application/json':
        return HttpResponse(json.dumps(list(products)), content_type="application/json")
    else:
        template = request.POST.get('template', 'list')
        out = []
        for product in products:
            out.append(get_template('shop/%s/includes/catalog/%s.html' % (settings.SHOP_TEMPLATE, template)).render(
                Context({'product': product, 'property': 'vehicle', 'request': request, 'render_properties': False,
                         'render_manufacturer': True})))
        if len(products) == 0:
            out.append("Bu ürüne benzer bir ürün bulunamadı.")
        return HttpResponse("\n".join(out))


@required_parameters(GET={'offset': int, 'limit': int})
def product_search(request):
    tag_slug = request.GET.get('tag')
    p = {'offset': int(request.GET.get('offset')), 'limit': int(request.GET.get('limit')), 'tags_slug': tag_slug}
    if p['limit'] > 100:
        p['limit'] = 100
    elif p['limit'] < 1:
        p['limit'] = 1

    products = Query.get_products_by(request.user.group_id, **p)['products']

    if len(products) == 0:
        return HttpResponse(0)

    template = request.GET.get('template')
    if template is None or template not in CATALOG_TYPES.keys():
        template = CATALOG_TYPES['square']
    else:
        template = CATALOG_TYPES[template]

    out = []
    for idx, product in enumerate(products):
        out.append(get_template(template).render(Context({'product': product, 'counter': idx + 1})))

    return HttpResponse("\n".join(out))


def category_search(request):
    try:
        categories = Category.objects.filter(**request.GET.dict()).values('id', 'name')
    except:
        return HttpResponse(json.dumps({'status': 'An error occurred.'}), status=500)
    return HttpResponse(json.dumps(list(categories)), content_type="application/json")


def oem(request, product):
    p = get_object_or_404(Product, id=product)

    oem_codes = fetch_oem_codes(p.id)

    if request.META.get('CONTENT_TYPE') == 'application/json':
        return HttpResponse(json.dumps(list(oem_codes)), content_type="application/json")
    else:
        return render_to_response('shop/api/product_oem.html', {"oem_codes": oem_codes},
                                  context_instance=RequestContext(request))


def information(request, id):
    product = get_object_or_404(Product, pk=id)

    if request.META.get('CONTENT_TYPE') == 'application/json':
        return HttpResponse(json.dumps(product), content_type="application/json")

    return render_to_response('shop/api/product_information.html', {"product": product},
                              context_instance=RequestContext(request))


@required_parameters(GET={'term': unicode})
def search_product_code(request):
    cursor = helpers.Connection()
    term = re.sub(r'\W+', '', request.GET.get("term").lower())

    return HttpResponse(json.dumps(
        cursor.fetchall(
            "select partner_code from product where (regexp_replace(lower(partner_code), '[^0-9A-Za-z]+', '', 'g')) like %s limit 15",
            [term + "%"])), content_type="application/json")


@required_parameters(GET={'term': unicode})
def search_oem_code(request):
    cursor = helpers.Connection()
    term = unidecode(request.GET.get("term").replace('=', '==').replace('%', '=%').replace('_', '=_'))

    return HttpResponse(json.dumps(cursor.fetchall(
        "select oem_no from ege.tb_kart_stok_oem oem where lower(oem_no) like lower(%s) or lower(oem_no) like lower(%s) limit 15",
        [term + "%", term + "%"])), content_type="application/json")


@required_parameters(GET={'term': unicode})
def search_manufacturer(request):
    cursor = helpers.Connection()
    term = unidecode(request.GET.get("term").replace('=', '==').replace('%', '=%').replace('_', '=_'))

    return HttpResponse(json.dumps(
        cursor.fetchall("select name from manufacturer where lower(name) like lower(%s) limit 15", [term + "%"])),
                        content_type="application/json")


@required_parameters(GET={'term': unicode, 'level': int})
def search_vehicle_tree(request):
    cursor = helpers.Connection()
    term = unidecode(request.GET.get("term").replace('=', '==').replace('%', '=%').replace('_', '=_'))
    level = request.GET.get('level')

    return HttpResponse(json.dumps(
        cursor.fetchall(
            "select distinct name as name from vehicle_tree where level = %s and lower(name) like lower(%s) limit 15",
            [level, term + "%"])), content_type="application/json")


@required_parameters(GET={'term': unicode})
def search_category(request):
    cursor = helpers.Connection()
    term = unidecode(request.GET.get("term").replace('=', '==').replace('%', '=%').replace('_', '=_'))

    return HttpResponse(json.dumps(
        cursor.fetchall("select name from category where parent_id is null and lower(name) like lower(%s) limit 15",
                        [term + '%'])),
                        content_type="application/json")


@required_parameters(GET={'term': unicode})
def product_quick_search(request):
    query = request.GET.get('term')
    cursor = helpers.Connection()

    return HttpResponse(json.dumps(cursor.fetchall(
        "select suggestion, target from shop_quicksearchsuggestion where similarity(suggestion, %s)> 0.5 order by similarity(suggestion, %s) desc limit 7;",
        [query, query])))