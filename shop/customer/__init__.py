# -*- coding: utf-8 -*-

from django.db.models.signals import post_syncdb
from django.dispatch import receiver


@receiver(post_syncdb)
def create_variable(sender, **kwargs):
    from simit.models import CustomAreaCategory, CustomArea

    category, is_created = CustomAreaCategory.objects.get_or_create(name="Sistem")
    CustomArea.objects.get_or_create(category=category, slug="NOTIFICATION_EMAIL", name="Sipariş bilgilendirme e-posta adresi",
                              type=1,
                              description="Sipariş geldiğinde size e-posta yoluyla bilgilendirme mesajı gönderilir")