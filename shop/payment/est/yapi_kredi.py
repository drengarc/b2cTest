from lxml import etree
import re
import requests

__author__ = 'buremba'


class YapiKrediPay():
    def __init__(self, ShopCode, UserCode, UserPass, debug=True):
        self.ShopCode = ShopCode
        self.UserCode = UserCode
        self.UserPass = UserPass
        self.debug = debug

    def pay(self, Pan, Cvv2, month, year, PurchAmount, OrderId, CardType, Currency=949, SecureType="NonSecure",
            InstallmentCount=1, TxnType="Auth", Lang="TR"):
        Expiry = month + year

        if self.debug:
            url = "http://setmpos.ykb.com/PosnetWebService/XML"
        else:
            url = "https://www.posnet.ykb.com/PosnetWebService/XML"

        root = etree.Element('posnetRequest')
        child = etree.Element("mid")
        child.text = unicode(self.UserCode)
        root.append(child)

        child = etree.Element("tid")
        child.text = unicode(self.ShopCode)
        root.append(child)

        sale = {"amount": "%.0f" % PurchAmount,
                "ccno": Pan,
                "currencyCode": "YT",
                "cvc": Cvv2,
                "expDate": Expiry,
                "orderID": "000000000000"+OrderId,
                "installment": None if InstallmentCount < 2 else InstallmentCount
        }

        sale_root = etree.Element("sale")
        root.append(sale_root)

        for key, value in sale.iteritems():
            if value is None:
                continue
            child = etree.Element(key)
            child.text = unicode(value)
            sale_root.append(child)

        r = requests.post(url, data={"xmldata": etree.tostring(root, pretty_print=True)})
        data = etree.fromstring(r.text.encode('utf-8'),
                                parser=etree.XMLParser(ns_clean=True, recover=True, encoding='utf-8'))
        return data.find("approved") == "1", data.find("respText")