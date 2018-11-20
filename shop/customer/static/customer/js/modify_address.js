var personal_fields = $('#identity_number-field'), company_fields = $('#tax_authority-field, #tax_no-field');

var obj_to_option = function (data) {
    var ops = ["<option>---------</option>"];
    for (var i = 0; i < data.length; i++) {
        ops.push("<option value='" + data[i]['id'] + "'>" + data[i]['name'] + "</option>");
    }
    return ops.join("\n");
}
$('input[name="invoice_type"]').change(function () {
    if (this.value == 'personal') {
        personal_fields.show();
        company_fields.hide();
    } else if (this.value == 'company') {
        personal_fields.hide();
        company_fields.show();
    }
}).filter(':checked').trigger('change');

$(document).on('change', '#country-field', function (e) {
    $('#city-field').remove();
    $('#ilce-field').remove();
    var clone = $(e.target).closest('.fieldWrapper').clone().attr('id', 'city-field');
    clone.find('label').html('City');
    if (e.target.value == '') return;
    var _this = this;
    $.post('/api/city', {country: e.target.value}).done(function (data) {
        clone.find('select').html(obj_to_option(data)).attr('name', 'city');
        $(_this).closest('.fieldWrapper').after(clone);
    });
});

$(document).on('change', '#city-field', function (e) {
    $('#ilce-field').remove();
    var cloned = $(e.target).closest('.fieldWrapper')
    var ilce = cloned.clone().attr('id', 'ilce-field');
    ilce.find('label').html('İlçe');
    $.post('/api/ilce', {city: e.target.value}).done(function (data) {
        ilce.find('select').html(obj_to_option(data)).attr('name', 'ilce');
        cloned.after(ilce);
    });
});