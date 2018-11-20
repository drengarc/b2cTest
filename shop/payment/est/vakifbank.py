import re
import requests
#from lxml import etree

__author__ = 'buremba'


class Pay():
    def __init__(self, ShopCode, UserCode, UserPass, debug=True):
        self.ShopCode = ShopCode
        self.UserCode = UserCode
        self.UserPass = UserPass
        self.debug = debug

    def pay(self, Pan, Cvv2, month, year, PurchAmount, OrderId, CardType, Currency=949, SecureType="NonSecure",
            InstallmentCount=1, TxnType="Auth", Lang="TR"):
        Expiry = "20" + year + month

        if self.debug:
            url = "https://onlineodemetest.vakifbank.com.tr:4443/VposService/v3/Vposreq.aspx"
        else:
            url = "https://onlineodeme.vakifbank.com.tr:4443/VposService/v3/Vposreq.aspx"

        root = etree.Element('VposRequest')

        data = {"TransactionType": "Sale", "MerchantId": self.UserCode,
                "TerminalNo": self.ShopCode,
                "ClientIp": "190.20.13.12",
                "TransactionDeviceSource": "0",
                "Password": self.UserPass, "Pan": Pan, "Cvv": Cvv2, "SurchargeAmount": "%.2f" % PurchAmount,
                "Expiry": Expiry, "CurrencyAmount": "%.2f" % PurchAmount,
                "OrderId": OrderId, "CurrencyCode": Currency,
                "NumberOfInstallments": None if InstallmentCount < 2 else InstallmentCount}
        for key, value in data.iteritems():
            if value is None:
                continue
            child = etree.Element(key)
            child.text = unicode(value)
            root.append(child)

        r = requests.post(url, data={"prmstr": etree.tostring(root, pretty_print=True)})
        data = etree.fromstring(r.text.encode('utf-8'),
                                parser=etree.XMLParser(ns_clean=True, recover=True, encoding='utf-8'))
        return data.find("ResultCode").text == "0000", data.find("ResultDetail").text

def credit_card_type(cc_number):
    VISA_CC_RE = re.compile(r"^4[0-9]{12}(?:[0-9]{3})?$")
    MASTERCARD_CC_RE = re.compile(r"^5[1-5][0-9]{14}$")

    if MASTERCARD_CC_RE.match(str(cc_number)):
        return 1
    elif VISA_CC_RE:
        return 0
    else:
        return None