# coding: utf-8
from django.conf import settings
from django.core.mail import EmailMultiAlternatives


def send_html_mail(subject, content, to_mails, fail_silently=False):
    content = unicode(content)
    content += u' <br> <a style="word-wrap:break-word;color:#606060;font-weight:normal;text-decoration:none;font-size:9px" href="%unsubscribe_url%">mail listesinden çıkmak için tıklayınız</a>'
    from_email = "%s <%s>" % (settings.DEFAULT_MAIL_FROM_NAME, settings.DEFAULT_FROM_EMAIL)
    mail = EmailMultiAlternatives(unicode(subject), content, from_email, to_mails)
    mail.attach_alternative(content, 'text/html')
    mail.send(fail_silently)