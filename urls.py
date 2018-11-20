from django.conf.urls import patterns, include, url
from django.conf import settings
from django.contrib import admin
from django.views.decorators.cache import cache_page
from shop.sitemap import sitemaps
from django.contrib.sitemaps import views as sitemap_views

admin.autodiscover()

urlpatterns = patterns('',
       url(r'^', include("shop.urls", app_name='shop')),
       url(r'^%s(?P<path>.*)$' % settings.MEDIA_URL[1:], 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
       (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT, 'show_indexes': True}),
       url(r'^sitemap\.xml$', cache_page(86400)(sitemap_views.index), {'sitemaps': sitemaps, 'sitemap_url_name': 'sitemaps'}),
       url(r'^sitemap-(?P<section>.+)\.xml.gz$', cache_page(86400)(sitemap_views.sitemap), {'sitemaps': sitemaps}, name='sitemaps'),
       url(r'^doc/', include('django.contrib.admindocs.urls'), name="admin_docs"),
       url(r'^tinymce/', include('tinymce.urls')),
       url(r'^administratorPage/filebrowser/', include("filebrowser.urls")),
       url(r'^admin_tools/', include("admin_tools.urls"), name="django_admin_tools_url"),
       url(r'^administratorPage/', include(admin.site.urls), name="django_admin_url"),
)

handler404 = 'shop.views.handler404'
handler500 = 'shop.views.handler500'
handler403 = 'shop.views.handler403'
handler400 = 'shop.views.handler400'