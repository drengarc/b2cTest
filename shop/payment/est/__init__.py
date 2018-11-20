# -*- coding: utf-8 -*-

from django.db.models.signals import post_syncdb
from django.dispatch import receiver


@receiver(post_syncdb)
def create_variable(sender, **kwargs):
    from simit.models import CustomAreaCategory, CustomArea

    category, _ = CustomAreaCategory.objects.get_or_create(name="Alışveriş")
    CustomArea.objects.get_or_create(category=category, slug="ACTIVATE_3D", name="3D ile ödeme", type=5,
                                     description="3D ile ödemeyi aktifleştir")


