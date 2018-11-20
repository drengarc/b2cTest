#coding: utf-8

from django import forms
from django.forms.util import ErrorDict
from django.forms.forms import NON_FIELD_ERRORS
from django.core.exceptions import ValidationError

PAYMENT_CHOICES = (
    ('credit_card', 'credit_card'),
    ('money_order', 'moneyorder'),
    ('3d_pay', '3d_pay'),
)


class PaymentInformation(forms.Form):
    cc_owner = forms.CharField(max_length=100)
    cc_number = forms.CharField(max_length=19, min_length=16)
    cc_cvv = forms.CharField(max_length=4)
    cc_exp = forms.CharField(max_length=10)
    installment = forms.IntegerField(max_value=24, min_value=0)
    payment_type = forms.ChoiceField(choices=PAYMENT_CHOICES)

    def clean_cc_number(self):
        data = self.data['pan']
        if data:
            raise ValidationError("Missing input")
        return data

    def clean_cc_number(self):
        data = self.cleaned_data['cc_number']
        s = data.replace(" ", "")
        if len(s) != 16:
            raise ValidationError('kredi kartı formatı yanlış', code='invalid')
        return s

    def clean_cc_exp(self):
        data = self.cleaned_data['cc_exp']
        try:
            month, year = data.split(" / ")
            if not 0 < int(month) <= 12:  #and not (13 < int(year) < 45 or 2013 < int(year) < 2045):
                raise forms.ValidationError("Expiration date is not valid.")
        except:
            raise forms.ValidationError("Expiration date is not valid.")

        return month, year

    def add_form_error(self, message):
        if not self._errors:
            self._errors = ErrorDict()
        if not NON_FIELD_ERRORS in self._errors:
            self._errors[NON_FIELD_ERRORS] = self.error_class()
        self._errors[NON_FIELD_ERRORS].append(message)