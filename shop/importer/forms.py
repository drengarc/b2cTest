from django import forms
from django.utils.translation import ugettext_lazy as _


class UploadForm(forms.Form):
    file = forms.FileField(label=_(u'file'))