        # coding: utf-8

from __future__ import unicode_literals

from celery.task import task
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.db import models
from django.contrib.auth.models import AnonymousUser, AbstractUser, AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import ugettext as _
from django_hstore import hstore
import psycopg2
from mptt.fields import TreeForeignKey
from filebrowser.fields import FileBrowseField
from tinymce.models import HTMLField
from mptt.models import MPTTModel

from shop.fields import VectorField


GENDER_TYPE_CHOICES = (
    (1, _('male')),
    (2, _('female')),
    (3, _('hidden')),
)


class Country(models.Model):
    name = models.CharField(_('name'), max_length=40)
    iso_code = models.CharField(_('iso code'), max_length=3L, unique=True)

    class Meta:
        db_table = 'country'
        verbose_name_plural = _("countries")
        verbose_name = _('country')

    def __unicode__(self):
        return self.name


class City(models.Model):
    country = models.ForeignKey(Country)
    name = models.CharField(_('name'), max_length=32L)

    class Meta:
        db_table = 'city'
        verbose_name_plural = _("cities")
        verbose_name = _('city')

    def __unicode__(self):
        return self.name


class Ilce(models.Model):
    city = models.ForeignKey(City)
    name = models.CharField(_('name'), max_length=100)

    class Meta:
        db_table = 'ilce'
        verbose_name_plural = "ilçe"
        verbose_name = 'ilçeler'

    def __unicode__(self):
        return self.name


class Category(MPTTModel):
    name = models.CharField(_('name'), max_length=150)
    image = FileBrowseField(_('image'), max_length=200, directory="images/category",
                            extensions=[".jpg", ".jpeg", ".png", ".gif"], blank=True, null=True)
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', verbose_name=_('parent category'))
    attr = hstore.DictionaryField(blank=True, null=True)
    description = HTMLField(_('description'), blank=True, null=True)
    slug = models.SlugField(_('slug'), unique=True, blank=False, max_length=100,
                            help_text=_("Slug will be used when creating urls."))


    class Meta:
        db_table = 'category'
        verbose_name_plural = _("categories")
        verbose_name = _('category')

    def __unicode__(self):
        return self.name


class Language(models.Model):
    name = models.CharField(_('name'), max_length=32L)
    code = models.CharField(_('language code'), max_length=2L)
    image = FileBrowseField(_('image'), max_length=200, directory="images/language",
                            extensions=[".jpg", ".jpeg", ".png", ".gif"], blank=True, null=True)
    order = models.PositiveIntegerField(_('order'), )

    class Meta:
        db_table = 'language'
        verbose_name_plural = _("languages")
        verbose_name = _("language")

    def __unicode__(self):
        return self.name


class QuickSearchSuggestion(models.Model):
    suggestion = models.CharField(max_length=150, primary_key=True)
    target = models.CharField(max_length=150)


class Manufacturer(models.Model):
    name = models.CharField(_('name'), max_length=32L)
    image = FileBrowseField(_('image'), max_length=200, directory="images/manufacturers",
                            extensions=[".jpg", ".jpeg", ".png", ".gif"], blank=True, null=True)
    is_original = models.BooleanField(default=False)

    def __init__(self, *args, **kwargs):
        super(Manufacturer, self).__init__(*args, **kwargs)
        self._name = self.name

    class Meta:
        db_table = 'manufacturer'
        verbose_name_plural = _("manufacturers")
        verbose_name = _("manufacturer")

    def __unicode__(self):
        return self.name


class ProductImage(models.Model):
    product = models.ForeignKey("Product", related_name="images")
    image = FileBrowseField(_('image'), "image", max_length=200, directory="images/products",
                            extensions=[".jpg", ".png", ".gif"], blank=True, null=True)
    order = models.PositiveIntegerField(_('order'), )
    is_original = models.NullBooleanField(_('order'))

    class Meta:
        db_table = 'product_images'
        verbose_name_plural = _("product images")
        verbose_name = _("product image")
        unique_together = ('product', 'order')

    def __unicode__(self):
        return u""


class ProductPage(models.Model):
    product = models.ForeignKey("Product", primary_key=True)
    page_title = models.CharField(_('title'), max_length=255, blank=True)
    page_description = models.TextField(_('description'), blank=True)
    keywords = models.CharField(_('keywords'), max_length=255, blank=True)

    class Meta:
        db_table = 'product_page'
        verbose_name_plural = _("product pages")
        verbose_name = _("product page")


class Product(models.Model):
    quantity = models.IntegerField(_('quantity'), )
    name = models.CharField(_('name'), max_length=255)
    category = models.ForeignKey(Category)
    price = models.DecimalField(_('price'), max_digits=17, decimal_places=2)
    date_added = models.DateTimeField(_('added date'), auto_now_add=True)
    discount_price = models.DecimalField(_('discount price'), max_digits=17, decimal_places=2, blank=True, null=True)
    cargo_price = models.DecimalField(_('shipment price'), max_digits=17, decimal_places=2, blank=True, null=True)
    last_modified = models.DateTimeField(_('last modified'), auto_now=True)
    active = models.BooleanField(_('is active'), blank=False, default=True)
    manufacturer = models.ForeignKey(Manufacturer)
    description = HTMLField(_('description'), null=True, blank=True)
    fulltext = VectorField()
    tags = models.ManyToManyField("ProductTag", verbose_name=_('tags'), related_name="product_tags", blank=True,
                                  null=True, help_text=_('The tags for this product'))
    attr = hstore.DictionaryField(null=True, blank=True)

    objects = hstore.HStoreManager()
    sync_ege = models.BooleanField()
    ege_stok_id = models.IntegerField(null=True, blank=True)

    def __getitem__(self, item):
        return getattr(self, item)

    def get_active_raw_price(self):
        return self.discount_price if self.discount_price is not None else self.price

    def get_price(self, user):
        from vehicle.query import get_product_price

        p = get_product_price(self.id, user.id if isinstance(user, User) else user)[0]
        return p['price'], p['discount_price']

    def __setitem__(self, key, value):
        return setattr(self, key, value)

    class Meta:
        db_table = 'product'
        verbose_name_plural = _("products")
        verbose_name = _("product")

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('shop_product', args=(self.category.slug, slugify(self.name), self.id))


class ProductAttribute(models.Model):
    name = models.CharField(max_length=30)
    category = models.ForeignKey(Category)

    class Meta:
        db_table = "product_attribute"
        verbose_name_plural = _("product attributes")
        verbose_name = _("product attribute")


class ProductAttributeChoice(models.Model):
    attribute = models.ForeignKey(ProductAttribute, related_name="choices")
    choice = models.CharField(max_length=40)

    class Meta:
        db_table = "product_attribute_choice"
        verbose_name_plural = _("product attribute choices")
        verbose_name = _("product attribute choice")


'''
class ProductVariation(models.Model):
    product = models.ForeignKey(Product)

    class Meta:
        db_table = 'product_variation'
        verbose_name_plural = _("product variations")
        verbose_name = _("product variation")


class ProductVariationType(models.Model):
    name = models.CharField(_('name'), max_length=50, unique=True)

    class Meta:
        db_table = 'product_variation_type'
        verbose_name_plural = _("product variation types")
        verbose_name = _("product variation type")


class ProductVariationOption(models.Model):
    product_variation = models.ForeignKey(ProductVariation)
    variation = models.ForeignKey(ProductVariationType)
    value = models.TextField(_('value'), )

    class Meta:
        db_table = 'product_variation_option'
        verbose_name_plural = _("product variation options")
        verbose_name = _("product variation option")
'''


class ProductTag(models.Model):
    name = models.CharField(_('name'), max_length=32)
    slug = models.SlugField(_('slug'), max_length=150, unique=True)

    class Meta:
        db_table = 'product_tag'
        verbose_name_plural = _("product tags")
        verbose_name = _("product tag")

    def __unicode__(self):
        return self.name


class ConfigManager(models.Manager):
    def conf(self, key):
        v = cache.get("config-%s" % key, None, 600)
        if v is not None:
            return v
        try:
            v = super(ConfigManager, self).get(key=key).value
            cache.add("config-%s" % key, v)
            return v
        except ObjectDoesNotExist:
            return None


class Config(models.Model):
    key = models.CharField(_('key'), max_length=50, unique=True, blank=False, null=False)
    value = models.CharField(_('value'), max_length=100, blank=True, null=True)
    objects = ConfigManager()

    def __unicode__(self):
        return self.key

    class Meta:
        verbose_name_plural = _("configuration")
        verbose_name = _("configurations")


class UserManager(BaseUserManager):
    def _create_user(self, email, password,
                     is_staff, is_superuser, **extra_fields):
        """
        Creates and saves a User with the given username, email and password.
        """
        now = timezone.now()
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email,
                          is_staff=is_staff, is_active=True,
                          is_superuser=is_superuser, last_login=now,
                          date_joined=now, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        return self._create_user(email, password, False, False,
                                 **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        return self._create_user(email, password, True, True,
                                 **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_('email address'), unique=True, db_index=True)
    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=30, blank=True)
    is_staff = models.BooleanField(_('staff status'), default=False,
                                   help_text=_('Designates whether the user can log into this admin '
                                               'site.'))
    is_active = models.BooleanField(_('active'), default=True,
                                    help_text=_('Designates whether this user should be treated as '
                                                'active. Unselect this instead of deleting accounts.'))
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    gender = models.SmallIntegerField(_('gender'), blank=True, null=True, choices=GENDER_TYPE_CHOICES)
    default_shipment_address = models.ForeignKey('customer.CustomerAddress', null=True, blank=True,
                                                 related_name="default_shipment_address",
                                                 help_text="The default shipment address that the customer use")
    default_invoice_address = models.ForeignKey('customer.CustomerAddress', null=True, blank=True,
                                                related_name="default_invoice_address",
                                                help_text="The default invoice address that the customer use")
    phone = models.CharField(_('phone number'), max_length=50, blank=True, null=True)

    group = models.ForeignKey("customer.CustomerGroup", null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = UserManager()

    class Meta(AbstractUser.Meta):
        swappable = 'AUTH_USER_MODEL'
        db_table = 'auth_user'
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        "Returns the short name for the user."
        return self.first_name

    def email_user(self, subject, message, from_email=settings.DEFAULT_FROM_EMAIL):
        """
        Sends an email to this User.
        """
        send_mail(subject, message, from_email, [self.email])


class Synonym(models.Model):
    from_text = models.TextField()
    to_text = models.TextField()

    def __unicode__(self):
        return "%s -> %s" % (self.from_text, self.to_text)

    class Meta:
        verbose_name_plural = _("synonyms")
        verbose_name = _("synonym")


setattr(AnonymousUser, 'group_id', 1)


@task(time_limit=300)
def product_fulltext_save(where, arg, alias='default'):
    db = settings.DATABASES[alias]
    conn = psycopg2.connect(database=db['NAME'], user=db['USER'], password=db['PASSWORD'], host=db['HOST'],
                            port=db['PORT'])
    cursor = conn.cursor()
    cursor.execute(("update product set fulltext = product_fulltext(product) where " % where), arg)
    conn.commit()

    cursor.close()
    conn.close()