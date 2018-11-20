# -*- coding: utf-8 -*-
from datetime import timedelta
from time import time as get_timestamp
import os
import random
import string

from celery.task import task
from django.core.urlresolvers import reverse
from django.template import Context, Template
from PIL import Image
import psycopg2
from django.conf import settings

from shop.customer.models import Order
from shop.models import Config
from shop.newsletter.models import Mail
from shop.utils.mail import send_html_mail


DAMGA_FILE_PATH = settings.PROJECT_PATH + "/scripts/damga/"

SAVE_PATH = "images/product"
SOURCE_DIRECTORY = "/home/" + os.path.basename(settings.PROJECT_PATH) + "/"


@task(name='moneyorder-notification')

def check_money_orders():
    pending_orders = Order.objects.raw('select "order".* from public."order" \
    join (select * from order_status order by time desc limit 1) order_status on (order_status.order_id = "order".id) \
    where order_status.order_status_type_id = 1 and order_status."time" > NOW() - \'1 day\'::INTERVAL')

    orders_url = settings.SITE_URL + reverse('shop_customer_orders')
    for order in pending_orders:
        message_url = settings.SITE_URL + reverse('shop_modules_messaging_new') + "?order=%s" % order.id

        mail = Mail.objects.get(slug="pending_money_order")
        context = Context({"orders_url": orders_url, "order_time": order.date_processed,
                           "message_url": settings.SITE_URL + message_url, 'customer': order.customer})
        title = Template(mail.title).render(context)
        content = Template(mail.content).render(context)

        send_html_mail(title, content,[order.customer.email])

    return "%s emails sent." % len(list(pending_orders))


@task(name='order-status-change-notification')
def order_status_change():
    conf, created = Config.objects.get_or_create(key='ORDER_STATUS_NOTIFICATION_CURSOR')

    cursor = int(conf.value) if conf.value else int(get_timestamp())

    orders = Order.objects.raw('select "order".id, "order_status".order_status_type_id as status, "order".cargo_no  \
        from "order" join (select DISTINCT ON (order_id) * from "order_status" order by order_id, id desc) \
        "order_status" on ("order_status".order_id = "order".id) \
        where "order_status".time > to_timestamp(%s)', [cursor])

    for order in orders:
        if order.status == 5 and order.cargo_no:
            mail = Mail.objects.get(slug="order_status_change")
            context = Context({"order": order})

            send_html_mail(Template(mail.title).render(context), Template(mail.content).render(context),
                           [order.customer.email])

    conf.value = str(int(get_timestamp()))
    conf.save()

    return "%s emails sent." % len(list(orders))


# @task(name='import_images')
def import_images(directory):
    result = []
    db = settings.DATABASES["default"]
    conn = psycopg2.connect(database=db['NAME'], user=db['USER'], password=db['PASSWORD'], host=db['HOST'],
                            port=db['PORT'])
    cur = conn.cursor()

    layer = Image.open(os.path.join(DAMGA_FILE_PATH, "damga.png")).rotate(45, expand=1)
    (layer_width, layer_height) = layer.size
    layer_small = layer.resize((layer_width / 2, layer_height / 2), Image.ANTIALIAS)

    # wtf security?
    main_directory = SOURCE_DIRECTORY + str(directory)
    result.append("%s klasoru inceleniyor" % main_directory)
    for filename in os.listdir(main_directory):
        path = os.path.join(main_directory, filename)
        if os.path.isfile(path):
            try:
                img = Image.open(path)
                (width, height) = img.size
                if width + 10 < layer_width or height + 10 < layer_height:
                    thumb = layer_small
                    pos = ((width - layer_width / 2) / 2, (height - layer_height / 2) / 2)
                else:
                    thumb = layer
                    pos = ((width - layer_width) / 2, (height - layer_height) / 2)
                img.paste(thumb, pos, mask=thumb)

                file_raw_name, file_extension = os.path.splitext(filename)
                rand_name = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(15))

                cur.execute(
                    'delete from product_images where product_id in (select id from product where lower(partner_code) = lower(%s))',
                    [file_raw_name])

                cur.execute(
                    'insert into product_images (product_id, image, "order", is_original) (select id, %s, 0, true from product where lower(partner_code) = lower(%s)) RETURNING id;',
                    [os.path.join(SAVE_PATH, rand_name + file_extension), file_raw_name])
                df = cur.fetchone()
                if df is not None:
                    img.save(os.path.join(settings.MEDIA_ROOT + SAVE_PATH, rand_name + file_extension), quality=80)
                    # os.remove(path)
                  #  result.append("%s moved" % path)
                else:
                    result.append("%s not found" % path)
                conn.commit()

            except Exception as e:
                result.append("HATA (%s): %s" % (e, path))
        else:
            result.append("directory %s" % path)

    cur.close()
    conn.close()
    return "<br>".join(result)


settings.CELERYBEAT_SCHEDULE['moneyorder-notification-per-hour'] = {
    'task': 'moneyorder-notification',
    'schedule': timedelta(seconds=30),
}

settings.CELERYBEAT_SCHEDULE['order-status-change-notification'] = {
    'task': 'order-status-change-notification',
    'schedule': timedelta(seconds=30),
}
