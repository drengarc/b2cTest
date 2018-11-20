var $ = django.jQuery;
$(document).ready(function() {
    $('#category_0').change(function() {
       if (!this.value) return;
       $.getJSON($('#admin-url').text()+'shop/category/get', {id: this.value}, function(data) {
        if(data.vehicle_category) $('.field-vehicle').closest('.fieldset').hide().find('select').attr('disabled', true); else $('.field-vehicle').closest('.fieldset').show().find('select').removeAttr('disabled');
       })
    }).trigger('change');
})