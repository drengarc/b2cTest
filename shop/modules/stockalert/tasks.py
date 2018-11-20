# coding: utf-8

from datetime import timedelta

from celery.task import task
from django.contrib.auth import get_user_model
from django.template import Context, Template
from django.template.loader import get_template
from settings_local import DEFAULT_FROM_EMAIL, SITE_URL
from django.conf import settings

from shop.modules.stockalert.models import StockAlertCustomer
from shop.newsletter.models import Mail
from shop.templatetags.shop_tags import get_product_link
from shop.utils.mail import send_html_mail
from vehicle import query


@task(name='stockalert-notification')
def notify_people():
    rows = query.get_products_by(1, extra_select=('alert.customer_id', ), in_stock=True, extra_join=(
        ('join module_stockalert_customer alert on (alert.product_id = product.id)', ), ), extra_group_by=['alert.customer_id'], limit=None)['products']

    email_count = len(rows)

    for row in rows:
        customer = get_user_model().objects.get(id=row['customer_id'])
        mail = Mail.objects.get(slug="stock_alert_customer")
        context = Context(
            {"product": row, "customer": customer, "product_url": settings.SITE_URL + get_product_link(row)})
        title = Template(mail.title).render(context)
        content = Template(mail.content).render(context)
        send_html_mail(title, content, [customer.email])
        r = StockAlertCustomer.objects.get(customer=customer, product_id=row['id'])
        r.delete()

    customer_count = len(rows)

    return "%s email sent. %s them were customer emails." % (customer_count+email_count, email_count)

settings.CELERYBEAT_SCHEDULE['stockalert-notify-people-per-hour'] = {
    'task': 'stockalert-notification',
    'schedule': timedelta(hours=1),
}