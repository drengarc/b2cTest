# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.template.loader import get_template
from xlrd import open_workbook
from django.utils.translation import ugettext as _
from django.db import connection
from shop.importer.forms import UploadForm
from shop.importer.utils import parse
from django.db import transaction

__author__ = 'buremba'

COLUMNS = {
    "stok_kodu": u"Stok Kod",
    "stok_ad": u"Stok Ad",
    "tedarikci": u"Tedarikçi",
    "marka": u"Marka",
    "arac_model": u"Model",
    "arac_model_tip": u"Model Tip",
    "motor_tip": u"Motor Tip",
    "yakit_tip": u"Yakıt Tip",
    "arac_baslangic_yil": u"Baslangic Yil",
    "arac_bitis_yil": u"Bitis Yil",
    "kirilim1": u"Kırılım 1",
    "kirilim2": u"Kırılım 2",
    "kirilim3": u"Kırılım 3",
    "depo_miktar": u"Depo Miktar",
    "liste_fiyat": u"liste_fiyat",
    "liste_fiyat_doviz": u"liste_fiyat_doviz",
    "iskonto": u"iskonto",
    "iskonto2": u"iskonto2",
    "iskonto3": u"iskonto3",
    "minimum_adet": u"Minimum Adet",
    "kampanya_fiyat": u"kampanya_fiyat",
    "kampanya_fiyat_doviz": u"kampanya_fiyat_doviz",
    "kdv": u"kdv",
    "kargo_fiyat": u"Cargo Bedeli",
    "yeni_urun": u"yeni_urun(E/H)",
}
COLUMNS_BY_VALUE = dict(zip(COLUMNS.values(), COLUMNS.keys()))


@transaction.atomic
def process(columns, rows):
    cursor = connection.cursor()
    cols = {COLUMNS_BY_VALUE[column]: idx for idx, column in enumerate(columns)}

    keys = ", ".join(COLUMNS.keys())

    params = []
    col_list = COLUMNS.keys()
    parameters = []
    for row in rows:
        if not row[cols.get("stok_ad")] or not row[cols.get("stok_kodu")] or not row[cols.get("tedarikci")] or not row[
            cols.get("marka")] or not row[cols.get("arac_baslangic_yil")] or not row[cols.get("kirilim1")]:
            continue

        liste_fiyat = row[cols.get("liste_fiyat")].replace(',', '.')
        row[cols.get("liste_fiyat")] = float(liste_fiyat) if liste_fiyat else None
        kampanya_fiyat = row[cols.get("kampanya_fiyat")].replace(',', '.')
        row[cols.get("kampanya_fiyat")] = float(kampanya_fiyat) if kampanya_fiyat else None
        row[cols.get("arac_baslangic_yil")] = int(row[cols.get("arac_baslangic_yil")])
        bitis = row[cols.get("arac_bitis_yil")]
        row[cols.get("arac_bitis_yil")] = int(bitis) if bitis else None

        for col in col_list:
            idx = cols.get(col)
            if idx is None:
                params.append(None)
            elif row[idx] is None or row[idx] == "":
                params.append(get_placeholder(col))
            else:
                params.append(row[idx])

        parameters.append("(" + ", ".join(["%s" for col in range(len(COLUMNS))]) + ")")

    cursor.execute('create temporary table stok as select * from (VALUES %s) as q(%s)' % (", ".join(parameters), keys),
                   params)
    cursor.execute('''
        insert into ege.tb_kart_stok_araclar (marka, ortak_adi, model, motor_tipi, yakit_tipi, baslangic_yili, bitis_yili)
        select distinct marka, arac_model, arac_model_tip, motor_tip, yakit_tip, arac_baslangic_yil, arac_bitis_yil from stok n
        where (marka, arac_model, arac_model_tip, motor_tip, yakit_tip, arac_baslangic_yil::text, arac_bitis_yil::text)
        not in (select marka, ortak_adi, model, motor_tipi, yakit_tipi, baslangic_yili, bitis_yili from ege.tb_kart_stok_araclar)
    ''')
    cursor.execute('''
        UPDATE ege.tb_kart_stok_araclar SET grup_id = artis
    ''')
    cursor.execute('''
        INSERT INTO ege.tb_kart_stok (grup_id, urun_adi, stok_kodu, tedarikci, kirilim1, kirilim2, kirilim3)
        select e.artis, n.stok_ad, n.stok_kodu, n.tedarikci, n.kirilim1, n.kirilim2, n.kirilim3 from stok n join ege.tb_kart_stok_araclar e on
        (e.marka = n.marka and e.ortak_adi = n.arac_model and e.model = n.arac_model_tip and e.motor_tipi = n. motor_tip and n.yakit_tip = e.yakit_tipi and n.arac_baslangic_yil::text = e.baslangic_yili and e.bitis_yili is not distinct from n.arac_bitis_yil::text)
    ''')
    cursor.execute('''
        WITH fiyatlar AS (
            select kdv::float8, 1 as toptanci_id, e.artis::int4 as grup_id, stok_kodu, coalesce(ege.convert_to_integer(minimum_adet), 1) as minumum_adet, tedarikci,
            kargo_fiyat::float8 as kargo_fiyati, depo_miktar::float8 as depo1, 0 as depo2,0 as depo3, 0 as depo4, 0 as depo5, yeni_urun,
            iskonto::float8 as isk1, iskonto2::float8 as isk2, iskonto3::float8 as isk3, 0 as isk4, 0 as kmp_isk,
            liste_fiyat::float as liste_fiyati,
            (SELECT artis FROM ege.tb_kart_doviz_tipleri WHERE doviz_adi = trim(liste_fiyat_doviz)) as liste_fiyati_doviz_id,
            kampanya_fiyat::float as fiyat,
            (SELECT artis FROM ege.tb_kart_doviz_tipleri WHERE doviz_adi = trim(kampanya_fiyat_doviz)) as fiyat_doviz_id,
            (CASE WHEN kampanya_fiyat is not null THEN 'A' ELSE 'P' END) as net_fiyat_aktifmi,
            (select artis from ege.tb_kart_stok where
                (grup_id, urun_adi, stok_kodu, tedarikci, kirilim1, kirilim2, kirilim3) =
                (e.artis, n.stok_ad, n.stok_kodu, n.tedarikci, n.kirilim1, n.kirilim2, n.kirilim3) LIMIT 1) as ege_stok_id
            from stok n
            join ege.tb_kart_stok_araclar e on
            (e.marka = n.marka and e.ortak_adi = n.arac_model and e.model = n.arac_model_tip and e.motor_tipi = n. motor_tip and n.yakit_tip = e.yakit_tipi and n.arac_baslangic_yil::text = e.baslangic_yili and e.bitis_yili is not distinct from n.arac_bitis_yil::text)
        ), insert_not_existed AS (
            INSERT INTO ege.tb_kart_stok_fiyatlar (kdv, toptanci_id, grup_id, stok_kodu, minumum_adet, tedarikci,
                kargo_fiyati, depo1, depo2,depo3,depo4,depo5, yeni_urun, isk1, isk2, isk3, isk4, kmp_isk,
                liste_fiyati, liste_fiyati_doviz_id, fiyat, fiyat_doviz_id, net_fiyat_aktifmi, ege_stok_id)
                SELECT * from fiyatlar WHERE (tedarikci, stok_kodu)
				NOT IN (SELECT tedarikci, stok_kodu FROM ege.tb_kart_stok_fiyatlar) RETURNING 1
        ), update_existed AS (
            UPDATE ege.tb_kart_stok_fiyatlar SET kdv = f.kdv, toptanci_id = f.toptanci_id, grup_id = f.grup_id, minumum_adet = f.minumum_adet,
                kargo_fiyati = f.kargo_fiyati, depo1 = f.depo1, depo2 = f.depo2, depo3 = f.depo3, depo4 = f.depo4, depo5 = f.depo5, yeni_urun = f.yeni_urun, isk1 = f.isk1, isk2 = f.isk2, isk3 = f.isk3, isk4 = f.isk4, kmp_isk = f.kmp_isk,
                liste_fiyati = f.liste_fiyati, liste_fiyati_doviz_id = f.liste_fiyati_doviz_id, fiyat = f.fiyat, fiyat_doviz_id = f.fiyat_doviz_id, net_fiyat_aktifmi = f.net_fiyat_aktifmi, ege_stok_id = f.ege_stok_id
                FROM fiyatlar f WHERE f.tedarikci = tb_kart_stok_fiyatlar.tedarikci AND
				f.stok_kodu = tb_kart_stok_fiyatlar.stok_kodu RETURNING 1
        ) SELECT count(*) FROM insert_not_existed UNION ALL SELECT count(*) FROM update_existed
         ''')
    cursor.execute('''
            UPDATE ege.tb_kart_stok_fiyatlar SET fiyat = coalesce(fiyat, liste_fiyati), fiyat_doviz_id = coalesce(fiyat_doviz_id, liste_fiyati_doviz_id);
         ''')
    cursor.callproc("ege.ege_sync")

def get_placeholder(key):
    if key in ["kirilim1", "kirilim2", "kirilim3", "motor_tip", "yakit_tip", "arac_model_tip"]:
        return "-"
    else:
        return None


def importer(request):
    if request.method == "POST":
        sheets = None
        if request.GET.get('form') is None:
            form = UploadForm(request.POST, request.FILES)
            if form.is_valid():
                workbook = open_workbook(file_contents=form.cleaned_data.get('file').file.getvalue())
                sheets = []
                for s in workbook.sheets():
                    sheet = {'name': s.name, 'columns': s._cell_values[0], 'rows': s._cell_values[1:]}
                    sheets.append(sheet)
        else:
            req = parse(request.POST.urlencode())
            sheets = req['sheets'].values()
            for sheet in sheets:
                sheet['rows'] = sheet['rows'].values()
                sheet['rows'] = [sheet['rows'][i][''] for i in range(len(sheet['rows']))]
                sheet['columns'] = sheet['columns']['']
            if request.POST.get("action") == 'delete_selected':
                for sheet_id, row_ids in req['act'].items():
                    sheets[sheet_id]['rows'] = [r for i, r in enumerate(sheets[sheet_id]['rows']) if i not in row_ids]

        if sheets is not None:
            process(sheets[0]["columns"], sheets[0]["rows"])
            return render_to_response('admin/base_site.html', {
                "content": u"Başarıyla aktarıldı",
                "title": _("import product")}, RequestContext(request))
            # return render_to_response('admin/base_site.html', {"content": get_template('admin/importer.html').render(
            # RequestContext(request, {"sheets": sheets, "total": total})), "title": _("product importer")},
            # RequestContext(request))
    else:
        form = UploadForm()
    return render_to_response('admin/base_site.html', {
        "content": get_template('admin/form.html').render(RequestContext(request, {"form": form})),
        "title": _("import product")}, RequestContext(request))