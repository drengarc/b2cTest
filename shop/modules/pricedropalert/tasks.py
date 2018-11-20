# -*- coding: utf-8 -*-
from datetime import timedelta

from celery.task import task
from django.contrib.auth import get_user_model
from django.template import Context, Template
from django.template.loader import get_template
from django.conf import settings

from shop.modules.pricedropalert.models import PriceDropAlertCustomer
from shop.newsletter.models import Mail
from shop.templatetags.shop_tags import get_product_link
from shop.utils.mail import send_html_mail
from vehicle import query


@task(name='pricedropalert-notification')
def notify_people():

    rows = query.get_products_by(1, extra_select=('auth_user.id as customer_id',), extra_join=(
        ('join module_pricedropalert_customer alert on (alert.product_id = product.id) join auth_user on (auth_user.id = alert.customer_id)', ), ),
                                 extra_where=[['alert.checkpoint_price > discount_price', ], ], extra_group_by=['auth_user.id'], limit=None)['products']

    for row in rows:
        customer = get_user_model().objects.get(id=row['customer_id'])
        mail = Mail.objects.get(slug="price_drop_alert_customer")
        context = Context(
            {"product": row, "customer": customer, "product_url": settings.SITE_URL + get_product_link(row)})
        title = Template(mail.title).render(context)
        content = Template(mail.content).render(context)
        send_html_mail(title, content, [customer.email])
        r = PriceDropAlertCustomer.objects.get(customer=customer, product_id=row['id'])
        r.checkpoint_price = row['discount_price']
        r.save()

    customer_count = len(rows)

    return "%s emails sent." % customer_count


settings.CELERYBEAT_SCHEDULE['pricedropalert-notify-people-per-hour'] = {
    'task': 'pricedropalert-notification',
    'schedule': timedelta(hours=1),
}