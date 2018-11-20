import json
from django.http import HttpResponse
from shop import helpers
from shop.utils.request import required_parameters
from vehicle.models import VehicleTree
from vehicle.query import get_vehicle_tree_from_product


@required_parameters(GET={'parent': unicode})
def vehicle_path(request):
    data = VehicleTree.objects.filter(parent__slug=request.GET.get('parent')).values('slug', 'name')

    return HttpResponse(json.dumps(list(data)), content_type="application/json")

@required_parameters(GET={'vehicle': unicode})
def motor_type(request):
    cursor = helpers.Connection()
    data = cursor.fetchall(
        "select slug, name from vehicle_motor_type where id in (select motor_type_id from vehicle where model_type_id = (select id from vehicle_tree where slug = %s))",
        [request.GET.get('vehicle')])
    return HttpResponse(json.dumps(data), content_type="application/json")


@required_parameters(GET={'vehicle': unicode, 'motor': unicode})
def fuel_type(request):
    cursor = helpers.Connection()

    data = cursor.fetchall(
        "select slug, name from vehicle_fuel_type where id in (select fuel_type_id from vehicle where model_type_id = (select id from vehicle_tree where slug = %s) and motor_type_id = (select id from vehicle_motor_type where slug = %s))",
        [request.GET.get('vehicle'), request.GET.get('motor')])
    return HttpResponse(json.dumps(data), content_type="application/json")

@required_parameters(GET={'vehicle': unicode, 'motor': unicode, 'fuel': unicode})
def vehicle_years(request):
    cursor = helpers.Connection()

    data = cursor.fetchall(
        "(select distinct begin_year || (CASE WHEN end_year IS NOT NULL THEN '-' || end_year ELSE '' END) as name, begin_year || (CASE WHEN end_year IS NOT NULL THEN '-' || end_year ELSE '' END) as slug from vehicle where model_type_id = (select id from vehicle_tree where slug = %s) and motor_type_id = (select id from vehicle_motor_type where slug = %s) and fuel_type_id = (select id from vehicle_fuel_type where slug = %s))",
        [request.GET.get('vehicle'), request.GET.get('motor'), request.GET.get('fuel')])
    return HttpResponse(json.dumps(data), content_type="application/json")

@required_parameters(GET={'products': unicode, 'vehicle': unicode, 'motor': unicode})
def product_supports_vehicle(request):
    try:
        vehicle = VehicleTree.objects.get(slug=request.GET.get('vehicle'))
    except VehicleTree.DoesNotExist:
        return HttpResponse(json.dumps({"status": 404}), content_type="application/json")

    products = request.GET.get('products').split("-")
    result = {}
    for product in products:
        supported_vehicles = get_vehicle_tree_from_product(product)
        status = len([1 for i in supported_vehicles if i[vehicle.level]['slug'] == vehicle.slug]) > 0
        if vehicle.level < 2:
            return status

        if status and request.GET.get('motor'):
            status = status and len([1 for i in supported_vehicles if i[3]['slug'] == request.GET.get('motor')]) > 0

        if status and request.GET.get('fuel'):
            status = status and len([1 for i in supported_vehicles if i[4]['slug'] == request.GET.get('fuel')]) > 0

        if status and request.GET.get('years'):
            status = status and len([1 for i in supported_vehicles if i[5]['slug'] == request.GET.get('years')]) > 0

        result[product] = status
    return HttpResponse(json.dumps(result), content_type="application/json")


