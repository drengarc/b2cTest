# -*- coding: utf-8 -*-
from decimal import Decimal
from itertools import groupby
import re

from django.core.cache import cache
from django.core.urlresolvers import reverse
from unidecode import unidecode

from shop import helpers
from shop.helpers import get_custom_variable
from shop.models import Config, Product, ProductAttributeChoice
from shop.utils.cache import DEFAULT_CACHE_TIMEOUT, cache_func
from shop.utils.exception import BasketItemInsufficientStock, BasketItemNotExist


MAX_ROW_PER_QUERY = 100
DISCOUNT_QUERY = '''
    SELECT d.id, d.name, d.amount, d.percentage, d.minimum_order_price, array_agg(DISTINCT tag.producttag_id) tags, array_agg(DISTINCT cat.category_id) cats, array_agg(DISTINCT customer.customergroup_id) customers
    FROM discount d LEFT JOIN discount_category cat ON (d.id = cat.category_id)
    LEFT JOIN discount_product_tag tag ON (d.id = tag.discount_id)
    LEFT JOIN discount_customer_group customer ON (customer.discount_id = d.id)
    WHERE d.is_active = TRUE AND CURRENT_DATE BETWEEN start_date AND end_date GROUP BY d.id
'''

FACET_IDS = {
    0: "count",
    1: "manufacturer",
    2: "category",
    3: "vehicle",
    4: "tag",
}

VEHICLE_TREE_FACET_QUERY = [
    '''
    SELECT dataset_count, brand.id, brand.name, brand.slug, 3 AS filter FROM (
    SELECT COUNT (DISTINCT dataset. ID) as dataset_count, rel.brand_id as vehicle_brand_id
    FROM dataset
    JOIN vehicle rel ON (dataset.grup_id = rel.grup_id)
    WHERE in_tag != false and in_manufacturer != false
    GROUP BY rel.brand_id
    ) rel
    JOIN vehicle_tree brand ON rel.vehicle_brand_id = brand.id
    ORDER BY brand.name
    ''',

    '''
    SELECT dataset_count, model.id, model.name, model.slug, 3 AS filter FROM (
    SELECT COUNT (DISTINCT dataset. ID) as dataset_count, rel.model_id as vehicle_model_id
    FROM dataset
    JOIN vehicle rel ON (dataset.grup_id = rel.grup_id)
    WHERE rel.brand_id = %s and in_tag != false and in_manufacturer != false
    GROUP BY rel.model_id
    ) rel
    JOIN vehicle_tree model ON rel.vehicle_model_id = model.id
    ORDER BY model.name
    ''',

    '''
    SELECT dataset_count, model_type.id, model_type.name, model_type.slug, 3 AS filter FROM (
    SELECT COUNT (DISTINCT dataset. ID) as dataset_count, rel.model_type_id as model_type_id
    FROM dataset
    JOIN vehicle rel ON (dataset.grup_id = rel.grup_id)
    WHERE rel.model_id = %s and in_tag != false and in_manufacturer != false
    GROUP BY rel.model_type_id
    ) rel
    JOIN vehicle_tree model_type ON rel.model_type_id = model_type.id
    ORDER BY model_type.name
    ''',

    '''
    SELECT dataset_count, motor_type.id, motor_type.name, motor_type.slug, 3 AS filter FROM (
    SELECT COUNT (DISTINCT dataset. ID) as dataset_count, rel.motor_type_id as vehicle_motor_type_id
    FROM dataset
    JOIN vehicle rel ON (dataset.grup_id = rel.grup_id)
    WHERE rel.model_type_id = %s and in_tag != false and in_manufacturer != false
    GROUP BY rel.motor_type_id
    ) rel
    JOIN vehicle_motor_type motor_type ON rel.vehicle_motor_type_id = motor_type.id
    ORDER BY motor_type.name
    ''',

    '''
    SELECT dataset_count, fuel_type.id, fuel_type.name, fuel_type.slug, 3 AS filter FROM (
    SELECT COUNT (DISTINCT dataset. ID) as dataset_count, rel.fuel_type_id as vehicle_fuel_type_id
    FROM dataset
    JOIN vehicle rel ON (dataset.grup_id = rel.grup_id)
    WHERE rel.model_type_id = %s AND rel.motor_type_id = %s and in_tag != false and in_manufacturer != false
    GROUP BY rel.fuel_type_id
    ) rel
    JOIN vehicle_fuel_type fuel_type ON rel.vehicle_fuel_type_id = fuel_type.id
    ORDER BY fuel_type.name
    ''',

    '''
    SELECT COUNT (DISTINCT dataset. ID), null, rel.begin_year || COALESCE('-' || rel.end_year, ''), rel.begin_year || COALESCE('-' || rel.end_year, ''), 3 as filter
    FROM dataset
    JOIN vehicle rel ON (dataset.grup_id = rel.grup_id)
    WHERE rel.model_type_id = %s AND rel.motor_type_id = %s AND rel.fuel_type_id = %s and in_tag != false and in_manufacturer != false
    GROUP BY rel.begin_year, rel.end_year
    ORDER BY rel.begin_year, rel.end_year
    '''
]


def get_active_payment_alternatives():
    cursor = helpers.Connection()
    result = cursor.fetchall('''select  m.name as method_name, p.description,  m.image as method_image, p.installment, p.discount_percentage, p.discount_amount, p.minimum_price
            from est_installmentalternative p
            join est_bank m on (p.bank_id = m.id) where p.package_id = %s order by installment,m.name''',
                             [Config.objects.conf("ACTIVE_PAYMENTPACKAGE")])


    methods = {}
    desc_counter = 0
    for alternative in result:
        if 'description' in alternative:
            desc_counter += 1
            alternative['desc_counter'] = desc_counter

        if alternative['method_name'] in methods:
            m = methods[alternative['method_name']]
            if m['max_installment'] < alternative['installment']:
                m['max_installment'] = alternative['installment']
        else:
            methods[alternative['method_name']] = {}
            methods[alternative['method_name']]['max_installment'] = alternative['installment']
            methods[alternative['method_name']]['image'] = alternative['method_image']

    alternatives = {}
    for installment, payment in groupby(result, lambda a: int(a['installment'])):
        alternatives[installment] = list(payment)

    return methods, alternatives


def get_path(query={}, types=None, include_me=True):
    if len(query) == 0 and False:
        raise Exception("You must pass at least one filter")

    cursor = helpers.Connection()
    a = []
    for k, v in query.iteritems():
        a.append((" parent.%s = " % k) + "%s")

    params = query.values()
    select = "SELECT node.id, node.name, node.slug, node.level"
    squery = " FROM category AS node, category AS parent "
    where = " WHERE node.lft <= parent.lft " + ("-1" if not include_me else "") + " AND node.rght >= parent.rght " + (
        "+1" if not include_me else "") + " " + ("and" if len(a) > 0 else "") + " and ".join(
        a) + " and parent.tree_id = node.tree_id "
    order = " ORDER BY node.lft, level"

    if types is not None:
        if types is False:
            where += " and parent.type is null"
        else:
            where += " and parent.type in (" + ",".join(list(map(lambda x: '%s', types))) + ")"
            params += types

    return cursor.fetchall(select + squery + where + order, params)


def get_same_level(dict):
    a = []
    for k, v in dict.iteritems():
        a.append((" node.%s = " % k) + "%s")
    cursor = helpers.Connection()
    select = "SELECT id, name, slug, level "
    query = " FROM category where parent_id <=> (select node.parent_id from category node where " + " and ".join(
        a) + ") and category.tree_id = (select node.tree_id from category node where " + " and ".join(
        a) + ")  order by id"
    params = dict.values() + dict.values()
    return cursor.fetchall(select + query, params)


def get_children(dict, max_deep=None, include_me=True):
    cursor = helpers.Connection()
    a = []
    for k, v in dict.iteritems():
        a.append((" parent.%s = " % k) + "%s")
    select = " SELECT node.id, node.name, node.slug, node.level "
    query = " FROM category AS node, category AS parent "
    where = " WHERE node.lft >" + ("=" if include_me is True else "") + " parent.lft AND  node.lft <" + (
        "=" if include_me is True else "") + " parent.rght AND " + " and ".join(
        a) + " AND parent.tree_id = node.tree_id "
    order_by = " ORDER BY node.lft "
    params = dict.values()

    if max_deep is not None:
        where += " and parent.level+%s >= node.level "
        params.append(max_deep)

    return cursor.fetchall(select + query + where + order_by, params)


def get_category(id=None, slug=None, attrs=True):
    cursor = helpers.Connection()

    if slug is None and id is None:
        raise Exception()

    category = cursor.fetch(
        "SELECT id, name, image, description FROM category WHERE " + ("id" if id is not None else "slug") + " = %s",
        [id if id is not None else slug])
    if category is None:
        return None
    if attrs:
        category['attrs'] = cursor.fetchall('''select pschema.id, pschema.title, pschema.help_text, pschema.datatype, value_text, value_float, value_date, value_bool from category_attribute_value val
                join category_attribute_schema pschema on (pschema.id = val.schema_id)
                where val.entity_id = %s''', [category['id']])
    return category


def get_metadata(category_id):
    choice_list = ProductAttributeChoice.objects.filter(attribute__category=category_id)

    attributes = {}
    for c in choice_list:
        if c.attribute.name not in attributes:
            attributes[c.attribute.name] = []
        attributes[c.attribute.name].append(c.choice)

    return attributes


@cache_func(60)
def get_active_brands():
    cursor = helpers.Connection()
    return cursor.fetchall(
        "select brand.id, brand.slug, brand.name from product join vehicle rel on (rel.grup_id = product.grup_id) join vehicle_tree brand on (brand.id = rel.brand_id) group by brand.id order by brand.name")


def get_discounts():
    cursor = helpers.Connection()
    cache_key = 'shop:product:discounts'
    discounts = cache.get(cache_key)
    if discounts is None:
        discounts = cursor.fetchall('''SELECT discount.id, discount.percentage, discount.amount, discount.end_date, array(SELECT DISTINCT customergroup.customergroup_id) AS customer_groups,
                array(SELECT DISTINCT tag.producttag_id) AS tags, array(SELECT DISTINCT category.category_id) AS categories
                FROM discount
                LEFT JOIN discount_category category ON (category.discount_id = discount.id)
                LEFT JOIN discount_product_tag tag ON (tag.discount_id = discount.id)
                LEFT JOIN discount_customer_group customergroup ON (customergroup.discount_id = discount.id)
                WHERE start_date < now() + INTERVAL '1 day' AND end_date > now() ''', [])

        cache.set(cache_key, discounts, DEFAULT_CACHE_TIMEOUT)
    return discounts


def get_categories_by(type=None, filter=None):
    cursor = helpers.Connection()
    arg = []
    a = []
    where = []
    if filter is not None:
        for k, v in filter.iteritems():
            a.append(((" category.%s " + ("=" if v is not None else "is") + " ") % k) + "%s")

    if len(a) > 0:
        where.append(" AND ".join(a))
        arg += where.values()

    if type is not None:
        where.append(" category.type in (" + ', '.join(list(map(lambda x: '%s', type))) + ") ")
        arg += type

    return cursor.fetchall(
        "SELECT category.id, category.name, parent_id, slug, level, category.type FROM category WHERE " + " and ".join(
            where) + " ORDER BY category.tree_id, category.lft", arg)


# vehicle = {vehicle_years:[], vehicle_tree_branch:[], vehicle_motor_type:[], vehicle_fuel_type:[]}
# @cache_func(600)
def get_products_by(user_group, category=None, fulltext=None,
                    product_code=None, oem_code=None, vehicle=None, limit=15, offset=0,
                    in_customer_basket=None,
                    ids=None, facets=None, data=True, order_by=None, price=None, extra_where=None,
                    extra_join=None, extra_group_by=None,
                    extra_select=None, category_fulltext=None, in_stock=None, **kwargs):
    cursor = helpers.Connection()
    if limit > MAX_ROW_PER_QUERY:
        limit = MAX_ROW_PER_QUERY
    elif limit is not None and limit < 1:
        limit = 1
    get_children({'parent_id': None})
    if extra_where is None:
        extra_where = []
    if extra_select is None:
        extra_select = []
    if extra_join is None:
        extra_join = []
    if extra_group_by is None:
        extra_group_by = []
    if in_stock:
        extra_where.append(["quantity > 0"])
    select = '''
                WITH _discounts AS (
                    ''' + DISCOUNT_QUERY + '''
                )
                select product.id, product.quantity>0 as in_stock, product.weight, product.partner_code, product.name, product.price, manufacturer.name as manufacturer_name, category.slug as category, category.name as category_name, product.grup_id,
                array(select tags.producttag_id as tags from product_tags tags where tags.product_id = product.id) as tags,

                round(COALESCE((select (CASE WHEN d.percentage IS NOT NULL THEN (100-d.percentage)/100.0*COALESCE(product.discount_price, product.price) ELSE COALESCE(product.discount_price, product.price)-d.amount END)
                from _discounts d WHERE
                (d.cats = '{NULL}'::int[] or product.category_id = any(d.cats)) and
                (d.customers = '{NULL}'::int[] or %s = any(d.customers)) and
                (d.tags = '{NULL}'::int[] or d.tags && array(select producttag_id from product_tags where product_id = product.id)) order by COALESCE(d.percentage*product.price, d.amount) desc limit 1 ), product.discount_price, product.price), 2) discount_price,
                image.image  '''
    query = ''' from product left join category on (category.id = product.category_id) join manufacturer on (product.manufacturer_id = manufacturer.id) left join product_images image on (image.order = 0 and image.product_id = product.id)'''
    where = [" product.active = true "]
    params = [user_group]

    if vehicle is not None and vehicle is not {}:
        if isinstance(vehicle, dict):
            v_param = []
            v_cases = []
            if 'vehicle_tree_branch' in vehicle:
                if vehicle['level'] == 0:
                    v_cases.append(' brand_id = %s ')
                elif vehicle['level'] == 1:
                    v_cases.append(' model_id = %s ')
                elif vehicle['level'] == 2:
                    v_cases.append(' model_type_id = %s ')
                v_param.append(vehicle['vehicle_tree_branch'])

            if 'vehicle_motor_type' in vehicle:
                v_cases.append(' rel.motor_type_id = %s ')
                v_param.append(vehicle['vehicle_motor_type'])
            if 'vehicle_years' in vehicle:
                v_cases.append(' rel.begin_year = %s ')
                v_param.append(vehicle['vehicle_years'][0])

                if len(vehicle['vehicle_years']) > 1:
                    v_cases.append(
                        " rel.end_year " + ("=" if vehicle['vehicle_years'][1] is not None else "is") + " %s ")
                    v_param.append(vehicle['vehicle_years'][1])

            if 'vehicle_fuel_type' in vehicle:
                v_cases.append('rel.fuel_type_id = %s')
                v_param.append(vehicle['vehicle_fuel_type'])

            if len(v_param) > 0 or any([True for v in vehicle if
                                        v in ['vehicle_brand_fulltext', 'vehicle_brand_model_fulltext',
                                              'vehicle_brand_model_type_fulltext']]):
                query += " join vehicle rel on (rel.grup_id = product.grup_id) "
                where += v_cases
                params += v_param

            if 'vehicle_brand_fulltext' in vehicle:
                query += " join vehicle_tree brand on (brand.id = rel.brand_id) "
                where.append("  to_tsvector('simple_unaccent', brand.name) @@ plainto_tsquery('simple_unaccent', %s) ")
                params.append(vehicle['vehicle_brand_fulltext'])
            if 'vehicle_brand_model_fulltext' in vehicle:
                query += " join vehicle_tree model on (model.id = rel.model_id) "
                where.append("  to_tsvector('simple_unaccent', model.name) @@ plainto_tsquery('simple_unaccent', %s) ")
                params.append(vehicle['vehicle_brand_model_fulltext'])
            if 'vehicle_brand_model_type_fulltext' in vehicle:
                query += " join vehicle_tree model_type on (model_type.id = rel.model_type_id) "
                where.append(
                    "  to_tsvector('simple_unaccent', model_type.name) @@ plainto_tsquery('simple_unaccent', %s) ")
                params.append(vehicle['vehicle_brand_model_type_fulltext'])
        else:
            raise Exception("vehicle must be either list or dict")

    if category_fulltext is not None:
        where.append(" product.category_id in (SELECT node.id \
        FROM category AS node, category AS parent \
        WHERE node.lft >= parent.lft AND node.lft <= parent.rght AND parent.tree_id = node.tree_id \
        and LOWER (parent.name) LIKE LOWER (%s)) ")
        params.append(unidecode(category_fulltext.replace('=', '==').replace('%', '=%').replace('_', '=_') + "%"))

    if oem_code is not None:
        where.append(
            " product.grup_id in (select grup_id from ege.tb_kart_stok_oem where oem_no = %s or oem_no_orjinal = %s ) ")
        params.append(oem_code)
        params.append(oem_code)

    if ids is not None:
        where.append(" product.id = any (%s) ")
        params.append(ids)

    if len(extra_where) > 0:
        for w in extra_where:
            if not isinstance(w, list):
                raise Exception("extra_where items must be list")
            where.append(" %s " % w[0])
            if len(w) > 1:
                params += w[1]

    if len(extra_join) > 0:
        for w in extra_join:
            query += w[0]
            if len(w) > 1:
                params.append(" %s " % w[1])

    if len(extra_select) > 0:
        select += ", %s" % (", ".join(extra_select))

    if product_code is not None:
        where.append(" (regexp_replace(lower(partner_code), '[^0-9A-Za-z]+', '', 'g')) LIKE %s ")
        params.append(re.sub(r'\W+', '', product_code.lower()) + "%")

    if fulltext is not None:
        where.append(
            " product.fulltext @@ (SELECT ts_rewrite(plainto_tsquery('simple_unaccent', %s), 'SELECT to_tsquery(''simple_unaccent'', from_text), to_tsquery(''simple_unaccent'', to_text) FROM shop_synonym')) ")
        params.append(fulltext)

    if category is not None:
        str = " product.category_id in (select category.id from category parent, category where parent.id in (%s) AND category.lft BETWEEN parent.lft AND parent.rght and category.tree_id = parent.tree_id) "
        if isinstance(category, list):
            str %= ', '.join(list(map(lambda x: '%s', category)))
            params += category
        else:
            params.append(category.id)
        where.append(str)

    if in_customer_basket is not None:
        where.append(" product.id in (select product_id from customer_basket where customer_id = %s) ")
        params.append(in_customer_basket)

    result = {"offset": offset, "per_page": limit}

    if facets:
        f_select = '''
                select DISTINCT ON (product.id) product.id, manufacturer_id, category_id, product.grup_id,
                ''' + (" manufacturer_id in(%s) " % ', '.join(
            list(map(lambda x: '%s', kwargs["manufacturer"]))) if len(kwargs.get("manufacturer", [])) > 0 else "true") + ''' as in_manufacturer,
                ''' + (
                       " array(select producttag_id from product_tags where product_id = product.id) && ARRAY[%s] " % ', '.join(
                           list(map(lambda x: '%s', kwargs["tag"]))) if len(kwargs.get("tag", [])) > 0 else "true") + ''' as in_tag,
                round(COALESCE((select (CASE WHEN d.percentage IS NOT NULL THEN (100-d.percentage)/100.0*COALESCE(product.discount_price, product.price) ELSE COALESCE(product.discount_price, product.price)-d.amount END)
                from _discounts d WHERE
                (d.cats = '{NULL}'::int[] or product.category_id = any(d.cats)) and
                (d.customers = '{NULL}'::int[] or %s = any(d.customers)) and
                (d.tags = '{NULL}'::int[] or d.tags && array(select producttag_id from product_tags where product_id = product.id)) order by COALESCE(d.percentage*product.price, d.amount) desc limit 1 ), product.discount_price, product.price), 2) price
                '''

        count_query = "select count(product.id), null as id, null as name, null as slug, 0 as filter from dataset product where in_tag != false and in_manufacturer != false "

        f_param = []
        if len(kwargs.get("manufacturer", [])) > 0:
            f_param += kwargs["manufacturer"]
        if len(kwargs.get("tag", [])) > 0:
            f_param += kwargs["tag"]
        f_param += list(params)
        f_where = list(where)
        f_full_query = _get_query(f_select, query, f_where, f_param, price=price)

        f_param += [facets.get('parent_category')]

        r = '''
            WITH _discounts AS ({1}), dataset AS ({0})
            {2}
            union all (select count(dataset.id), m.id as id, m.name, null as slug, 1 as filter from dataset join manufacturer m on (m.id = dataset.manufacturer_id)  where in_tag != false group by m.id order by m.name)
            union all (select count(dataset.id), t.id as id, t.name as name, t.slug as slug, 4 as filter from dataset join product_tags rel on (rel.product_id = dataset.id) join product_tag t on (t.id = rel.producttag_id) where in_manufacturer != false  group by t.id order by t.name)
            union all (SELECT count(dataset.id), c.id as id, c.name, c.slug, 2 as filter FROM category c JOIN category AS node on (c.tree_id = node.tree_id and node.lft > C .lft - 1 AND node.rght < C .rght + 1) JOIN dataset ON (dataset.category_id = node.id) WHERE c.parent_id {3} %s and in_tag != false and in_manufacturer != false  GROUP BY c.id ORDER BY c.slug)
        '''.format(f_full_query, DISCOUNT_QUERY, count_query, "is" if facets.get('parent_category') is None else "=")

        if facets.get('vehicle_level') is not None:
            r += "union all (%s )" % VEHICLE_TREE_FACET_QUERY[facets['vehicle_level'] + 1]
            if facets['vehicle_level'] >= 0:
                f_param.append(facets['parent_vehicle_branch'])
            if facets['vehicle_level'] >= 3:
                f_param.append(facets['motor_type'])
            if facets['vehicle_level'] >= 4:
                f_param.append(facets['fuel_type'])

        result['facets'] = dict((FACET_IDS[key], list(group) if key > 0 else list(group)[0]['count']) for key, group in
                                groupby(cursor.fetchall(r, f_param, 60 * 60 * 3), lambda x: x['filter']))

    if data:
        g = "GROUP BY product.id, manufacturer.id, category.id, image.id"
        if len(extra_group_by) > 0:
            g += "," + ", ".join(extra_group_by)
        data_query = _get_query(select, query, where, params, order_by=order_by, group_by=g, price=price, **kwargs)

        if limit is not None:
            params.append(limit)
            data_query += " limit %s "

        data_query += " offset %s "
        params.append(offset)
        products = cursor.fetchall(data_query, params)

        result['products'] = products

    return result


def _apply_price_filter(select, query, where, order_by, price, params=None, group_by=None):
    if price is not None and (price[0] or price[1]):
        p_where = []
        if price[0]:
            p_where.append("d.price >= %s")
            if params is not None:
                params.append(price[0])
        if price[1]:
            p_where.append("d.price <= %s")
            if params is not None:
                params.append(price[1])

        data_query = "SELECT * FROM (%s) d WHERE %s " % (
            select + query + (" where " + " and ".join(where) if len(where) > 0 else "") + (group_by or "") + (
                order_by or ""),
            " and ".join(p_where))
    else:
        data_query = select + query + (" where " + " and ".join(where) if len(where) > 0 else "") + (group_by or "") + (
            order_by or "")

    return data_query


def _get_query(select, query, where, params, price=None, order_by=None, tag=None, tags_slug=None, group_by=None,
               manufacturer=None,
               manufacturer_fulltext=None, raw=None):
    if tag:
        str = " product.id in (select rel.product_id from product_tags rel join product_tag tag on (rel.producttag_id = tag.id) where tag.id in (%s)) "
        if isinstance(tag, list):
            if len(tag) > 0:
                str %= ', '.join(list(map(lambda x: '%s', tag)))
                params += tag
                where.append(str)
        else:
            params.append(tag.id)
            where.append(str)

    if raw is not None:
        where.append(raw[0])
        params += raw[1]

    if tags_slug is not None:
        str = " product.id in (select rel.product_id from product_tags rel join product_tag tag on (rel.producttag_id = tag.id) where tag.slug in (%s)) "
        params.append(tags_slug)
        where.append(str)

    if manufacturer is not None:
        str = " product.manufacturer_id in (%s) "
        if isinstance(manufacturer, list):
            if len(manufacturer) > 0:
                str %= ', '.join(list(map(lambda x: '%s', manufacturer)))
                params += manufacturer
                where.append(str)
        else:
            params.append(manufacturer.id)
            where.append(str)

    if manufacturer_fulltext is not None:
        str = " product.manufacturer_id in (select id from manufacturer where to_tsvector('simple_unaccent', name) @@ plainto_tsquery('simple_unaccent', %s)) "
        params.append(manufacturer_fulltext)
        where.append(str)

    if order_by is not None:
        _order_by = []
        for _order in order_by:
            if not isinstance(_order, tuple):
                raise Exception("order by must be a tuple")
            if _order[1] not in ["discount_price", "product.name", "product.partner_code", "manufacturer.name",
                                 "category.name", "product.quantity>0", "image.image is not null"]:
                raise Exception("The sorting criteria is not valid.")
            _order_by.append(" %s %s" % (_order[1], "desc" if _order[0] == "-" else " asc "))
        _order_by = " order by " + ", ".join(_order_by)
    else:
        _order_by = None

    return _apply_price_filter(select, query, where, _order_by, price, params, group_by=group_by)


def get_product_price(product_ids, customer_id):
    cursor = helpers.Connection()
    return cursor.fetchall('''
        WITH _discounts AS (
            ''' + DISCOUNT_QUERY + '''
        )
        select product.id, product.price,

        round(COALESCE((select (CASE WHEN d.percentage IS NOT NULL THEN (100-d.percentage)/100.0*COALESCE(product.discount_price, product.price) ELSE COALESCE(product.discount_price, product.price)-d.amount END)
        from _discounts d WHERE
        (d.cats = '{NULL}'::int[] or product.category_id = any(d.cats)) and
        (d.customers = '{NULL}'::int[] or %s = any(d.customers)) and
        (d.tags = '{NULL}'::int[] or d.tags && array(select producttag_id from product_tags where product_id = product.id)) order by COALESCE(d.percentage*product.price, d.amount) desc limit 1 ), product.discount_price, product.price), 2) discount_price

        from product where product.id = any (%s)
    ''', [customer_id, product_ids if isinstance(product_ids, list) else [product_ids]])


def get_product(id, user_group=None, images=True):
    cursor = helpers.Connection()
    product = cursor.fetch('''
        WITH _discounts AS (
            ''' + DISCOUNT_QUERY + '''
        )
        select product.id, product.quantity, product.name, category.slug as category_slug, product.price, product.description, product.attr, product.minimum_order_amount, product.partner_code, product.grup_id,

        round(COALESCE((select (CASE WHEN d.percentage IS NOT NULL THEN (100-d.percentage)/100.0*COALESCE(product.discount_price, product.price) ELSE COALESCE(product.discount_price, product.price)-d.amount END)
        from _discounts d WHERE
        (d.cats = '{NULL}'::int[] or product.category_id = any(d.cats)) and
        (d.customers = '{NULL}'::int[] or %s = any(d.customers)) and
        (d.tags = '{NULL}'::int[] or d.tags && array(select producttag_id from product_tags where product_id = product.id)) order by COALESCE(d.percentage*product.price, d.amount) desc limit 1 ), product.discount_price, product.price), 2) discount_price,

        array(select tags.producttag_id as tags from product_tags tags where tags.product_id = product.id) as tags,
        manufacturer.id as manufacturer_id, manufacturer.name as manufacturer_name, manufacturer.image as manufacturer_image, manufacturer.is_original as manufacturer_is_original
        from product
        left join manufacturer on (product.manufacturer_id = manufacturer.id)
        left join category on (product.category_id = category.id)
        where product.active = true and product.id = %s''', [user_group, id])

    if product is None:
        return None

    if images:
        product['images'] = cursor.fetchall(
            "SELECT image.image FROM product_images image WHERE image.product_id = %s ORDER BY image.order ASC", [id])

    return product


def calculate_cargo_price(shipment_alternative, basket):
    '''for shipment in shipments:
        if shipment.price_by_kg is not None:
            shipment.weight_price = Decimal()
            shipment.total_weight = Decimal()
            for item in basket['basket']:
                if item['product']['weight'] is not None:
                    shipment.weight_price += item['product']['weight'] * shipment.price_by_kg
                    shipment.total_weight += item['product']['weight']'''
    max_cargo_price = 0
    for item in basket['basket']:
        if item['product'].cargo_price > max_cargo_price:
            max_cargo_price = item['product'].cargo_price

    if shipment_alternative.fixed_price < max_cargo_price:
        return max_cargo_price

    if shipment_alternative.minimum_price is None or basket.get("final_price") > shipment_alternative.minimum_price:
        return Decimal(0)
    else:
        return max_cargo_price


def get_basket(customer=None, items=None, fail_silently=False):
    cursor = helpers.Connection()
    total_price = Decimal()
    total_kdv = Decimal()
    total_discount_price = Decimal()
    errors = []

    if customer is not None:
        basket = cursor.fetchall("SELECT product_id, quantity, sase_code FROM customer_basket WHERE customer_id = %s",
                                 [customer.id])
        products = Product.objects.filter(customerbasket__customer=customer)

    elif items is not None:
        basket = items
        products = Product.objects.filter(id__in=[i['product_id'] for i in items])
    else:
        raise TypeError("this function only works with either customer or items arguments")

    for product in products:
        for b in basket:
            if b['product_id'] == product.id:
                if not product.active:
                    e = BasketItemNotExist(product)
                    if not fail_silently:
                        raise e
                    else:
                        errors.append(e)
                variable = get_custom_variable("depo-miktari-kontrolu")
                if product.quantity == 0 or (variable and product.quantity < b['quantity']):
                    e = BasketItemInsufficientStock(product)
                    if not fail_silently:
                        raise e
                    else:
                        errors.append(e)
                if product.minimum_order_amount > 0 and b['quantity'] % product.minimum_order_amount != 0:
                    b['quantity'] = product.minimum_order_amount
                b['product'] = product
                product.discount_price = product.get_price(customer)[1]
                total_price += b['quantity'] * product.price
                total_kdv += b['quantity'] * (product.discount_price / (100 + product.kdv)) * product.kdv
                total_discount_price += b['quantity'] * product.discount_price
                b['total_price'] = b['quantity'] * product.discount_price
                b['total_price_without_discount'] = b['quantity'] * product.price

    return {"basket": basket,
            "c": total_price,
            "final_price_without_kdv": total_discount_price - total_kdv,
            "total_price_without_kdv": total_price - total_kdv,
            "total_discount": total_price - total_discount_price,
            "final_price": total_discount_price,
            "kdv": total_kdv,
            "errors": errors,
            "total_basket": total_discount_price}


def get_vehicle_tree_from_product(product_id):
    cursor = helpers.Connection()
    vehicle_data = cursor.fetchall('''
    select brand.name as brand_name, brand.slug as brand_slug,
    model.name as model_name, model.slug as model_slug,
    model_type.name as model_type_name, model_type.slug as model_type_slug,
    motor.name as motor_type_name, motor.slug as motor_type_slug,
    fuel.name as fuel_type_name, fuel.slug as fuel_type_slug,
    r.begin_year, r.end_year
    from vehicle r
    join vehicle_motor_type motor on (motor.id = r.motor_type_id)
    join vehicle_fuel_type fuel on (fuel.id = r.fuel_type_id)
    join vehicle_tree model_type on (model_type.id = r.model_type_id)
    join vehicle_tree model on (model.id = r.model_id)
    join vehicle_tree brand on (brand.id = r.brand_id)
    where r.grup_id = (select grup_id from product where id = %s)
    ''', [product_id])

    vehicles = []
    for key, vehicle in enumerate(vehicle_data):
        model_type = reverse("shop_list_page") + "?v=" + vehicle['model_type_slug']
        motor_type = model_type + "&motor_type=" + vehicle['motor_type_slug']
        fuel_type = motor_type + "&fuel_type=" + vehicle['fuel_type_slug']
        vehicle = [
            {"url": reverse("shop_list_page") + "?v=" + vehicle['brand_slug'], "name": vehicle['brand_name'],
             "slug": vehicle['brand_slug']},
            {"url": reverse("shop_list_page") + "?v=" + vehicle['model_slug'], "name": vehicle['model_name'],
             "slug": vehicle['model_slug']},
            {"url": model_type, "name": vehicle['model_type_name'], "slug": vehicle['model_type_slug']},
            {"url": motor_type, "name": vehicle['motor_type_name'], "slug": vehicle['motor_type_slug']},
            {"url": fuel_type, "name": vehicle['fuel_type_name'], "slug": vehicle['fuel_type_slug']},
            {"url": fuel_type + "&begin_year=" + str(vehicle['begin_year']) + (
                "&end_year=" + str(vehicle['end_year']) if vehicle['end_year'] else ""),
             "name": "%s%s" % (
                 vehicle['begin_year'], "-" + str(vehicle['end_year']) if vehicle['end_year'] is not None else ""),
             "slug": "%s%s" % (
                 vehicle['begin_year'], "-" + str(vehicle['end_year']) if vehicle['end_year'] is not None else "")}
        ]

        vehicles.append(vehicle)
    return vehicles


def get_similar_products(product):
    cursor = helpers.Connection()
    products = cursor.fetchall('''SELECT sp.id, sp.quantity, sp.name, sp.price, category.id as category_id, sp.manufacturer_id, sp.discount_price,  sp.description, category.slug as category,
                array(select tags.producttag_id as tags from product_tags tags where tags.product_id = sp.id) as tags,
                (select image.image from product_images image where image.product_id = sp.id and image.order = 0 limit 1) as image
                 from product, product sp JOIN category ON sp.category_id = category.id
                 where sp.active = true and sp.id != product.id and sp.manufacturer_id = product.manufacturer_id and sp.category_id = product.category_id and product.id = %s limit 10''',
                               [product])
    return products


def get_motor_types(model_type_id):
    cursor = helpers.Connection()
    return cursor.fetchall('''select DISTINCT motor_type.id, motor_type.name, motor_type.slug, 'motor' as url from vehicle_motor_type motor_type
                           join vehicle on (vehicle.motor_type_id = motor_type.id) where vehicle.model_type_id = %s order by motor_type.name''',
                           [model_type_id])


def get_fuel_types(model_type_id, motor_type, by="id"):
    cursor = helpers.Connection()
    if by not in ["id", "slug"]:
        raise Exception("houston?")
    return cursor.fetchall('''select DISTINCT fuel_type.id, fuel_type.name, fuel_type.slug, 'fuel' as url from vehicle_motor_type motor_type
                           join vehicle on (vehicle.motor_type_id = motor_type.id)
                           join vehicle_fuel_type fuel_type on (vehicle.fuel_type_id = fuel_type.id)
                           where vehicle.model_type_id = %s and motor_type.''' + by + " = %s order by fuel_type.name",
                           [model_type_id, motor_type[by]])


def get_vehicle_years(model_type_id, motor_type, fuel_type, by="id"):
    cursor = helpers.Connection()
    if by not in ["id", "slug"]:
        raise Exception("houston?")

    return cursor.fetchall('''select vehicle.id, vehicle.begin_year || coalesce('-' || vehicle.end_year::text, '') as slug, vehicle.begin_year || coalesce('-' || vehicle.end_year::text, '') as name, 'vyear' as url from vehicle_motor_type motor_type
                           join vehicle on (vehicle.motor_type_id = motor_type.id)
                           join vehicle_fuel_type fuel_type on (vehicle.fuel_type_id = fuel_type.id)
                           where vehicle.model_type_id = %s and motor_type.''' + by + " = %s and fuel_type." + by + " = %s order by vehicle.begin_year",
                           [model_type_id, motor_type[by], fuel_type[by]])


def fetch_similar_products(user_id, product_id):
    return get_products_by(user_id, extra_where=[[
                                                     ' product.grup_id = (select grup_id from product where id = %s) and product.id != %s',
                                                     [product_id, product_id]], ],
                           order_by=(('-', 'product.quantity>0'),))['products']


@cache_func(60)
def get_category_not_related_vehicle():
    cursor = helpers.Connection()
    main_cats = cursor.fetchall(
        "select id, slug, name, image from category where vehicle_category = false and parent_id is null")

    sub_categories = {}
    for item in main_cats:
        sub_categories[item['id']] = cursor.fetchall(
            "select id, slug, name, image from category where vehicle_category = false and parent_id = %s",
            [item['id']])

    return main_cats, sub_categories