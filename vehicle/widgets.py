from django.forms import Widget
from django.template import Context
from django.template.loader import get_template
from django.utils.datastructures import MultiValueDict, MergeDict
from vehicle.models import VehicleBrand, Vehicle


class VehicleSelect(Widget):
    allow_multiple_selected = True

    def value_from_datadict(self, data, files, name):
        if isinstance(data, (MultiValueDict, MergeDict)):
            return data.getlist(name)
        return data.get(name, None)

    def render(self, name, values, attrs=None, choices=()):
        ct = {'brands': VehicleBrand.objects.all()}
        str = []
        if values is not None and len(values) > 0:
            for idx, value in enumerate(values):
                vehicle = ct['vehicle'] = Vehicle.objects.get(pk=value)
                ct['brandmodeltype'] = brandmodeltype = vehicle.vehicle_model_type
                ct['brandmodel'] = brandmodel = brandmodeltype.parent
                ct['brand'] = brandmodel.parent
                ct['motortype'] = vehicle.motor_type
                ct['fueltype'] = vehicle.fuel_type
                ct['vehicles'] = Vehicle.objects.filter(vehicle_model_type=brandmodeltype, motor_type=vehicle.motor_type, fuel_type=vehicle.fuel_type)
                str.append(get_template('vehicle/vehicle_widget.html').render(Context(dict(ct.items() + ({"last": True} if idx == len(values)-1 else {}).items()))))
        if len(str) == 0:
            return get_template('vehicle/vehicle_widget.html').render(Context(dict(ct.items() + {"last": True}.items())))
        else:
            return "\n".join(str)