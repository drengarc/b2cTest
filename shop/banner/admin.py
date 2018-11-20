from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.utils import timezone
from filebrowser.functions import path_to_url, version_generator, url_to_path
from filebrowser.settings import ADMIN_THUMBNAIL
from shop.banner.models import Banner, BannerArea
from django.utils.translation import ugettext_lazy as _


class BannerStatusFilter(admin.SimpleListFilter):
    title = _('status')
    parameter_name = 'sent'

    def lookups(self, request, model_admin):
        return ('0', _('scheduled')), ('1', _('past'))

    def queryset(self, request, queryset):
        if self.value() is not None:
            if self.value() == '0':
                return queryset.filter(start_date__gte=timezone.now())
            elif self.value() == '1':
                return queryset.filter(end_date__lte=timezone.now())


class BannerAdmin(ModelAdmin):
    list_display = ('title', 'is_active', 'area', 'image_thumbnail')
    list_filter = ('area', BannerStatusFilter)
    search_fields = ('title',)

    def image_thumbnail(self, obj):
        if obj.image and obj.image.filetype == "Image":
            return '<img src="%s" />' % path_to_url(version_generator(url_to_path(unicode(obj.image)), ADMIN_THUMBNAIL))
        else:
            return ""

    image_thumbnail.allow_tags = True
    image_thumbnail.short_description = "Thumbnail"


class BannerAreaAdmin(ModelAdmin):
    search_fields = ('name',)
    list_display = ('name',)


admin.site.register(Banner, BannerAdmin)
admin.site.register(BannerArea)