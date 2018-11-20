django.jQuery( document ).ready(function() {
    if (django.jQuery.cookie('auto_refresh_page')=='true')
        var open = false;
    else
        var open = true;

    var elem = django.jQuery('<p/>', {
        id: 'reload_page'
    }).css('cursor', 'pointer').css('color', 'red').css('padding', '2px').click(function() {
     open = !open;
     django.jQuery.cookie('auto_refresh_page', open);
     if (open)
         elem.text('Toggle Refresh (active)');
     else
         elem.text('Toggle Refresh (inactive)');
    }).prependTo('#changelist-filter');
     elem.click();
      setTimeout(function() {
          if (open)
          location.reload();
      }, 5000)
});