from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db import models, connection
from django.db.models import Q
from django.db.models.signals import post_syncdb, pre_save
from django.dispatch import receiver
from django.db import transaction
from django.utils.translation import ugettext_lazy as _
from filebrowser.fields import FileBrowseField
from tinymce.models import HTMLField
from mptt.fields import TreeForeignKey

from shop import helpers
from shop.fields import VectorField
from shop.models import Category, Product, product_fulltext_save, Manufacturer, QuickSearchSuggestion


Product.add_to_class('minimum_order_amount', models.PositiveSmallIntegerField())
Product.add_to_class('grup_id', models.IntegerField(null=True, blank=True))
Product.add_to_class('kdv', models.IntegerField())
Product.add_to_class('toptanci', models.ForeignKey("vehicle.Toptanci", null=True, blank=True))
Category.add_to_class('vehicle_category', models.BooleanField(default=False))
Product.add_to_class('volume', models.DecimalField(_('volume'), decimal_places=2, max_digits=17, blank=True, null=True))
Product.add_to_class('weight', models.DecimalField(_('weight'), max_digits=9, blank=True, null=True, decimal_places=2))
Product.add_to_class('partner_code', models.CharField(_('partner code'), max_length=50, blank=True, null=True))


class Currency(models.Model):
    name = models.CharField(max_length=70)
    code = models.CharField(max_length=10)
    symbol = models.CharField(max_length=1)
    parity = models.DecimalField(max_digits=17, decimal_places=3)


class Vehicle(models.Model):
    brand = models.ForeignKey("VehicleTree", limit_choices_to=Q(level=0), related_name="brand")
    model = models.ForeignKey("VehicleTree", limit_choices_to=Q(level=1), related_name="model")
    model_type = models.ForeignKey("VehicleTree", limit_choices_to=Q(level=2), related_name="model_type")
    motor_type = models.ForeignKey("MotorType")
    fuel_type = models.ForeignKey("FuelType")
    begin_year = models.IntegerField()
    end_year = models.IntegerField(null=True, blank=True)
    fulltext = VectorField()
    grup_id = models.IntegerField(_('group id'), blank=True, null=True)

    class Meta:
        db_table = 'vehicle'
        verbose_name_plural = _("vehicle")
        verbose_name = _("vehicles")
        unique_together = ('brand', 'model', 'model_type', 'motor_type', 'fuel_type', 'begin_year', 'end_year')

    def clean(self):
        if self.end_year is not None and self.begin_year > self.end_year:
            raise ValidationError(_('End year cannot be higher than begin year.'))

    def __unicode__(self):
        return "%s %s %s %s %s %s-%s" % (
            self.model_type.parent.parent.name, self.model_type.parent.name,
            self.model_type.name,
            self.motor_type.name, self.fuel_type.name, self.begin_year,
            self.end_year if self.end_year else _('present'))


class VehicleTree(models.Model):
    name = models.CharField(max_length=150)
    image = FileBrowseField(_('image'), max_length=200, directory="images/vehicle",
                            extensions=[".jpg", ".jpeg", ".png", ".gif"], blank=True, null=True)
    slug = models.SlugField(_('slug'), unique=True, blank=False, max_length=150,
                            help_text=_("Slug will be used when creating urls."))
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', verbose_name=_('parent category'))
    level = models.PositiveSmallIntegerField()
    description = HTMLField(_('description'), blank=True, null=True)

    class Meta:
        db_table = 'vehicle_tree'

    def save(self, *args, **kwargs):
        parent = self.parent
        if self.parent is not None:
            self.slug = "%s-%s" % (parent.slug, self.slug)
        return super(VehicleTree, self).save(*args, **kwargs)

    def get_ancestors(self, include_self=True):
        path = []
        if self.level == 1:
            path.append(self.parent)
        elif self.level == 2:
            path.append(self.parent.parent)
            path.append(self.parent)
        if include_self:
            path.append(self)
        return path

    def url(self):
        return 'v'

    def __unicode__(self):
        return self.name


class VehicleBrandManager(models.Manager):
    def get_query_set(self):
        return super(VehicleBrandManager, self).get_query_set().filter(level=0)


class VehicleBrand(VehicleTree):
    objects = VehicleBrandManager()
    def save(self, *args, **kwargs):
        super(VehicleBrand, self).save(*args, **kwargs)

    class Meta:
        proxy = True


class VehicleOtherManager(models.Manager):
    def get_query_set(self):
        return super(VehicleOtherManager, self).get_query_set().filter(vehicle_category=True)


class VehicleOther(Category):
    objects = VehicleOtherManager()

    def save(self, *args, **kwargs):
        self.vehicle_category = True
        super(VehicleOther, self).save(*args, **kwargs)

    class Meta:
        proxy = True


class CustomCategoryManager(models.Manager):
    def get_query_set(self):
        return super(CustomCategoryManager, self).get_query_set().filter(vehicle_category=False)


class CustomCategory(Category):
    objects = CustomCategoryManager()

    def save(self, *args, **kwargs):
        self.vehicle_category = False
        super(CustomCategory, self).save(*args, **kwargs)

    class Meta:
        proxy = True


class VehicleBrandModelManager(models.Manager):
    def get_query_set(self):
        return super(VehicleBrandModelManager, self).get_query_set().filter(level=1)

class VehicleBrandModel(VehicleTree):
    objects = VehicleBrandModelManager()
    def save(self, *args, **kwargs):
        super(VehicleBrandModel, self).save(*args, **kwargs)

    class Meta:
        proxy = True
        verbose_name = _('brand model')
        verbose_name_plural = _('brand models')


class VehicleBrandModelTypeManager(models.Manager):
    def get_query_set(self):
        return super(VehicleBrandModelTypeManager, self).get_query_set().filter(level=2)


class VehicleBrandModelType(VehicleTree):
    objects = VehicleBrandModelTypeManager()

    def save(self, *args, **kwargs):
        super(VehicleBrandModelType, self).save(*args, **kwargs)

    class Meta:
        proxy = True
        verbose_name = _('model type')
        verbose_name_plural = _('model types')


class TaxRate(models.Model):
    category = models.ForeignKey(Category)
    tax_rate = models.DecimalField(_('tax rate'), max_digits=9, decimal_places=2)
    date_added = models.DateTimeField(_('added date'), auto_now_add=True)

    class Meta:
        db_table = 'tax_rate'
        verbose_name_plural = _("tax rates")
        verbose_name = _("tax rate")

    def __unicode__(self):
        return "%s - (%s %s)", (self.category, self.tax_rate, self.verbose_name)


class FuelType(models.Model):
    name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(_('slug'), unique=True, blank=False, max_length=150,
                            help_text=_("Slug will be used when creating urls."))

    class Meta:
        db_table = 'vehicle_fuel_type'
        verbose_name_plural = _("fuel types")
        verbose_name = _("fuel type")

    def __unicode__(self):
        return self.name


class MotorType(models.Model):
    name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(_('slug'), unique=True, blank=False, max_length=150,
                            help_text=_("Slug will be used when creating urls."))

    class Meta:
        db_table = 'vehicle_motor_type'
        verbose_name_plural = _("motor types")
        verbose_name = _("motor type")

    def __unicode__(self):
        return self.name


class ProductOriginal(models.Model):
    product = models.ForeignKey(Product)
    oem_no = models.CharField(_('oem number'), max_length=32L)
    oem_no_original = models.CharField(_('original oem number'), max_length=32L)
    brand = models.ForeignKey(VehicleTree, limit_choices_to={"level": 0})

    class Meta:
        db_table = 'product_original'
        verbose_name_plural = _('original products')
        verbose_name = _('original product')

    def __unicode__(self):
        return self.oem_no_original


class Toptanci(models.Model):
    name = models.CharField(max_length=150)


class KarMarji(models.Model):
    toptanci = models.ForeignKey(Toptanci)
    manufacturer = models.ForeignKey(Manufacturer)
    value = models.DecimalField(decimal_places=2, max_digits=2)

    class Meta:
        db_table = 'vehicle_kar_marji'


class FirmParameter(models.Model):
    name = models.CharField(_('name'), max_length=32L)
    redirect_to_basket = models.BooleanField(_('redirect to basket'), default=True, help_text=_(
        'Whether the user who added to basket an item will be redirected to basket page or not.'))
    min_price_for_cargo = models.DecimalField(_('minimum order price for shipment'), max_digits=17, decimal_places=2)

    class Meta:
        db_table = 'firm_parameter'
        verbose_name_plural = _('firm parameters')
        verbose_name = _('firm parameter')

    def __unicode__(self):
        return self.name


@receiver(post_syncdb, sender=Vehicle)
def full_text_column_triggers_indexes(sender, **kwargs):
    cursor = connection.cursor()
    cursor.execute('''
    CREATE OR REPLACE FUNCTION vehicle_fulltext(newrow vehicle)
        RETURNS tsvector AS
        $$
        BEGIN
            RETURN (select to_tsvector('simple_unaccent', COALESCE(new.begin_year::text, '') ||' '|| COALESCE(new.end_year::text, '') ||' '|| COALESCE(motor.name, '') ||' '|| COALESCE(fuel.name, '') ||' '|| COALESCE(brand.name, '') ||' '|| COALESCE(model.name, '') ||' '|| COALESCE(modeltype.name, ''))
              from vehicle_tree modeltype
              join vehicle_tree model on (model.id = modeltype.parent_id)
              join vehicle_tree brand on (brand.id = model.parent_id)
              join vehicle_motor_type motor on (new.motor_type_id = motor.id)
              join vehicle_fuel_type fuel on (new.fuel_type_id = fuel.id)
              where modeltype.id = new.model_type_id);
        END;
    $$ LANGUAGE plpgsql;

    CREATE OR REPLACE FUNCTION vehicle_fulltext_trigger() RETURNS trigger AS $$
        begin
          new.fulltext := vehicle_fulltext(new);

          return new;
        end
    $$ LANGUAGE plpgsql;

    CREATE TRIGGER vehicle_tsvectorupdate BEFORE INSERT OR UPDATE OF begin_year, end_year, model_type_id, motor_type_id, fuel_type_id ON vehicle FOR EACH ROW EXECUTE PROCEDURE vehicle_fulltext_trigger();
    CREATE INDEX vehicle_fulltext_idx ON vehicle USING gin(fulltext);

    CREATE OR REPLACE FUNCTION product_fulltext(newrow product)
        RETURNS tsvector AS
        $$
        BEGIN
            RETURN ((select to_tsvector('simple_unaccent', COALESCE(newrow.name::text, '') ||' '|| COALESCE(newrow.partner_code::text, '') ||' '|| COALESCE(category.name, '') ||' '|| COALESCE(manufacturer.name, ''))
            from category
            join manufacturer on (manufacturer.id = newrow.manufacturer_id)
            where category.id = newrow.category_id) ||
            (select concat_tsvectors(fulltext) from vehicle v join product_vehicle rel on (rel.vehicle_id = v.id) where rel.product_id = newrow.id) ||
            (select concat_tsvectors(to_tsvector('simple_unaccent', (oem_no ||' '|| oem_no_original))) from product_original p where p.product_id = newrow.id));
        END;
    $$ LANGUAGE plpgsql;


    ''')


@receiver(post_syncdb, sender=FuelType)
def full_text_column_triggers_indexes(sender, **kwargs):
    cursor = connection.cursor()
    cursor.execute('''
    create index fuel_type_name_fulltext_idx on vehicle_fuel_type USING gin(to_tsvector('simple_unaccent', name));
    ''')


@receiver(post_syncdb, sender=MotorType)
def full_text_column_triggers_indexes(sender, **kwargs):
    cursor = connection.cursor()
    cursor.execute('''
    create index motor_type_name_fulltext_idx on vehicle_motor_type USING gin(to_tsvector('simple_unaccent', name));
    ''')


@receiver(post_syncdb, sender=VehicleTree)
def full_text_column_triggers_indexes(sender, **kwargs):
    cursor = connection.cursor()
    cursor.execute('''
    create index vehicle_name_fulltext_idx on vehicle_tree USING gin(to_tsvector('simple_unaccent', name));
    ''')


@receiver(pre_save, sender=Vehicle)
def vehicle_update_product_full_text(sender, instance, *args, **kwargs):
    if instance.id is None or kwargs.get('raw'):
        return
    pre_instance = sender.objects.get(pk=instance.id)
    for field in sender._meta.fields:
        if getattr(pre_instance, field) != getattr(instance, field):
            product_fulltext_save("id in (select product_id from product_vehicle where vehicle_id = %s)", [instance.id])


@receiver(pre_save, sender=ProductOriginal)
def oemcode_update_product_full_text(sender, instance, *args, **kwargs):
    if instance.id is None or kwargs.get('raw'):
        return
    pre_instance = sender.objects.get(pk=instance.id)
    for field in ["oem_no", "oem_no_original"]:
        if getattr(pre_instance, field) != getattr(instance, field):
            product_fulltext_save("id in (select product_id from product_original where id = %s)", [instance.id])


@receiver(pre_save, sender=VehicleTree)
def vehicletree_update_product_full_text(sender, instance, *args, **kwargs):
    if instance.id is None or kwargs.get('raw'):
        return
    pre_instance = sender.objects.get(pk=instance.id)
    for field in ["name"]:
        if getattr(pre_instance, field) != getattr(instance, field):
            ids = [v.id for v in instance.get_ancestors(include_self=True) if v.level == 2]
            product_fulltext_save(
                "id in (select product_id from product_vehicle join vehicle on (vehicle_id = vehicle.id) where model_type_id in (%s))" % ",".join(
                    ids), [instance.id])


@receiver(pre_save, sender=FuelType)
def fueltype_update_product_full_text(sender, instance, *args, **kwargs):
    if instance.id is None or kwargs.get('raw'):
        return
    pre_instance = sender.objects.get(pk=instance.id)
    for field in ["name"]:
        if getattr(pre_instance, field) != getattr(instance, field):
            product_fulltext_save(
                "id in (select product_id from product_vehicle join vehicle on (vehicle_id = vehicle.id) where vehicle.fuel_type_id = %s)",
                [instance.id])


@receiver(pre_save, sender=MotorType)
def motortype_update_product_full_text(sender, instance, *args, **kwargs):
    if instance.id is None or kwargs.get('raw'):
        return
    pre_instance = sender.objects.get(pk=instance.id)
    for field in ["name"]:
        if getattr(pre_instance, field) != getattr(instance, field):
            product_fulltext_save(
                "id in (select product_id from product_vehicle join vehicle on (vehicle_id = vehicle.id) where vehicle.motor_type_id = %s)",
                [instance.id])


# @task
def fill_quicksearch_suggestions():
    cursor = helpers.Connection()

    vehicles = cursor.fetchall("select DISTINCT ON (category_id, brand_id, model_id) \
    lower(category.name) as category_name, category.slug as category_slug, \
    lower(brand.name) as brand_name, brand.slug as brand_slug, \
    lower(model.name) as model_name, model.slug as model_slug \
    from product join vehicle on (vehicle.grup_id = product.grup_id) \
    join category on (category.id = category_id) join vehicle_tree brand on (brand.id = brand_id) \
    join vehicle_tree model on (model.id = model_id)")

    manufacturers = cursor.fetchall("select DISTINCT ON (category_id, manufacturer_id) \
    lower(category.name) as category_name, category.slug as category_slug, \
    lower(manufacturer.name) as manufacturer_name, manufacturer.id as manufacturer_id \
    from product join category on (category.id = category_id) \
    join manufacturer on (manufacturer.id = manufacturer_id)")

    with transaction.atomic():
        QuickSearchSuggestion.objects.all().delete()

        saved_categories = set()
        for vehicle in vehicles:
            name = "%s %s" % (vehicle['brand_name'], vehicle['model_name'])
            QuickSearchSuggestion(suggestion=name,
                                  target=reverse('shop_vehicle_page', args=(vehicle['model_slug'],))).save()
            QuickSearchSuggestion(suggestion="%s %s" % (vehicle['category_name'], name),
                                  target=reverse('shop_list_page') + "?c=%s&v=%s" % (
                                      vehicle['category_slug'], vehicle['model_slug'])).save()
            if vehicle['category_slug'] not in saved_categories:
                saved_categories.add(vehicle['category_slug'])
                QuickSearchSuggestion(suggestion=vehicle['category_name'],
                                      target=reverse('shop_category_page', args=(vehicle['category_slug'],))).save()

        for manufacturer in manufacturers:
            name = "%s %s" % (manufacturer['manufacturer_name'], manufacturer['category_name'])
            QuickSearchSuggestion(suggestion=name, target=reverse('shop_list_page') + (
                "?c=%s&br=%s" % (manufacturer['category_slug'], manufacturer['manufacturer_id']))).save()
            QuickSearchSuggestion(suggestion=manufacturer['manufacturer_name'],
                                  target=reverse('shop_list_page') + (
                                      "?br=%s" % manufacturer['manufacturer_id'])).save()
            if vehicle['category_slug'] not in saved_categories:
                saved_categories.add(manufacturer['category_slug'])
                QuickSearchSuggestion(suggestion=manufacturer['category_name'],
                                      target=reverse('shop_category_page',
                                                     args=(manufacturer['category_slug'],))).save()