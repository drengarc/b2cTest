# -*- coding: utf-8 -*-
import json
import logging
import re

from django.core.exceptions import SuspiciousOperation
from django.http import Http404, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext, Context
from django.template.loader import get_template
from django.utils.text import slugify
from django.views.decorators.cache import cache_page
from simit.models import Page
from django.utils.translation import ugettext as _

from shop.banner.models import Banner
from shop.models import Category, ProductTag, Manufacturer
from shop.utils.cache import cache_func
from shop.utils.request import required_parameters, get_client_ip
from vehicle.ege_integration.tasks import fetch_oem_codes
from vehicle.models import VehicleTree, VehicleOther, VehicleBrand
from vehicle import query
from vehicle.query import get_vehicle_tree_from_product, fetch_similar_products
from django.conf import settings

logger = logging.getLogger(__name__)

CATALOG_TYPES = {'list': 'shop/%s/includes/catalog/list.html' % settings.SHOP_TEMPLATE,
                 'square': 'shop/%s/includes/catalog/square.html' % settings.SHOP_TEMPLATE,
                 'thumb_square': 'shop/%s/includes/catalog/thumb_square.html' % settings.SHOP_TEMPLATE}
PER_PAGE = (15, 100)
ORDER_BY = {
    "p": "discount_price",
    "n": "product.name",
    "pc": "product.partner_code",
    "bn": "manufacturer.name",
    "cn": "category.name",
}


def homepage(request):
    @cache_func(60)
    def homepage_variables():
        main_cats, sub_categories = query.get_category_not_related_vehicle()
        ct = {
            'vehicles': query.get_active_brands(),
            'categories': VehicleOther.objects.all().order_by('tree_id', 'lft'),
            'categories_not_related_vehicle': main_cats,
            'categories_not_related_vehicle_sub': sub_categories,
            'banners': Banner.objects.filter(area__name="ANASAYFA", is_active=True),
            'gunun_firsati': query.get_products_by(request.user.group_id,
                                                   tags_slug="gunun-urunu", limit=10, in_stock=True,
                                                   order_by=(('-', "image.image is not null"),))['products'],
            'indirimdekiler':
                query.get_products_by(request.user.group_id, tags_slug="kampanyali-urun",
                                      limit=16, in_stock=True,
                                      order_by=(('-', "image.image is not null"),))['products'],
            'yeni_urunler':
                query.get_products_by(request.user.group_id, tags_slug="yeni-urun",
                                      limit=16, in_stock=True,
                                      order_by=(('-', "image.image is not null"),))['products'],
            "ip": get_client_ip(request)
        }

        ct.update(search(request, request.GET))
        return ct

    return render_to_response('shop/%s/homepage.html' % settings.SHOP_TEMPLATE, homepage_variables(),
                              context_instance=RequestContext(request))


def category(request, slug):
    d = request.GET.dict()
    d['c'] = slug
    request.extraGET = {"c": slug}
    ct = search(request, d)
    if ct['category'] is None:
        raise Http404(_("The category couldn't found"))
    ct['page_title'] = u'%s Kategorisinde' % ct['category'].name
    return render_to_response('shop/%s/search.html' % settings.SHOP_TEMPLATE, ct,
                              context_instance=RequestContext(request))


def vehicle_page(request, vehicle_tree=None, motor=None, fuel=None):
    d = request.GET.dict()
    d['v'] = vehicle_tree
    request.extraGET = {"v": vehicle_tree}
    ct = search(request, d)
    if ct is None:
        raise Http404(_("The vehicle couldn't found"))
    if ct['vlevel'] == 0:
        ct['page_title'] = u'%s Markasında' % ct['vehiclepath'][0].name
    elif ct['vlevel'] == 1:
        ct['page_title'] = u'%s Markasının %s Modelinde' % (ct['vehiclepath'][0].name, ct['vehiclepath'][1].name)
    elif ct['vlevel'] == 2:
        ct['page_title'] = u'%s Markasının %s Modelinde' % (ct['vehiclepath'][0].name, ct['vehiclepath'][2].name)
    return render_to_response('shop/%s/search.html' % settings.SHOP_TEMPLATE, ct,
                              context_instance=RequestContext(request))


def tag_page(request, slug):
    tag = get_object_or_404(ProductTag, slug=slug)
    d = request.GET.dict()
    d['tag'] = unicode(tag.id)
    request.extraGET = {"tag": unicode(tag.id)}
    ct = search(request, d)
    if ct is None:
        raise Http404(_("The tag couldn't found."))

    ct['page_title'] = u'%s Etiketinde' % tag.name
    return render_to_response('shop/%s/search.html' % settings.SHOP_TEMPLATE, ct,
                              context_instance=RequestContext(request))


def product_page(request, cat, slug, _id):
    ct = {}
    ct['product'] = product = query.get_product(_id, user_group=request.user.group_id)
    if product is None:
        raise Http404("The product couldn't found")

    ct['methods'], ct['alternatives'] = query.get_active_payment_alternatives()
    ct['categorytree'] = query.get_path({"slug": cat})
    ct['similar_products'] = fetch_similar_products(request.user.id, product['id'])
    ct['oem_codes'] = fetch_oem_codes(product['id'])
    ct['vehicle_trees'] = get_vehicle_tree_from_product(product['id'])
    ct['brands'] = VehicleBrand.objects.all()

    if slug != slugify(product['name']) or len(ct['categorytree']) == 0 or ct['categorytree'][-1]['slug'] != product[
        'category_slug']:
        return redirect("shop_product", product['category_slug'], slugify(product['name']), product['id'])

    return render_to_response(('shop/' + settings.SHOP_TEMPLATE + '/product.html', 'shop/default/product.html'), ct,
                              context_instance=RequestContext(request))


def search_page(request):
    ct = search(request, request.GET)
    if ct is None:
        raise Http404("The category couldn't found")

    return render_to_response('shop/%s/search.html' % settings.SHOP_TEMPLATE, ct,
                              context_instance=RequestContext(request))


def search(request, req):
    ct = {}
    p = {}

    _page = 1 if 'p' not in req else int(req['p'])

    if req.get('c'):
        ct['category'] = cat = get_object_or_404(Category, slug=req['c'])
        ct['categoryfields'] = query.get_metadata(cat.id)
        cat.cached_ancestors = query.get_path({"slug": cat.slug})
        p['category'] = cat

    vlevel = None
    p['vehicle'] = pvehicle = {}
    ct['levels'] = p_levels = []
    if req.get('v'):
        vehicle = get_object_or_404(VehicleTree, slug=req['v'])
        ct['vehiclepath'] = vehiclepath = vehicle.get_ancestors(include_self=True)
        for pa in vehiclepath:
            p_levels.append(VehicleTree.objects.filter(parent_id=pa.parent_id).order_by('name'))
        ct['vehicle'] = vehicle
        pvehicle['level'] = vlevel = vehicle.level
        pvehicle['vehicle_tree_branch'] = vehicle.id
    else:
        p_levels.append(VehicleTree.objects.filter(parent_id=None).order_by('name'))

    if req.get('motor', False):
        if vlevel >= 2:
            vlevel = 3
            ct['motor_types'] = motor_types = query.get_motor_types(vehicle.id)
            mot = [motor for motor in motor_types if motor['slug'] == req['motor']]
            if len(mot) > 0:
                ct['motor_type'] = motor_type = mot[0]
            else:
                raise Http404("Motor tipi bulunamadı")
            pvehicle['vehicle_motor_type'] = motor_type['id']

    if req.get('fuel', False):
        if vlevel >= 3:
            vlevel = 4
            ct['fuel_types'] = fuel_types = query.get_fuel_types(vehicle.id, motor_type, by="slug")
            fuels = [fuel for fuel in fuel_types if fuel['slug'] == req['fuel']]
            if len(fuels) > 0:
                ct['fuel_type'] = fuel_type = fuels[0]
            else:
                raise Http404("Yakıt tipi bulunamadı")

            pvehicle['vehicle_fuel_type'] = fuel_type['id']

    if req.get('vyear', False):
        pvehicle['vehicle_years'] = vy = req['vyear'].split("-")
        if not vy[0].isdigit() or (len(vy) > 1 and not vy[1].isdigit()):
            raise Http404("Yıl değeri ancak sayı veya sayı aralığı olabilir. Örnek: 2006 veya 2006-2010.")

        if vlevel >= 4:
            vlevel = 5
            ct['vehicle_years'] = vehicle_years = query.get_vehicle_years(vehicle.id, motor_type, fuel_type, by="slug")
            combinations = [year_comb for year_comb in vehicle_years if year_comb['slug'] == req['vyear']]
            if len(combinations) == 0:
                raise Http404(_("The vehicle year combination couldn't found"))
            else:
                ct['vehicle_year'] = vehicle_year = combinations[0]

            years = vehicle_year['slug'].split('-')
            pvehicle['vehicle_years'] = (int(years[0]), int(years[1]) if len(years) > 1 else None)

    if vlevel is not None:
        ct['vlevel'] = vlevel
        p['vehicle'] = pvehicle

    if req.get('vbrand', False):
        p['vehicle']['vehicle_brand_fulltext'] = req['vbrand']

    if req.get('vmodel', False):
        p['vehicle']['vehicle_brand_model_fulltext'] = req['vmodel']

    if req.get('oem'):
        p['oem_code'] = req.get('oem')

    if req.get('vtype', False):
        p['vehicle']['vehicle_brand_model_type_fulltext'] = req['vtype']

    if req.get('vcat', False):
        p['category_fulltext'] = req['vcat']

    if 'catalog' in req and req['catalog'] in CATALOG_TYPES.keys():
        ct['catalog_template'] = CATALOG_TYPES[req['catalog']]
        ct['catalog'] = req['catalog']
    else:
        ct['catalog_template'] = CATALOG_TYPES['square']
        ct['catalog'] = 'square'

    if len(req.get('tag', "")) > 0:
        p['tag'] = [int(i) for i in req['tag'].split("-") if i.isdigit()]

    if 'q' in req and req['q']:
        ct['search_term'] = p['fulltext'] = req['q']
        # ct['search_term'] = p['fulltext'] = re.sub(r"([0-9\-\*/\\\?\-\. ]+){6,}",
        #                                            lambda match: " %s " % re.sub('[*-/. \\\]', '', match.group()),
        #                                            req['q'])

    p['limit'] = per_page = req['per_page'] if req.get('per_page') >= PER_PAGE[0] >= req['per_page'] else PER_PAGE[0]

    if req.get('code'):
        p['product_code'] = req['code']

    p['order_by'] = (('-', 'product.quantity>0'), ('-', "image.image is not null"))

    order = req.get('or')
    if order and order[1:] in ORDER_BY and order[0] in ["i", "d"]:
        p['order_by'] += (("+" if order[0] == "i" else "-", ORDER_BY[order[1:]]),)

    price0 = req.get('price0', "")
    price1 = req.get('price1', "")
    if price0 or price1:
        if (price0 and not price0.isdigit()) or (price1 and not price1.isdigit()):
            raise SuspiciousOperation(_("The query string is not valid"))
        p["price"] = (int(price0) if price0.isdigit() else None, int(price1) if price1.isdigit() else None)

    ct['manufacturers'] = Manufacturer.objects.all()
    if 'br' in req:
        p['manufacturer'] = [int(i) for i in req['br'].split("-") if i.isdigit()]

    if req.get('brand'):
        p['manufacturer_fulltext'] = req.get('brand')

    p['offset'] = (_page - 1) * per_page

    p['facets'] = {'vehicle_level': -1 if vlevel is None else (None if vlevel == 5 else vlevel),
                   'parent_category': cat.id if ct.get('category') else None}
    if vlevel > 2:
        p['facets']['motor_type'] = motor_type['id']
    if vlevel > 3:
        p['facets']['fuel_type'] = fuel_type['id']
    if vlevel > 4:
        p['facets']['vehicle_years'] = vehicle_year

    if vlevel is not None:
        p['facets']['parent_vehicle_branch'] = vehicle.id
    ct['result'] = query.get_products_by(request.user.group_id, **p)
    return ct


def page(request, slug):
 #   print 1
    ct = {}
    try:
        ct['page'] = Page.objects.get(slug=slug)
        ct['categories'] = Category.objects.filter(parent__isnull=True)
    except Page.DoesNotExist:
        raise Http404(_("The page couldn't found"))

    return render_to_response('shop/%s/page.html' % settings.SHOP_TEMPLATE, ct,
                              context_instance=RequestContext(request))


def handler404(request):
    response = render_to_response('shop/%s/404.html' % settings.SHOP_TEMPLATE, {},
                                  context_instance=RequestContext(request))
    response.status_code = 404
    return response


def handler400(request, *args, **kwargs):
    response = render_to_response('shop/%s/400.html' % settings.SHOP_TEMPLATE, {},
                                  context_instance=RequestContext(request))
    response.status_code = 400
    return response


def handler500(request):
    response = render_to_response('shop/%s/500.html' % settings.SHOP_TEMPLATE, context_instance=RequestContext(request))
    response.status_code = 500
    return response


def handler403(request):
    response = render_to_response('shop/%s/403.html' % settings.SHOP_TEMPLATE, context_instance=RequestContext(request))
    response.status_code = 403
    return response


def tos_page(request):
    return render_to_response('shop/%s/tos_page.html' % settings.SHOP_TEMPLATE,
                              context_instance=RequestContext(request))


def about_us(request):
    return render_to_response('shop/%s/about_us.html' % settings.SHOP_TEMPLATE,
                              context_instance=RequestContext(request))


def contact_us(request):
    return render_to_response('shop/%s/contact_us.html' % settings.SHOP_TEMPLATE,
                              context_instance=RequestContext(request))


def affiliates(request):
    return render_to_response('shop/%s/affiliates.html' % settings.SHOP_TEMPLATE,
                              context_instance=RequestContext(request))


@cache_page(60 * 60 * 24)
@required_parameters(GET={'id': int})
def main_menu_ajax(request):
    if request.method == 'GET':
        brand_id = request.GET.get('id')
        vehicle_models = VehicleTree.objects.filter(parent_id=brand_id).order_by("name")
        cats = set()
        exclude = []
        for model in vehicle_models:
            categories = \
                query.get_products_by(request.user.id, facets={'parent_category': None}, data=False,
                                      vehicle={'vehicle_tree_branch': model.id, 'level': 1})['facets'].get('category')
            for_model = []
            if categories is not None:
                for category_ in categories:
                    cats.add((category_['slug'], category_['name']))
                    for_model.append(category_['slug'])
            else:
                exclude.append(model.id)
            model.categories = json.dumps(for_model)

        return HttpResponse(get_template('shop/%s/includes/modalbox/main_menu.html' % settings.SHOP_TEMPLATE).render(
            Context({'vehicle_models': vehicle_models, 'exclude_ids': exclude, 'MEDIA_URL': settings.MEDIA_URL,
                     'categories': sorted(cats, key=lambda k: k[0])})))
    else:
        return HttpResponse("")


def template_context_processor(request):
    return {'SHOP_TEMPLATE': settings.SHOP_TEMPLATE}