from django.db import connection
from django.db.models.signals import pre_save, post_syncdb, pre_syncdb
from django.dispatch import receiver

import shop.models
from shop.models import Category, Manufacturer


@receiver(post_syncdb, sender=shop.models)
def full_text_column_triggers_indexes(sender, **kwargs):
    cursor = connection.cursor()
    try:
        cursor.execute('''
        CREATE OR REPLACE FUNCTION product_fulltext(newrow product)
            RETURNS tsvector AS
            $$
            BEGIN
                RETURN ((select to_tsvector('simple_unaccent', COALESCE(newrow.name::text, '') ||' '|| COALESCE(newrow.partner_code, '') ||' '||COALESCE(regexp_replace(newrow.partner_code, '[^0-9A-Za-z]+', '', 'g')::text, '') ||' '||COALESCE(regexp_replace(newrow.partner_code, '[^0-9A-Za-z]+', '.', 'g')::text, '') || ' '||COALESCE(regexp_replace(newrow.partner_code, '[^0-9A-Za-z]+', ',', 'g')::text, '') ||' '|| COALESCE(category.name, '') ||' '|| COALESCE(manufacturer.name, ''))
                from category
                join manufacturer on (manufacturer.id = newrow.manufacturer_id)
                where category.id = newrow.category_id) ||
                COALESCE((select concat_tsvectors(fulltext) from vehicle v where (newrow.grup_id = v.grup_id) limit 100), '') ||
                (select concat_tsvectors(to_tsvector('simple_unaccent', oem_no)) from (select oem_no from ege.tb_kart_stok_oem where grup_id = newrow.grup_id limit 100) oem));
            END;
        $$ LANGUAGE plpgsql;

        CREATE OR REPLACE FUNCTION product_fulltext_trigger() RETURNS trigger AS $$
            begin
              new.fulltext := product_fulltext(new);
              return new;
            end
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER product_tsvectorupdate BEFORE INSERT OR UPDATE OF name, category_id, partner_code ON product FOR EACH ROW EXECUTE PROCEDURE product_fulltext_trigger();
        CREATE INDEX product_fulltext_idx ON product USING gin(fulltext);
        CREATE INDEX product_active_idx ON product(id) WHERE active;
        create index product_partner_code_number_idx on product (regexp_replace(lower(partner_code), '[^0-9A-Za-z]+', '', 'g'));
        CREATE INDEX category_parent_idx ON category(id) WHERE parent_id is NULL;

        CREATE INDEX product_partner_code_lower ON product (lower(product.partner_code));


        ''')
    except Exception, e:
        raise "Product full text functions couldn't created: %s" % e


@receiver(post_syncdb, sender=shop.models)
def full_text_procedures(sender, **kwargs):
    cursor = connection.cursor()
    try:
        cursor.execute('''
            CREATE EXTENSION IF NOT EXISTS unaccent;
            create extension pg_trgm;
            DROP TEXT SEARCH CONFIGURATION IF EXISTS simple_unaccent;
            CREATE TEXT SEARCH CONFIGURATION simple_unaccent ( COPY = simple );
            ALTER TEXT SEARCH CONFIGURATION simple_unaccent ALTER MAPPING FOR hword, hword_part, word WITH unaccent, simple, turkish_stem;

            CREATE OR REPLACE FUNCTION tsv_add(tsv1 tsvector, tsv2 tsvector)
            RETURNS tsvector AS
            $$
            BEGIN
                RETURN tsv1 || tsv2;
            END;
            $$ LANGUAGE plpgsql;

            DROP AGGREGATE IF EXISTS concat_tsvectors(tsvector);
            CREATE AGGREGATE concat_tsvectors (
                BASETYPE = tsvector,
                SFUNC = tsv_add,
                STYPE = tsvector,
                INITCOND = ''
            );

            CREATE INDEX shop_quicksearch_suggestion_similarity_idx ON shop_quicksearchsuggestion USING gist (suggestion gist_trgm_ops);
        ''')
    except Exception, e:
        raise "Product full text functions couldn't created: %s" % e


@receiver(pre_save, sender=Manufacturer)
def manufacturer_update_product_full_text(sender, instance, *args, **kwargs):
    if instance.id is None:
        return
    pre_instance = sender.objects.get(pk=instance.id)
    for field in ["name"]:
        if getattr(pre_instance, field) != getattr(instance, field):
            shop.product_fulltext_save("manufacturer_id = ", [instance.id])


@receiver(pre_save, sender=Category)
def category_update_product_full_text(sender, instance, *args, **kwargs):
    if instance.id is None:
        return
    pre_instance = sender.objects.get(pk=instance.id)
    for field in ["name"]:
        if getattr(pre_instance, field) != getattr(instance, field):
            shop.product_fulltext_save("category_id = ", [instance.id])