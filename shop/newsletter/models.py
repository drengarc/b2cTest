# coding: utf-8

from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from django.db import models

from shop.models import Language


MAILS = {}


class Newsletter(models.Model):
    title = models.CharField(_('title'), max_length=40)
    content = models.TextField(_('content'), )
    date_added = models.DateTimeField(_('added date'), auto_now_add=True)
    date_sent = models.DateTimeField(_('sent date'), null=True, blank=True)
    is_active = models.BooleanField(_('is active'), )
    language = models.ForeignKey(Language)

    class Meta:
        db_table = 'newsletter'
        verbose_name_plural = _("newsletters")
        verbose_name = _("newsletter")


from tinymce import widgets as tinymce_widgets


class HTMLField(models.TextField):
    def formfield(self, **kwargs):
        kwargs['widget'] = tinymce_widgets.TinyMCE(
            mce_attrs={'relative_urls': False, 'remove_script_host': False, 'document_base_url': "http://orsanparca.com/media/"})

        return super(HTMLField, self).formfield(**kwargs)


class Mail(models.Model):
    slug = models.SlugField(_('slug'), max_length=150, primary_key=True)
    title = models.CharField(_('title'), max_length=120)
    content = HTMLField()

    class Meta:
        db_table = 'mail'
        verbose_name_plural = _("mails")
        verbose_name = _("mail")