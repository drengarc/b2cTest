from django.conf import settings
from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.db.models import F, Q
from django.shortcuts import redirect, get_object_or_404
from django.template import Context
from django.template.loader import get_template
from django.utils.translation import ugettext as _

from shop.modules.messaging.models import CustomerMessage, MessageDepartment
from shop.newsletter.models import Mail
from shop.utils.mail import send_html_mail


class ProductPriceFilter(admin.SimpleListFilter):
    title = _('price')
    parameter_name = 'price'

    def lookups(self, request, model_admin):
        model = model_admin.model
        max_value = model.objects.aggregate((self.parameter_name))['price__max']
        if max_value is not None:
            max_value = int(max_value)
            if max_value < 10:
                return ()
        else:
            return ()
        s = 5

        step = max_value / s
        arr = []
        for i in range(s):
            arr.append((("%s-%s" % ((i * step), ((i + 1) * step))), ("%s < %s" % (i * step, (i + 1) * step))))

        return arr

    def queryset(self, request, queryset):
        if self.value() is not None:
            v = self.value().split('-')
            return queryset.filter(price__gte=v[0], price__lte=v[1])


class MessagingAdmin(ModelAdmin):
    list_display = ('department', 'customer', 'order', 'time', 'is_new')

    change_form_template = 'shop/admin/modules/messaging/list_messages.html'

    def has_add_permission(self, request):
        return False

    def get_queryset(self, request):
        return CustomerMessage.objects.filter(top_message__isnull=True).order_by('time')

    def is_new(self, model):
        if model.unread:
            return '<img src="data:image/png;base64,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">'
        else:
            return '<img src="data:image/png;base64,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"'

    is_new.allow_tags = True

    def change_view(self, request, object_id, form_url='', extra_context={}):
        if request.method == 'POST':
            obj = CustomerMessage.objects.get(pk=object_id)
            item = CustomerMessage(staff=request.user, top_message_id=object_id, message=request.POST.get("message"),
                                   department=obj.department, customer=obj.customer)
            item.save()
            content = get_template('shop/modules/messaging/message_notification.html').render(Context(
                {'message': item, "SITE_URL": settings.SITE_URL}))
            send_html_mail(u'Yeni mesaj var.', content, [item.customer.email])
            return redirect('admin:messaging_customermessage_change', object_id)

        model = get_object_or_404(CustomerMessage, id=object_id)
        parent_id = model.id if model.top_message_id is None else model.top_message_id
        extra_context['customermessages'] = CustomerMessage.objects.filter(
            Q(top_message=parent_id) | Q(id=parent_id)).order_by('time')
        return super(MessagingAdmin, self).render_change_form(request, extra_context, change=True, obj=model,
                                                              form_url=form_url)


admin.site.register(CustomerMessage, MessagingAdmin)
admin.site.register(MessageDepartment)
