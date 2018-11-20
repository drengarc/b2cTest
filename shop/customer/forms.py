# coding: utf-8
from captcha.fields import ReCaptchaField
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.models import get_current_site
from django.forms.util import ErrorList
from django.template import loader
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import ugettext_lazy as _
from shop.customer.models import CustomerAddress
from shop.models import City, Ilce


class LoginForm(forms.Form):
    email = forms.CharField(max_length=100, label=_(u'Email'))
    password = forms.CharField(widget=forms.PasswordInput(), label=_(u'Password'))
    remember_me = forms.BooleanField(required=False, label=_(u'Remember me'))

    def __init__(self, *args, **kwargs):
        captcha = kwargs.pop('captcha', False)
        super(LoginForm, self).__init__(*args, **kwargs)
        if captcha:
            self.fields['captcha'] = ReCaptchaField()


INVOICE_TYPE_CHOICES = (('personal', _('personal')), ('company', _('company')))


class CustomerAddressForm(forms.ModelForm):
    invoice_type = forms.ChoiceField(label=_('invoice type'), widget=forms.RadioSelect, choices=INVOICE_TYPE_CHOICES,
                                     initial='personal')
    city = forms.ModelChoiceField(label=_('city'), queryset=City.objects.filter(country_id=1))

    class Meta:
        fields = (
            'address_name', 'first_name', 'last_name', 'address', 'postcode', 'land_line', 'cell_phone', 'city',
            'invoice_type', 'identity_number', 'tax_authority', 'tax_no')
        model = CustomerAddress

    def __init__(self, *args, **kwargs):
        super(CustomerAddressForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = [
            'address_name', 'first_name', 'last_name', 'address', 'postcode', 'land_line', 'cell_phone',
            'city', 'invoice_type', 'identity_number', 'tax_authority', 'tax_no']

        if kwargs.get('instance'):
            if len(args) > 0 and args[0].get('city'):
                city_id = args[0].get('city')
                self.fields['ilce'] = forms.ModelChoiceField(label=_('ilçe'), queryset=Ilce.objects.filter(city_id=city_id),
                                                             initial=kwargs.get('instance').ilce_id)
            elif kwargs.get('instance').ilce is not None:
                ilce = kwargs.get('instance').ilce
                self.fields['ilce'] = forms.ModelChoiceField(queryset=Ilce.objects.filter(city_id=ilce.city_id),
                                                             initial=ilce)
                self.fields['city'].initial = ilce.city_id
            if "ilce" in self.fields:
                self.fields.keyOrder = [
                'address_name', 'first_name', 'last_name', 'address', 'postcode', 'land_line', 'cell_phone',
                'city', 'ilce', 'invoice_type', 'identity_number', 'tax_authority', 'tax_no']

    class Media:
        js = ('customer/js/modify_address.js',)

    def clean(self):
        invoice_type = self.cleaned_data.get('invoice_type')
        if invoice_type == 'personal':
            if not self.cleaned_data.get('identity_number'):
                self._errors["identity_number"] = self.error_class([_("This field is required.")])
            self.cleaned_data['invoice_type'] = None
            self.cleaned_data['tax_no'] = None
        elif invoice_type == 'company':
            if not self.cleaned_data.get('tax_no'):
                self._errors["tax_no"] = self.error_class([_("This field is required.")])
            if not self.cleaned_data.get('tax_authority'):
                self._errors["tax_authority"] = self.error_class([_("This field is required.")])
            self.cleaned_data['identity_number'] = None
        data = super(CustomerAddressForm, self).clean()
        return data

    def save(self, force_insert=False, force_update=False, commit=True):
        if self.data.get('ilce') is not None:
            self.instance.ilce_id = int(self.data.get('ilce'))
        return super(CustomerAddressForm, self).save(commit)


class RegisterForm(forms.Form):
    email = forms.EmailField(label=_(u'Email'))
    password1 = forms.CharField(widget=forms.PasswordInput(), label=_(u'Password'), min_length=5)
    password2 = forms.CharField(widget=forms.PasswordInput(), label=_(u'Password *(Again)'))
    first_name = forms.CharField(label=_(u'First name'))
    last_name = forms.CharField(label=_(u'Last name'), required=False)
    phone = forms.CharField(label=_(u'Phone number'), required=False)
    agreement = forms.BooleanField(required=True)

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')

        if not password2:
            raise forms.ValidationError("Şifrenizi teyit etmemiz için iki kere girmeniz gerekiyor.")
        if password1 != password2:
            raise forms.ValidationError("Şifreleriniz eşleşmiyor")
        return password2


class ProfileUpdateForm(forms.Form):
    email = forms.EmailField(label=_(u'Email'), required=False, )
    old_password = forms.CharField(widget=forms.PasswordInput(), label=_(u'Old Password'), required=False)
    new_password = forms.CharField(widget=forms.PasswordInput(), label=_(u'New password'), required=False)
    first_name = forms.CharField(label=_(u'First name'))
    last_name = forms.CharField(label=_(u'Last name'), required=False)
    phone = forms.CharField(label=_(u'Phone number'), required=False)

    def __init__(self, user, data=None, files=None, auto_id='id_%s', prefix=None,
                 initial=None, error_class=ErrorList, label_suffix=None,
                 empty_permitted=False):
        if data:
            data = data.copy()
            data['email'] = user.email
        else:
            initial = {"email": user.email, "first_name": user.first_name, "last_name": user.last_name,
                       "phone": user.phone}
        super(ProfileUpdateForm, self).__init__(data, files, auto_id, prefix,
                                                initial, error_class, label_suffix,
                                                empty_permitted)
        self.user = user
        self.fields['email'].widget.attrs['disabled'] = 'disabled'

    def clean(self):
        cleaned_data = super(ProfileUpdateForm, self).clean()
        if "new_password" in cleaned_data and not cleaned_data.get("old_password"):
            raise forms.ValidationError(_("You need to enter your old password in order to update your password"))
        return cleaned_data

    def clean_old_password(self):
        old_pass = self.cleaned_data.get('old_password')
        if old_pass and not self.user.check_password(old_pass):
            raise forms.ValidationError(_("The password you entered is wrong."))
        return old_pass

    def save(self):
        customer = self.user
        customer.email = self.cleaned_data['email']
        customer.first_name = self.cleaned_data['first_name']
        customer.last_name = self.cleaned_data['last_name']
        customer.phone = self.cleaned_data['phone']
        if self.cleaned_data.get('new_password'):
            customer.set_password(self.cleaned_data.get('new_password'))
        customer.save()


class PasswordResetForm(forms.Form):
    email = forms.EmailField(label=_("Email"), max_length=254)

    def __init__(self, *args, **kwargs):
        captcha = kwargs.pop('captcha', False)
        super(PasswordResetForm, self).__init__(*args, **kwargs)
        if captcha:
            self.fields['captcha'] = ReCaptchaField()


    def set_captcha(self):
        self.fields['captcha'] = ReCaptchaField()

    def save(self, domain_override=None,
             subject_template_name='registration/password_reset_subject.txt',
             email_template_name='registration/password_reset_email.html',
             use_https=False, token_generator=default_token_generator,
             from_email=None, request=None):
        """
        Generates a one-use only link for resetting password and sends to the
        user.
        """
        from django.core.mail import send_mail

        email = self.cleaned_data["email"]
        active_users = get_user_model()._default_manager.filter(
            email__iexact=email, is_active=True)
        for user in active_users:
            # Make sure that no email is sent to a user that actually has
            # a password marked as unusable
            if not user.has_usable_password():
                continue
            if not domain_override:
                current_site = get_current_site(request)
                site_name = current_site.name
                domain = current_site.domain
            else:
                site_name = domain = domain_override
            c = {
                'email': user.email,
                'domain': domain,
                'site_name': site_name,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'user': user,
                'token': token_generator.make_token(user),
                'protocol': 'https' if use_https else 'http',
            }
            subject = loader.render_to_string(subject_template_name, c)
            # Email subject *must not* contain newlines
            subject = ''.join(subject.splitlines())
            email = loader.render_to_string(email_template_name, c)
            send_mail(subject, email, from_email, [user.email])