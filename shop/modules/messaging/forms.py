from django import forms
from django.utils.translation import ugettext as _
from shop.customer.models import Order
from shop.modules.messaging.models import MessageDepartment


class NewCustomerMessage(forms.Form):
    message = forms.CharField(widget=forms.Textarea(), label=_(u'message'), required=True)


class CustomerMessageForm(forms.Form):
    topic = forms.CharField(max_length=100, label=_(u'topic'))
    order = forms.ModelChoiceField(queryset=None, label=_(u'order'), required=False)
    department = forms.ModelChoiceField(MessageDepartment.objects.all(), label=_(u'department'), required=True)
    message = forms.CharField(widget=forms.Textarea(), label=_(u'message'))

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(CustomerMessageForm, self).__init__(*args, **kwargs)

        self.fields['order'].queryset = Order.objects.filter(customer=user)

