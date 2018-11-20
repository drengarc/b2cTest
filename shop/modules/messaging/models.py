# coding: utf-8

from django.contrib.auth import get_user_model
from django.db import models
from django.template import Template, Context
from django.utils.translation import ugettext as _
from shop.customer.models import Order
from django.db.models.signals import post_save
from django.conf import settings
from shop.utils.mail import send_html_mail


class MessageDepartment(models.Model):
    name = models.CharField(_('name'), max_length=150)

    class Meta:
        verbose_name = 'Message Department'

    def __unicode__(self):
        return self.name


class CustomerMessage(models.Model):
    customer = models.ForeignKey(get_user_model())
    topic = models.CharField(_('topic'), max_length=200)
    message = models.TextField(_('message'))
    top_message = models.ForeignKey("self", null=True, blank=True)
    unread = models.BooleanField(_('is unread'), default=True)
    time = models.DateTimeField(_('time'), auto_now=True)
    staff = models.ForeignKey(get_user_model(), null=True, blank=True, related_name="staff")
    order = models.ForeignKey(Order, blank=True, null=True)
    department = models.ForeignKey(MessageDepartment, blank=True, null=True)

    class Meta:
        verbose_name = 'Customer Message'


def send_notification(sender, instance, **kwargs):
    send_html_mail(u"Müşteriden yeni mesaj var.", Template(
        '<a href="{{ SITE_URL }}{% url "admin:messaging_customermessage_change" message.id %}">{{ SITE_URL }}{% url "admin:messaging_customermessage_change" message.id %}</a>.').render(Context({"message": instance, "SITE_URL": settings.SITE_URL})), [settings.NOTIFICATION_MAIL])

post_save.connect(send_notification, sender=CustomerMessage, dispatch_uid="send_admin_mail_messaging")