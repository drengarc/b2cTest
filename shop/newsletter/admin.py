from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.admin.util import unquote
from django.utils.safestring import mark_safe
from shop.newsletter.models import Newsletter, Mail, MAILS
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone


class NewsletterStatusFilter(admin.SimpleListFilter):
    title = _('status')
    parameter_name = 'sent'

    def lookups(self, request, model_admin):
        return ('0', _('scheduled')), ('1', _('past'))

    def queryset(self, request, queryset):
        if self.value() is not None:
            if self.value() == '0':
                return queryset.filter(date_sent__gte=timezone.now())
            elif self.value() == '1':
                return queryset.filter(date_sent__lte=timezone.now())


class NewsletterAdmin(ModelAdmin):
    search_fields = ('title',)
    list_filter = (NewsletterStatusFilter, 'is_active', 'language')
    list_display = ('title', 'sent', 'is_active')
    change_form_template = 'change_form_template.html'

    def sent(self, obj):
        return obj.date_sent < timezone.now()

    sent.boolean = True


class MailAdmin(ModelAdmin):
    search_fields = ('title',)
    list_display = ('slug', 'title')
    readonly_fields = ('slug',)

    fieldsets = (('', {'fields': ('slug', 'title', 'content')}),)

    def get_actions(self, request):
        # actions = super(MailAdmin, self).get_actions(request)
        #del actions['delete_selected']
        return super(MailAdmin, self).get_actions(request)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        if extra_context is None:
            extra_context = {}

        variables = MAILS.get(unquote(object_id))
        html = '<table>'
        for key, desc in variables.items():
            html += '<tr><th style="font-weight:bold">' + key + ':</th><td>' + desc + '</td></tr>'

        html += '</table>'

        extra_context["variable_field"] = [[{"label_tag": _('Variables'), "is_readonly": True,
                                             "contents": mark_safe(html)}]]

        return super(MailAdmin, self).change_view(request, object_id, form_url, extra_context)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(Newsletter, NewsletterAdmin)
admin.site.register(Mail, MailAdmin)