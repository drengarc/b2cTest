import re
import math
import json

from django import template
from django.dispatch import Signal
from django.conf import settings
from django.template import Library
from django.core.urlresolvers import reverse
from django.utils.text import slugify
from django.utils.safestring import mark_safe
from shop.utils.cache import get_cache
from django.utils.translation import ugettext as _

register = Library()

CACHE_TIMEOUT = 60 * 60 * 24


@register.filter
def lookup(d, key):
    return d[key]


@register.filter
def jsonify(list):
    return mark_safe(json.dumps(list))


@register.filter
def installment(price, alternative):
    if alternative['minimum_price'] > price:
        return ''
    if alternative['discount_amount'] is not None:
        price -= alternative['discount_amount']
    elif alternative['discount_percentage'] is not None:
        price = (price * (100 - alternative['discount_percentage'])) / 100
    return price


@register.filter
def divide(value, arg):
    return value / arg


class SetVarNode(template.Node):
    def __init__(self, new_val, var_name):
        self.new_val = new_val
        self.var_name = var_name

    def render(self, context):
        context[self.var_name] = self.new_val
        return ''


@register.tag
def setvar(parser, token):
    # This version uses a regular expression to parse tag contents.
    try:
        # Splitting by None == splitting by spaces.
        tag_name, arg = token.contents.split(None, 1)
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires arguments" % token.contents.split()[0]
    m = re.search(r'(.*?) as (\w+)', arg)
    if not m:
        raise template.TemplateSyntaxError, "%r tag had invalid arguments" % tag_name
    new_val, var_name = m.groups()
    if not (new_val[0] == new_val[-1] and new_val[0] in ('"', "'")):
        raise template.TemplateSyntaxError, "%r tag's argument should be in quotes" % tag_name
    return SetVarNode(new_val[1:-1], var_name)


@register.filter
def subtract(value, arg):
    return value - arg


@register.filter
def add_decimal(value, arg):
    return value + arg


@register.filter
def get_discount_rate(value, arg):
    return "%" + str(100 - int((arg * 100) / value['price']))


@register.filter
def is_false(arg):
    return arg is False


@register.filter
def last_queryset(arg):
    try:
        return arg[len(arg) - 1]
    except:
        return None


@register.filter
def get_price(product, user=None):
    return product.get_price(user)[1]


@register.filter
def decimalparser(price, tag):
    price, decimal = str(price).split('.')
    return price + ",<" + tag + ">" + decimal[:2] + "</" + tag + ">"


class SetVarNode(template.Node):
    def __init__(self, var_name, var_value):
        self.var_name = var_name
        self.var_value = var_value

    def render(self, context):
        try:
            value = template.Variable(self.var_value).resolve(context)
        except template.VariableDoesNotExist:
            value = ""
        context[self.var_name] = value
        return u""


@register.tag
def set(parser, token):
    """
        {% set <var_name>  = <var_value> %}
    """
    parts = token.split_contents()
    if len(parts) < 4:
        raise template.TemplateSyntaxError("'set' tag must be of the form:  {% set <var_name>  = <var_value> %}")
    return SetVarNode(parts[1], parts[3])


change_param = Signal(providing_args=['q'])


class ChangeURLParam(template.Node):
    def __init__(self, _type, value=None, add=False, nodelist=None, toggle=None, remove=None, raw=False):
        self.type = _type
        self.value = value
        self.add = add
        self.nodelist = nodelist
        self.toggle = toggle
        self.remove = remove
        self.raw = raw

    def render(self, context):
        request = template.Variable('request').resolve(context)
        var_type = template.Variable(self.type).resolve(context)
        if self.value is not None:
            value = unicode(template.Variable(self.value).resolve(context))
        else:
            value = None
        q = request.GET.copy()
        if hasattr(request, "extraGET"):
            for k, v in request.extraGET.iteritems():
                q[k] = v
        found = False
        if self.nodelist or self.toggle:
            if q.get(var_type) == value:
                found = True
            else:
                types = q.get(var_type, "").split("-")
                if value in types:
                    found = True
        if self.nodelist:
            if found:
                return self.nodelist.render(context)
            else:
                return ''
        if self.remove and var_type in q:
            del q[var_type]
        elif not self.add or var_type not in q:
            q[var_type] = value
        else:
            types = q[var_type].split("-")
            if self.toggle and found:
                types.remove(value)
            elif value not in types:
                types.append(value)
            q[var_type] = "-".join(types)
        responses = change_param.send(sender=self, q=q, key=var_type, value=value)
        for response in responses:
            if response[1] is not None and not self.raw:
                return response[1]
        if not self.raw:
            return reverse('shop_list_page') + "?" + q.urlencode()
        else:
            return q.urlencode()


@register.tag
def change_parameter_url(parser, token):
    parts = token.split_contents()[1:]
    return ChangeURLParam(*parts)


@register.tag
def change_parameter_url_raw(parser, token):
    parts = token.split_contents()[1:]
    return ChangeURLParam(*parts, raw=True)


@register.tag
def add_parameter_url(parser, token):
    parts = token.split_contents()
    return ChangeURLParam(parts[1], parts[2], add=True)


@register.tag
def toggle_parameter_url(parser, token):
    parts = token.split_contents()
    return ChangeURLParam(parts[1], parts[2], toggle=True, add=True)


@register.tag
def remove_parameter_url(parser, token):
    parts = token.split_contents()
    return ChangeURLParam(parts[1], None, remove=True)


@register.tag
def remove_parameter_url_raw(parser, token):
    parts = token.split_contents()
    return ChangeURLParam(parts[1], None, remove=True, raw=True)


@register.tag
def param_exists(parser, token):
    nodelist = parser.parse(('endparam_exists',))
    parts = token.split_contents()
    parser.next_token()
    return ChangeURLParam(parts[1], parts[2], nodelist=nodelist)


@register.simple_tag
def get_conf(conf_str):
    from shop.models import Config

    return Config.objects.conf(conf_str)


@register.filter
def get_product_link(product):
    return reverse("shop_product", args=[product['category'], slugify(product['name']), product['id']])


@register.filter
def get_product_category_path(product):
    return product['vehicle']


@register.inclusion_tag("shop/default/includes/pagination.html")
def pagination(context, request, param, adjacent_pages=3):
    offset = max(0, context['offset'])
    page = int(math.ceil(float(offset) / context['per_page'])) + 1
    last_page = int(math.ceil(float(context['facets']['count']) / context['per_page']))
    startPage = max(page - adjacent_pages, 1)
    if startPage <= adjacent_pages:
        startPage = 1
    endPage = page + adjacent_pages + 1
    if endPage + adjacent_pages >= last_page:
        endPage = last_page
    previous = page - 1 if page > 1 else False
    next = page + 1 if page < last_page else False

    return {
        'pages': range(startPage, min(endPage, last_page) + 1),
        'per_page': context['per_page'],
        'current_page': page,
        'next': next,
        'previous': previous,
        'param': param,
        'request': request
    }


class TopCategories(template.Node):
    def __init__(self, var_name):
        from shop.models import Category

        self.categories = get_cache("shop:top_categories", lambda: Category.objects.filter(level=0).order_by('name'))
        self.var_name = var_name

    def render(self, context):
        context[self.var_name] = self.categories
        return ''


@register.tag
def get_top_categories(_, token):
    # This version uses a regular expression to parse tag contents.
    try:
        # Splitting by None == splitting by spaces.
        tag_name, arg = token.contents.split(None, 1)
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires arguments" % token.contents.split()[0]
    m = re.search(r'as (\w+)', arg)
    if not m:
        raise template.TemplateSyntaxError, "%r tag had invalid arguments" % tag_name
    var_name, = m.groups()
    return TopCategories(var_name)

@register.tag
def recursetree(parser, token):
    """
    Iterates over the nodes in the tree, and renders the contained block for each node.
    This tag will recursively render children into the template variable {{ children }}.
    Only one database query is required (children are cached for the whole tree)

    Usage:
            <ul>
                {% recursetree nodes %}
                    <li>
                        {{ node.name }}
                        {% if not node.is_leaf_node %}
                            <ul>
                                {{ children }}
                            </ul>
                        {% endif %}
                    </li>
                {% endrecursetree %}
            </ul>
    """
    bits = token.contents.split()
    if len(bits) != 2:
        raise template.TemplateSyntaxError(_('%s tag requires a queryset') % bits[0])

    queryset_var = template.Variable(bits[1])

    template_nodes = parser.parse(('endrecursetree',))
    parser.delete_first_token()

    return RecurseTreeNode(template_nodes, queryset_var)

class RecurseTreeNode(template.Node):
    def __init__(self, template_nodes, data):
        self.template_nodes = template_nodes
        self.data = data

    def _render_node(self, context, node):
        bits = []
        context.push()
        context['node'] = node
        context['children'] = mark_safe(''.join(bits))
        rendered = self.template_nodes.render(context)
        context.pop()
        return rendered

    def render(self, context):
        queryset = self.data.resolve(context)
        bits = [self._render_node(context, node) for node in queryset]
        return ''.join(bits)


@register.simple_tag
def get_version():
    return settings.PROJECT_VERSION


@register.simple_tag
def get_basket_item_count(request):
    if not request:
        raise ValueError("request object must be passed to templates.")

    if hasattr(request, "user") and request.user.is_authenticated():
        return request.user.customerbasket_set.count()
    else:
        try:
            return len(json.loads(request.COOKIES.get('basket')))
        except:
            return 0

@register.simple_tag
def get_basket(request):
    if not request:
        raise ValueError("request object must be passed to templates.")

    if hasattr(request, "user") and request.user.is_authenticated():
        return request.user.customerbasket_set.count()
    else:
        try:
            return json.loads(request.COOKIES.get('basket'))
        except:
            return 0