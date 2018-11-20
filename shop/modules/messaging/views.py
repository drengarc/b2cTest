# -*- coding: utf-8 -*-
from django.conf import settings

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext, Context
from django.template.loader import get_template

from shop.customer.views.user import LOGIN_URL
from shop.modules.messaging.forms import CustomerMessageForm, NewCustomerMessage
from shop.modules.messaging.models import CustomerMessage
from shop.utils.mail import send_html_mail


@login_required(login_url=LOGIN_URL)
def display_message(request, message_id):
    if request.method == 'POST':
        form = NewCustomerMessage(request.POST)
        if form.is_valid():
            CustomerMessage(customer=request.user, message=form.cleaned_data['message'],
                            top_message_id=message_id).save()
            return redirect('shop_modules_messaging_display', message_id)
    else:
        form = NewCustomerMessage()

    CustomerMessage.objects.filter(customer=request.user, top_message_id=message_id, unread=True).update(unread=False)

    customer_messages = CustomerMessage.objects.filter(
        Q(Q(top_message_id=message_id) | Q(id=message_id)) & Q(customer=request.user)).order_by('time')
    return render_to_response('shop/modules/messaging/display_message.html', locals(), RequestContext(request))


@login_required(login_url=LOGIN_URL)
def list_messages(request):
    customer_messages = CustomerMessage.objects.filter(customer=request.user).order_by('top_message', '-time').distinct(
        'top_message').reverse()
    return render_to_response('shop/modules/messaging/list_messages.html', locals(), RequestContext(request))


@login_required(login_url=LOGIN_URL)
def new_message(request):
    if request.method == 'POST':
        form = CustomerMessageForm(request.POST, user=request.user)
        if form.is_valid():
            message = CustomerMessage(customer=request.user, order=form.cleaned_data['order'],
                                      topic=form.cleaned_data['topic'], message=form.cleaned_data['message'],
                                      department=form.cleaned_data['department'])
            message.save()
            messages.add_message(request, messages.INFO,
                                 u'Mesajınız iletildi, en kısa sürede sizinle iletişime geçeceğiz.')
            content = get_template('shop/modules/messaging/new_message_notification.html').render(
                Context({'message': message, "SITE_URL": settings.SITE_URL}))
            send_html_mail(u'Mesajınız iletildi', content, [request.user.email], fail_silently=True)
            return redirect('shop.modules.messaging.views.list_messages')
    else:
        form = CustomerMessageForm(user=request.user)

    return render_to_response('shop/modules/messaging/new_message.html', locals(), RequestContext(request))
