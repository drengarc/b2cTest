(function($) {
    $(function() {
        $('.order-history').click(function() {
            $.getJSON($(this).attr('data-href'), function(data) {
                var tbl = "<table><tr><th>Status</th><th>Time</th><th>Comments</th></tr>";
                data.forEach(function(d) {
                    tbl += "<tr><td>"+ d.status +"</td><td>"+ d.time+"</td><td>"+ (d.comments ? d.comments : "") +"</td></tr>";
                });
                tbl += "</table>";
                vex.dialog.alert(tbl);
            });
        });

        $('button.markShipped').click(function(e) {
            e.preventDefault();
            $this = $(this);
            vex.dialog.prompt({message: "Lütfen kargo takip numarasını giriniz.", placeholder: "Kargo takip numarası", callback: function(cargo_no) {
                if (cargo_no)
                    $.post($this.attr('data-href'), {csrfmiddlewaretoken: $.cookie('csrftoken'), cargo_no: cargo_no}, function(data) {
                       if(data)
                            vex.dialog.alert(data);
                    });
            }})

        });

        $('button.approveRefund').click(function(e) {
            e.preventDefault();
            $.getJSON($(this).attr('data-href'), function(data) {
               if(data==true)
                    vex.dialog.alert("OK.");
            });
        });

        $('button.refund').click(function(e) {
            e.preventDefault();
            $.getJSON($(this).attr('data-href'), function(data) {
               if(data==true)
                    vex.dialog.alert("OK.");
            });
        });
    });
})(django.jQuery);