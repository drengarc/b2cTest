from django.core.urlresolvers import reverse, reverse_lazy
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

from admin_tools.menu import items
from menu import register_menu_item
from shop.templatetags.shop_tags import change_param


@register_menu_item
def menu_items():
    shop = items.ModelList(
        title=_('vehicle'),
        models=('vehicle.models.FuelType', 'vehicle.models.Vehicle', 'vehicle.models.MotorType', ),
        url=reverse_lazy('admin:app_list', kwargs={'app_label': 'vehicle'})
    )
    tree = items.ModelList(
        title=_('vehicle tree'),
        models=(
            'vehicle.models.VehicleBrand', 'vehicle.models.VehicleBrandModel', 'vehicle.models.VehicleBrandModelType',
            'vehicle.models.VehicleOther', ),
    )
    shop.children.append(tree)
    return shop


@receiver(change_param)
def delete_denied_params(sender, q, key=None, value=None, **kwargs):
    # these keys are temporary keys and must be available only for that specific search.
    for k in ['p', ]:
        if key != k and k in q:
            del q[k]
    keys = q.keys()
    if key == 'v':
        for i in keys:
            if i in ['motor', 'fuel', 'vyear', 'code', 'brand', 'vbrand', 'oem', 'vmodel', 'vcat', 'q', 'category']:
                del q[i]
    elif key == "motor":
        for i in keys:
            if i in ['fuel', 'vyear', 'code', 'brand', 'vbrand', 'oem', 'vmodel', 'vcat', 'q', 'category']:
                del q[i]
    elif key == "fuel":
        for i in keys:
            if i in ['vyear', 'code', 'brand', 'vbrand', 'oem', 'vmodel', 'vcat', 'q', 'category']:
                del q[i]
    elif key == "vyear":
        for i in keys:
            if i in ['code', 'brand', 'vbrand', 'oem', 'vmodel', 'vcat', 'q', 'category']:
                del q[i]
    elif key in ['code', 'brand', 'vbrand', 'oem', 'vmodel', 'vcat', 'q']:
        for i in keys:
            if i in ['motor', 'fuel', 'vyear']:
                del q[i]

    keys = q.keys()
    if keys == [u'c'] and q.get('c'):
        return reverse('shop_category_page', args=(q.get('c'),))
    elif keys == [u'v'] and q.get('v'):
        return reverse('shop_vehicle_page', args=(q.get('v'),))

