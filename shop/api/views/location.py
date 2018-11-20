import json
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from shop.models import City, Ilce


@csrf_exempt
def city(request):
    try:
        country = int(request.POST.get('country'))
    except:
        return HttpResponse(json.dumps({"error": "country is required"}), content_type="application/json")

    cities = City.objects.filter(country_id=country)
    return HttpResponse(json.dumps(list(cities.values())), content_type="application/json")


@csrf_exempt
def ilce(request):
    try:
        city = int(request.POST.get('city'))
    except:
        return HttpResponse(json.dumps({"error": "city is required"}), content_type="application/json")

    ilceler = Ilce.objects.filter(city_id=city)
    return HttpResponse(json.dumps(list(ilceler.values())), content_type="application/json")
