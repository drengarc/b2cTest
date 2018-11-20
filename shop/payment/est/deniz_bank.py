import re
import requests

__author__ = 'buremba'


class DenizBankPay():
    def __init__(self, ShopCode, UserCode, UserPass, debug=True):
        self.ShopCode = ShopCode
        self.UserCode = UserCode
        self.UserPass = UserPass
        self.debug = debug

    def pay(self, Pan, Cvv2, month, year, PurchAmount, OrderId, CardType, Currency=949, SecureType="NonSecure",
            InstallmentCount=1, TxnType="Auth", Lang="TR"):
        Expiry = month + year

        if self.debug:
            url = "http://93.94.199.122:7000/DenizNonSecure.aspx"
        else:
            url = "https://inter-vpos.com.tr/MPI/Default.aspx"

        r = requests.post(url,
                          data={"ShopCode": self.ShopCode, "UserCode": self.UserCode, "UserPass": self.UserPass,
                                "Pan": Pan, "Cvv2": Cvv2,
                                "Expiry": Expiry, "PurchAmount": "%.2f" % PurchAmount,
                                "CardType": CardType, "OrderId": OrderId,
                                "Currency": Currency,
                                "SecureType": SecureType,
                                "InstallmentCount": InstallmentCount, "TxnType": TxnType,
                                "Lang": Lang})

        response = r.text.split(";;")
        parsed = {}
        for val in response:
            key, value = val.split("=")
            parsed[key] = value

        return parsed["TxnResult"] == "Success", parsed["ErrorMessage"]


def credit_card_type(cc_number):
    VISA_CC_RE = re.compile(r"^4[0-9]{12}(?:[0-9]{3})?$")
    MASTERCARD_CC_RE = re.compile(r"^5[1-5][0-9]{14}$")

    if MASTERCARD_CC_RE.match(str(cc_number)):
        return 1
    elif VISA_CC_RE:
        return 0
    else:
        return None