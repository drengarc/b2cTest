from __future__ import unicode_literals

from django.db import models
from filebrowser.fields import FileBrowseField
from shop.models import Language
from django.utils.translation import ugettext_lazy as _


class BannerArea(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        db_table = 'banner_area'

    def __unicode__(self):
        return self.name


class Banner(models.Model):
    title = models.CharField(_('title'), max_length=45, blank=True, null=True)
    url = models.CharField(max_length=200)
    image = FileBrowseField(_('image'), max_length=200, directory="images/banners", extensions=[".jpg", ".jpeg", ".png", ".gif"], blank=True, null=True)
    html_text = models.TextField(_('description'), blank=True, null=True)
    end_date = models.DateTimeField(_('end date'), null=True, blank=True)
    start_date = models.DateTimeField(_('start date'), null=True, blank=True)
    date_added = models.DateTimeField(_('added date'), auto_now_add=True)
    is_active = models.BooleanField(_('is active'))
    area = models.ForeignKey(BannerArea)

    class Meta:
        db_table = 'banner'

    def __unicode__(self):
        return "%s" % self.title