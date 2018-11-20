CREATE OR REPLACE FUNCTION PUBLIC.convert_to_integer(v_input TEXT)
RETURNS INTEGER
LANGUAGE plpgsql
AS $function$
DECLARE v_int_value INTEGER DEFAULT NULL;
BEGIN
  BEGIN
    v_int_value := v_input:: INTEGER;
    EXCEPTION WHEN OTHERS THEN
RETURN NULL;
END;
RETURN v_int_value;
END;
$function$


CREATE OR REPLACE FUNCTION PUBLIC.convert_to_integer(v_input VARCHAR)
RETURNS INTEGER
LANGUAGE plpgsql
AS $function$
DECLARE v_int_value INTEGER DEFAULT NULL;
BEGIN
  BEGIN
    v_int_value := v_input:: INTEGER;
    EXCEPTION WHEN OTHERS THEN
RETURN NULL;
END;
RETURN v_int_value;
END;
$function$


CREATE OR REPLACE FUNCTION PUBLIC.ege_sync()
RETURNS boolean
LANGUAGE plpgsql
AS $function$
DECLARE ege_product record;
BEGIN

insert into public.vehicle_tree("slug", "name", "description", "parent_id", "level")
select  distinct on (slug) slugify(marka) as slug, initcap(marka), '', null, 0 as level
from ege.tb_kart_stok_araclar ege_arac
where marka != '' and slugify(marka) not in (select slug from vehicle_tree);
RAISE NOTICE 'vehicle brands imported';

insert into public.vehicle_tree("slug", "name", "description", "parent_id", "level")
select distinct on (slug) slugify(ortak_adi) as slug, initcap(ortak_adi), null as description, brand.id as parent_id, 1 as level
from ege.tb_kart_stok_araclar ege_arac
JOIN public.vehicle_tree brand ON (brand.level = 0 and brand.slug = slugify(ege_arac.marka))
where ortak_adi!='' and slugify(ortak_adi) not in (select slug from vehicle_tree);
RAISE NOTICE 'vehicle models imported';

insert into public.vehicle_tree("slug", "name", "description", "parent_id", "level")
select distinct on (slug) slugify(model) as slug, initcap(model), null as description, model.id as parent_id, 2 as level
from ege.tb_kart_stok_araclar ege_arac
JOIN public.vehicle_tree model ON (model.level = 1 and model.slug = slugify(ege_arac.ortak_adi))
where model!='' and slugify(model) not in (select slug from vehicle_tree);
RAISE NOTICE 'vehicle model types imported';

insert into public.vehicle_motor_type("slug", "name")
select distinct on (slug) slugify(motor_tipi) as slug, initcap(motor_tipi)
from ege.tb_kart_stok_araclar ege_arac
where slugify(motor_tipi) not in (select slug from vehicle_motor_type);
RAISE NOTICE 'vehicle motor types imported';

insert into public.vehicle_fuel_type("slug","name")
select distinct on (slug) slugify(yakit_tipi) as slug, initcap(yakit_tipi)
from ege.tb_kart_stok_araclar ege_arac
where slugify(yakit_tipi) not in (select slug from vehicle_fuel_type);
RAISE NOTICE 'vehicle fuel types imported';

insert into public.vehicle("brand_id", "model_id", "model_type_id","motor_type_id", "fuel_type_id","begin_year", "end_year", "grup_id")
select DISTINCT ON (model_type.id, motor.id, fuel.id, ege_arac.baslangic_yili, ege_arac.bitis_yili)
brand.id, model.id, model_type.id, motor.id, fuel.id, ege.convert_to_integer(ege_arac.baslangic_yili), ege.convert_to_integer(ege_arac.bitis_yili), ege_arac.grup_id
from ege.tb_kart_stok_araclar ege_arac
JOIN public.vehicle_tree model_type ON (model_type.level = 2 and model_type.slug = slugify(ege_arac.model))
JOIN public.vehicle_tree model ON (model.level = 1 and model.id = model_type.parent_id)
JOIN public.vehicle_tree brand ON (brand.level = 0 and brand.id = model.parent_id)
JOIN public.vehicle_motor_type motor ON (motor.slug = slugify(ege_arac.motor_tipi))
JOIN public.vehicle_fuel_type fuel ON (fuel.slug = slugify(ege_arac.yakit_tipi))
where model != '' and motor_tipi != '' and yakit_tipi != '' and ege.convert_to_integer(ege_arac.baslangic_yili) is not null
and row(model_type.id, motor.id, fuel.id, ege.convert_to_integer(ege_arac.baslangic_yili), ege.convert_to_integer(ege_arac.bitis_yili))
not in (select model_type_id, motor_type_id, fuel_type_id, begin_year, end_year from public.vehicle);
RAISE NOTICE 'vehicles imported';

PERFORM
 create_category(initcap(kirilim1), slugify(kirilim1), null)
from ege.tb_kart_stok stok
left join category cat_one on (slugify(kirilim1)=cat_one.slug)
where kirilim1 != '' and kirilim1 is not null and cat_one.id is null group by kirilim1;
RAISE NOTICE 'first level categories imported';


PERFORM
 create_category(initcap(kirilim2), slugify(kirilim1 || ' ' ||kirilim2), (select id from category where slug = slugify(kirilim1)))
from ege.tb_kart_stok stok
left join category cat_two on (slugify(kirilim1 || ' ' ||kirilim2)=cat_two.slug)
where kirilim2 != '' and kirilim2 is not null and cat_two.id is null group by kirilim1, kirilim2;
RAISE NOTICE 'second level categories imported';

PERFORM
create_category(initcap(kirilim3), COALESCE(substring(slugify(kirilim1 || ' ' ||kirilim2|| ' ' ||kirilim3) FROM '.{100}$'), slugify(kirilim1 || ' ' ||kirilim2|| ' ' ||kirilim3)), (select id from category where slug = slugify(kirilim1 || ' ' || kirilim2) ))
from ege.tb_kart_stok stok
left join category cat_three on (COALESCE(substring(slugify(kirilim1 || ' ' ||kirilim2|| ' ' ||kirilim3) FROM '.{100}$'), slugify(kirilim1 || ' ' ||kirilim2|| ' ' ||kirilim3)) = cat_three.slug)
where kirilim3 != '' and kirilim3 is not null and cat_three.id is null group by kirilim1, kirilim2, kirilim3;
RAISE NOTICE 'third level categories imported';


insert into manufacturer (name)
select initcap(stok.tedarikci)
from ege.tb_kart_stok stok
left join manufacturer on (initcap(stok.tedarikci)=manufacturer.name)
where manufacturer.id is null and stok.tedarikci!='' group by stok.tedarikci;
RAISE NOTICE 'manufacturers imported';

create temporary table ege_product ON COMMIT DROP as
with default_kar_marji AS (SELECT value::numeric FROM shop_config WHERE key = 'DEFAULT_KAR_MARJI')
select
	stok.stok_kodu,
	manufacturer. ID AS manufacturer,
	category. ID AS category,
	stok.urun_adi,
	stok.grup_id,
	COALESCE (kar_marji.value, (SELECT value FROM default_kar_marji)) AS urun_kar_marji,
	vehicle_currency. ID AS currency_id,
	liste_currency. ID AS liste_currency_id,
    vehicle_currency.parity,
	CASE WHEN fiyat.fiyat is null THEN NULL ELSE liste_currency.parity END AS liste_parity,
    fiyat.yeni_urun,
    fiyat.kdv,
	COALESCE(fiyat.fiyat, fiyat.indirimli_fiyat) as price,
	CASE WHEN fiyat.fiyat IS NULL THEN null ELSE fiyat.indirimli_fiyat END as discount_price,
    fiyat.net_fiyat_aktifmi AS kampanyali_urun,
    fiyat.minumum_adet AS minimum_order_amount,
    fiyat.depo AS quantity,
    fiyat.liste_fiyati,
	product.id as product_id
	FROM
    ege.tb_kart_stok stok
	JOIN (
		select distinct on (sira.siralama, fiyat.ege_stok_id) fiyat.kdv, fiyat.liste_fiyati_doviz_id, fiyat.net_fiyat_aktifmi = 'A' as net_fiyat_aktifmi, fiyat.minumum_adet, (fiyat.depo1+fiyat.depo2+fiyat.depo3+fiyat.depo4+fiyat.depo5) as depo, fiyat.liste_fiyati, fiyat.yeni_urun = 'E' as yeni_urun, fiyat.ege_stok_id, fiyat.fiyat_doviz_id,
		CASE WHEN fiyat.net_fiyat_aktifmi='P' THEN (((fiyat.fiyat*(1-(fiyat.isk1/100)))*(1-(fiyat.isk2/100)))*(1-(fiyat.isk3/100)))*(1-(fiyat.isk4/100))*(1-(fiyat.kmp_isk/100)) ELSE fiyat.fiyat END as indirimli_fiyat,
		CASE WHEN fiyat.net_fiyat_aktifmi='P' THEN null ELSE fiyat.liste_fiyati END as fiyat
		from ege.tb_kart_stok_fiyatlar fiyat
		join ege.tb_kart_toptanci_siralama sira on (sira.toptanci_id = fiyat.toptanci_id)
		where fiyat.depo1+fiyat.depo2+fiyat.depo3+fiyat.depo4+fiyat.depo5 >= 0
		order by sira.siralama asc
	) fiyat on (stok.artis = fiyat.ege_stok_id)
	JOIN ege.tb_kart_doviz_tipleri doviz ON (doviz.artis = fiyat.fiyat_doviz_id)
	JOIN ege.tb_kart_doviz_tipleri liste_doviz ON (liste_doviz.artis = fiyat.liste_fiyati_doviz_id)
	JOIN vehicle_currency ON (vehicle_currency.symbol = doviz.display)
	JOIN vehicle_currency liste_currency ON (liste_currency.symbol = liste_doviz.display)
	JOIN manufacturer ON (manufacturer.name = initcap(stok.tedarikci))
	FULL JOIN product ON (stok.stok_kodu = product.partner_code AND manufacturer.id = product.manufacturer_id)
	JOIN category ON (slugify(COALESCE(stok.kirilim1, 'sandbox') || COALESCE(' ' || stok.kirilim2, '') || COALESCE(' ' || stok.kirilim3, '')) = category.slug)
	LEFT JOIN vehicle_kar_marji kar_marji ON (kar_marji.manufacturer_id = manufacturer.id);
RAISE NOTICE 'ege_product merged with product table';


UPDATE product set quantity = e.quantity, name = e.urun_adi, minimum_order_amount = e.minimum_order_amount,
price = CASE WHEN product.sync_ege THEN (((e.price*(e.urun_kar_marji+1))*((e.kdv+100)/100.0))*COALESCE(e.liste_parity, e.parity)) ELSE product.price END,
discount_price = CASE WHEN product.sync_ege THEN (((e.discount_price*(e.urun_kar_marji+1))*((e.kdv+100)/100.0))*e.parity) ELSE product.discount_price END, cargo_price = 12.5,
kdv = e.kdv,
category_id = e.category
FROM ege_product e
	WHERE e.stok_kodu is not null and product.id = e.product_id;
RAISE NOTICE 'updated current products';

update product set active = false where id in (select product_id from ege_product where product_id is not null and stok_kodu is null);
RAISE NOTICE 'updated unactive products';

insert into product (partner_code, name, price, discount_price, quantity, minimum_order_amount, cargo_price, kdv, manufacturer_id, category_id, active, date_added, last_modified, sync_ege, grup_id)
select stok_kodu, urun_adi,
((e.price*(e.urun_kar_marji+1))*((e.kdv+100)/100.0))*COALESCE(e.liste_parity, e.parity),
((e.discount_price*(e.urun_kar_marji+1))*((e.kdv+100)/100.0))*e.parity,
quantity, minimum_order_amount, 12.5, kdv, manufacturer, category, true, now(), now(), true, e.grup_id from ege_product e where e.product_id is null;
RAISE NOTICE 'inserted new products';

RAISE NOTICE 'upgrading tags';
insert into product_tags (product_id, producttag_id)
select e.product_id, 1 from ege_product e join product_tags tags on (tags.product_id = e.product_id) where e.yeni_urun and 1 not in(select producttag_id from product_tags where product_id = e.product_id);

delete from product_tags t where t.producttag_id = 1 and t.product_id in
(select e.product_id from ege_product e join product_tags tags on (tags.product_id = e.product_id) where not e.yeni_urun and 1 in(select producttag_id from product_tags where product_id = e.product_id));

insert into product_tags (product_id, producttag_id)
select e.product_id, 2 from ege_product e join product_tags tags on (tags.product_id = e.product_id) where e.kampanyali_urun and 2 not in(select producttag_id from product_tags where product_id = e.product_id);

delete from product_tags t where t.producttag_id = 2 and t.product_id in
(select e.product_id from ege_product e join product_tags tags on (tags.product_id = e.product_id) where not e.kampanyali_urun and 2 in(select producttag_id from product_tags where product_id = e.product_id));
RAISE NOTICE 'tags are updated';

RAISE NOTICE 'successfully processed';
return true;
END;
$function$
