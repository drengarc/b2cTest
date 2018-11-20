from django.contrib.sitemaps import Sitemap, GenericSitemap
from django.core.urlresolvers import reverse
from simit.models import Page
from shop.models import Product, QuickSearchSuggestion
from vehicle.models import fill_quicksearch_suggestions


class ProductSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.5

    def items(self):
        return Product.objects.filter(active=True)

    def lastmod(self, obj):
        return obj.last_modified


class StaticViewSitemap(Sitemap):
    priority = 0.4
    changefreq = 'weekly'

    def items(self):
        return ['shop_page_tos', 'shop_page_about_us', 'shop_page_contact_us', 'shop_page_affiliates']

    def location(self, item):
        return reverse(item)


class ProductListSitemap(Sitemap):
    priority = 0.6
    changefreq = 'weekly'

    def items(self):
        return QuickSearchSuggestion.objects.all()

    def location(self, item):
        return item.target

sitemaps = {
    'urun': ProductSitemap,
    'urunliste': ProductListSitemap,
    'site': StaticViewSitemap,
    'sayfa': GenericSitemap(info_dict = {'queryset': Page.objects.all(), 'date_field': 'last_modified',}, priority=0.3)
}