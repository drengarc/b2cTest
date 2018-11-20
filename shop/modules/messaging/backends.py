from django.utils.translation import ugettext
from notification import backends
from shop.modules.messaging.models import CustomerMessage


class MessageBackend(backends.BaseBackend):
    spam_sensitivity = 2

    def can_send(self, user, notice_type):
        return super(MessageBackend, self).can_send(user, notice_type)

    def deliver(self, recipient, sender, notice_type, extra_context):
        message = CustomerMessage(customer=recipient, topic=notice_type.display)

        context = self.default_context()
        context.update({
            "recipient": recipient,
            "sender": sender,
            "notice": ugettext(notice_type.display),
        })
        context.update(extra_context)

        message.message = self.get_formatted_messages(("short.txt", "full.txt"), notice_type.label, context)

        message.save()
