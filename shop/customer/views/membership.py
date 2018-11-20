# coding: utf-8
from django.conf import settings
from django.contrib import auth
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import NON_FIELD_ERRORS
from django.core.urlresolvers import reverse
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, resolve_url
from django.template import RequestContext, Context, Template
from django.template.response import TemplateResponse
from django.utils.http import urlsafe_base64_decode
from django.utils.translation import ugettext as _
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from ratelimit.decorators import ratelimit
from ratelimit.helpers import is_ratelimited
from simit.models import Page

from shop.customer.forms import RegisterForm, LoginForm, PasswordResetForm
from shop.newsletter.models import Mail
from shop.utils.mail import send_html_mail
from shop.utils.request import secure_required_cloudflare


@secure_required_cloudflare
def register(request):
    ct = {}
    if request.user.is_authenticated():
        return HttpResponseRedirect(reverse('shop_customer_orders'))
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            customer = get_user_model()()
            customer.email = form.cleaned_data['email']
            customer.set_password(form.cleaned_data['password1'])
            customer.first_name = form.cleaned_data['first_name']
            customer.last_name = form.cleaned_data['last_name']
            customer.phone = form.cleaned_data['phone']
            try:
                customer.save()
                user = auth.authenticate(email=customer.email, password=form.cleaned_data['password1'],
                                         remember_me=False, request=request)
                auth.login(request, user)
                mail = Mail.objects.get(slug="user_welcome")
                context = Context({"customer": user})
                title = Template(mail.title).render(context)
                content = Template(mail.content).render(context)
                send_html_mail(title, content,
                               [user.email],
                               fail_silently=True)
                return HttpResponseRedirect(reverse("shop_homepage"))
            except IntegrityError as e:
                if e.message.find('auth_user_email_key') > -1:
                    form._errors["email"] = form.error_class(
                        [_("There is another account using this email address")])
                elif e.message.find('auth_user_username_key'):
                    form._errors["email"] = form.error_class(
                        [_("Username is not available.")])
                else:
                    raise e
                ct['form'] = form
        else:
            ct['form'] = form
    else:
        ct['form'] = RegisterForm()

    ct['agreement'] = Page.objects.get(slug='kullanim-sozlesmesi-resmi').content
    return render_to_response('shop/default/register.html', ct, context_instance=RequestContext(request))


@ratelimit(keys=lambda x: 'min', rate='1/m')
@secure_required_cloudflare
@csrf_protect
def password_reset(request, is_admin_site=False,
                   template_name='registration/password_reset_form.html',
                   email_template_name='registration/password_reset_email.html',
                   subject_template_name='registration/password_reset_subject.txt',
                   password_reset_form=PasswordResetForm,
                   token_generator=default_token_generator,
                   post_reset_redirect=None,
                   from_email=None,
                   current_app=None,
                   extra_context=None):
    if post_reset_redirect is None:
        post_reset_redirect = reverse('password_reset_done')
    else:
        post_reset_redirect = resolve_url(post_reset_redirect)
    if request.method == "POST":
        form = password_reset_form(request.POST, captcha=request.limited)
        if form.is_valid():
            opts = {
                'use_https': request.is_secure(),
                'token_generator': token_generator,
                'from_email': from_email,
                'email_template_name': email_template_name,
                'subject_template_name': subject_template_name,
                'request': request,
            }
            if is_admin_site:
                opts = dict(opts, domain_override=request.get_host())
            form.save(**opts)
            return HttpResponseRedirect(post_reset_redirect)
    else:
        form = password_reset_form(captcha=is_ratelimited(request, method='POST'))
    context = {
        'form': form,
    }
    if extra_context is not None:
        context.update(extra_context)
    return TemplateResponse(request, template_name, context,
                            current_app=current_app)


@ratelimit(field=['email'])
@secure_required_cloudflare
def login(request):
    ct = {}
    if request.method == 'POST':
        form = LoginForm(request.POST, captcha=request.limited)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            remember_me = form.cleaned_data['remember_me']
            user = auth.authenticate(email=email, password=password, remember_me=remember_me, request=request)
            if user is not None:
                if user.is_active:
                    auth.login(request, user)
                    return HttpResponseRedirect(
                        reverse("shop_homepage") if request.GET.get('next') is None else request.GET.get('next'))
                else:
                    form._errors[NON_FIELD_ERRORS] = form.error_class(
                        [_("The account has been disabled, please contact with administrators.")])
            else:
                form._errors[NON_FIELD_ERRORS] = form.error_class([_("The password you entered is wrong.")])
        ct['form'] = form
    else:
        ct['form'] = LoginForm()

    return render_to_response(('shop/'+settings.SHOP_TEMPLATE+'/login.html', 'shop/default/login.html'), ct, context_instance=RequestContext(request))


@secure_required_cloudflare
def logout(request):
    auth.logout(request)
    return HttpResponseRedirect(reverse("shop_homepage"))


# Doesn't need csrf_protect since no-one can guess the URL
@sensitive_post_parameters()
@never_cache
@secure_required_cloudflare
def password_reset_confirm(request, uidb64=None, token=None,
                           template_name='registration/password_reset_confirm.html',
                           token_generator=default_token_generator,
                           set_password_form=SetPasswordForm,
                           post_reset_redirect=None,
                           current_app=None, extra_context=None):
    """
    View that checks the hash in a password reset link and presents a
    form for entering a new password.
    """
    UserModel = get_user_model()
    assert uidb64 is not None and token is not None  # checked by URLconf
    if post_reset_redirect is None:
        post_reset_redirect = reverse('password_reset_complete')
    else:
        post_reset_redirect = resolve_url(post_reset_redirect)
    try:
        uid = urlsafe_base64_decode(uidb64)
        user = UserModel._default_manager.get(pk=uid)
    except (TypeError, ValueError, OverflowError, UserModel.DoesNotExist):
        user = None

    if user is not None and token_generator.check_token(user, token):
        validlink = True
        if request.method == 'POST':
            form = set_password_form(user, request.POST)
            if form.is_valid():
                form.save()
                return HttpResponseRedirect(post_reset_redirect)
        else:
            form = set_password_form(None)
    else:
        validlink = False
        form = None
    context = {
        'form': form,
        'validlink': validlink,
    }
    if extra_context is not None:
        context.update(extra_context)
    return TemplateResponse(request, template_name, context,
                            current_app=current_app)