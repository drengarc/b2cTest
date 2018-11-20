django.jQuery(document).ready(function () {
    var $ = django.jQuery, brand = $('#vehicle_brand'), model = $('#vehicle_model'), type = $('#vehicle_model_type'), year = $('#id_vehicle');
    brand.change(function () {
        model.html('');
        type.html('');
        year.html('');
        django.jQuery.getJSON("/admin/shop/category/filter/?parent=" + this.value, function (data) {
            var str = '';
            for (var i = 0; i < data.length; i++) str += '<option value="' + data[i]['id'] + '">' + data[i]['name'] + '</option>';
            model.html(str);
        });
    });
    model.change(function () {
        type.html('');
        year.html('');
        django.jQuery.getJSON("/admin/shop/category/filter/?parent=" + this.value, function (data) {
            var str = '';
            for (var i = 0; i < data.length; i++) str += '<option value="' + data[i]['id'] + '">' + data[i]['name'] + '</option>';
            type.html(str);
        });
    });
    type.change(function () {
        year.html('');
        django.jQuery.getJSON("/admin/shop/category/filter/?parent=" + this.value, function (data) {
            var str = '';
            for (var i = 0; i < data.length; i++) str += '<option value="' + data[i]['id'] + '">' + data[i]['name'] + '</option>';
            year.html(str);
        });
    });
});