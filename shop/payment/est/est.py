# -*- coding: utf-8 -*-

###############################################################################################
# Author: Ozgur Vatansever                                                                    #
# Email: ozgurvt@gmail.com                                                                    #
# This library provides a pure Python interface for the EST SanalPOS API.                     #
# Feel free to report bugs, contribute, use in your open source projects without permission.  #
###############################################################################################

"""
This library provides a pure Python interface for the EST SanalPOS API.
"""

import httplib
import urllib
import datetime
import re
import csv
from xml.dom import minidom
from decimal import Decimal, ROUND_UP
from StringIO import StringIO

BANKS = {
    "GARANTI": {
        "host": "ccpos.garanti.com.tr",
        "testhost": "testsanalpos.est.com.tr",
        "listOrdersURL": "/servlet/ozelrapor",
        "detailOrderURL": "/servlet/cc5ApiServer",
        "cancelOrderURL": "/servlet/cc5ApiServer",
        "returnOrderURL": "/servlet/cc5ApiServer",
        "SubmitPost3D": "/servlet/est3Dgate",
        "purchaseOrderURL": "/servlet/cc5ApiServer",
    },
    "tester": {
        "host": "testsanalpos.est.com.tr",
        "testhost": "testsanalpos.est.com.tr",
        "listOrdersURL": "/servlet/ozelrapor",
        "detailOrderURL": "/servlet/cc5ApiServer",
        "cancelOrderURL": "/servlet/cc5ApiServer",
        "returnOrderURL": "/servlet/cc5ApiServer",
        "SubmitPost3D": "/servlet/est3Dgate",
        "purchaseOrderURL": "/servlet/cc5ApiServer",
    },
    "ISBANK": {
        "host": "spos.isbank.com.tr",
        "testhost": "testsanalpos.est.com.tr",
        "test_user": {
            "company": "700200000",
            "username": "ISBANK",
            "password": "ISBANK07",
            "secret_key": "123456",
        },
        "listOrdersURL": "/servlet/listapproved",
        "detailOrderURL": "/servlet/cc5ApiServer",
        "cancelOrderURL": "/servlet/cc5ApiServer",
        "SubmitPost3D": "/servlet/est3Dgate",
        "returnOrderURL": "/servlet/cc5ApiServer",
        "purchaseOrderURL": "/servlet/cc5ApiServer",
    },
    "AKBANK": {
        "host": "www.sanalakpos.com",
        "testhost": "testsanalpos.est.com.tr",
        "listOrdersURL": "/servlet/listapproved",
        "detailOrderURL": "/servlet/cc5ApiServer",
        "cancelOrderURL": "/servlet/cc5ApiServer",
        "returnOrderURL": "/servlet/cc5ApiServer",
        "SubmitPost3D": "/servlet/est3Dgate",
        "purchaseOrderURL": "/servlet/cc5ApiServer",
    },

    "FINANSBANK": {
        "host": "www.fbwebpos.com",
        "test_user": {
            "company": "600100000",
            "username": "FINANSAPI",
            "password": "FINANS06",
            "secret_key": "123456",
        },
        "testhost": "entegrasyon.asseco-see.com.tr",
        "listOrdersURL": "/servlet/listapproved",
        "detailOrderURL": "/servlet/cc5ApiServer",
        "cancelOrderURL": "/servlet/cc5ApiServer",
        "returnOrderURL": "/servlet/cc5ApiServer",
        "SubmitPost3D": "/servlet/est3Dgate",
        "purchaseOrderURL": "/servlet/cc5ApiServer",
    },

    "TEB": {
        "host": "sanalpos.teb.com.tr",
        "test_user": {
            "company": "400000100",
            "username": "TEBAPI",
            "password": "TEBTEB04",
            "secret_key": "123456",
        },
        "testhost": "entegrasyon.asseco-see.com.tr",
        "listOrdersURL": "/servlet/listapproved",
        "detailOrderURL": "/servlet/cc5ApiServer",
        "cancelOrderURL": "/servlet/cc5ApiServer",
        "returnOrderURL": "/servlet/cc5ApiServer",
        "SubmitPost3D": "/servlet/est3Dgate",
        "purchaseOrderURL": "/servlet/cc5ApiServer",
    },

    "HALKBANK": {
        "host": "sanalpos.halkbank.com.tr",
        "testhost": "testsanalpos.est.com.tr",
        "listOrdersURL": "/servlet/listapproved",
        "detailOrderURL": "/servlet/cc5ApiServer",
        "cancelOrderURL": "/servlet/cc5ApiServer",
        "SubmitPost3D": "/servlet/est3Dgate",
        "returnOrderURL": "/servlet/cc5ApiServer",
        "purchaseOrderURL": "/servlet/cc5ApiServer",

    },

    "ANADOLUBANK": {
        "host": "anadolusanalpos.est.com.tr",
        "testhost": "testsanalpos.est.com.tr",
        "listOrdersURL": "/servlet/listapproved",
        "detailOrderURL": "/servlet/cc5ApiServer",
        "cancelOrderURL": "/servlet/cc5ApiServer",
        "SubmitPost3D": "/servlet/est3Dgate",
        "returnOrderURL": "/servlet/cc5ApiServer",
        "purchaseOrderURL": "/servlet/cc5ApiServer",

    },
}


def orderid_required(f):
    def check_orderid(*args, **kwargs):
        orderid = args[1] if len(args) > 1 else None
        orderid = kwargs.get("orderid") if orderid is None else orderid
        if orderid is None:
            raise Exception("Order ID vermelisiniz.")
        return f(*args, **kwargs)

    check_orderid.__doc__ = f.__doc__
    check_orderid.__name__ = f.__name__
    return check_orderid


class XMLBuilder(minidom.Document):
    def __init__(self, tag="CC5Request"):
        """
        This class wrapps around the Document class which is inside the minidom library,
        and provides some utility functions to build up XML document easily.
        """
        minidom.Document.__init__(self)
        self.rootElement = self.createElement(tag)
        self.appendChild(self.rootElement)

    def root(self):
        """
        Gets the root element which is at the top of Dom hierarchy.
        """
        return self.rootElement

    def createElementWithTextNode(self, tagName, nodeValue):
        """
        Creates a dom element with the given tag name and the node value.
        @input: string, string
        @output: DOM Element
        """
        nodeValue = True and nodeValue or ""
        element = self.createElement(str(tagName))
        node = self.createTextNode(str(nodeValue))
        element.appendChild(node)
        return element

    def createElementsWithTextNodes(self, **kwargs):
        """
        Creates a list of DOM Element instances with the given unlimited parameters.
        @input: string, string ...
        @output: [DOM Element, DOM Element, ...]
        """
        return [self.createElementWithTextNode(k, v) for k, v in kwargs.items()]

    def appendListOfElementsToElement(self, element, elements):
        """
        Appends list of DOM elements to the given DOM element.
        """
        for ele in elements:
            element.appendChild(ele)

    def __unicode__(self):
        return self.toxml()

    @staticmethod
    def get_data(xml, s):
        try:
            document = minidom.parseString(str(xml))
            a = document.getElementsByTagName(s)[0]
            return a.childNodes[0].data
        except:
            return ""


class OrderDetail(object):
    """
    Class that represents details of the order issued.
    Corressponds the Order object in Markafoni.
    """

    def __init__(self):
        self.orderid = None
        self.type = None
        self.installment = None
        self.amount = None
        self.code = None
        self.date = None
        self.cardno = None

    def __unicode__(self):
        return "%s - %s" % (self.orderid, self.type)

    def __str__(self):
        return "%s - %s" % (self.orderid, self.type)


class EST(object):
    """
    Base class for the EST interface. EST wraps Garanti, Isbank and Akbank POS services.
    This class provides the methods to:
    - Build up and send a payment transaction,
    - Fetch the details of a transaction,
    - Fetch the details of all the transaction between two datetimes,
    - Cancel the order,
    - Refund any amount from any order.
    """

    def __init__(self, slug, company, name, password, debug=True):
        """
        @slug: is a parameter that indicates which pos service you are going to connected.
        @company: is a string value which is your company id.
        @name: is your username.
        @password: is your password.
        """
        self.slug = slug
        self.debug = debug

        if not self.slug in BANKS.keys():
            raise Exception(
                "Geçersiz bir slug seçtiniz. Seçenekler: garanti, akbank, isbank, finansbank, halkbank, anadolubank")

        self.credientials = self.__get_credientials()
        self.credientials.update({"company": company, "username": name, "password": password})
        self.raw_response = None

    def __get_credientials(self):
        """
        Gets the relevant credientials according to the given
        slug.
        Returns dict or null if couldn't find the crediential.
        input: string
        output: dict or nil
        """
        if hasattr(self, "credientials"):
            return self.credientials
        else:
            if self.slug:
                return BANKS.get(self.slug)
        return None

    def __connect(self):
        """
        Builds up a secure connection between you and the selected POS service.
        May throw exception.
        input: string -> url must be either order detail url or order list url.
        output: HTTPS connection
        """
        c = self.credientials
        if self.debug:
            return httplib.HTTPSConnection(c.get("testhost"))
        else:
            return httplib.HTTPSConnection(c.get("host"))


    def pay(self, credit_card_number, cvv, month, year, amount, installment=None, orderid=None, typ="Auth", **kwargs):
        """
        Sends a direct payment or pre authentication request with the given order id and amount to the POS service.
        Order ID is not necessary. If you don't send it, POS service creates it for you.
        Amount must be greater than 0.0 TL. You can not issue 0 TL.
        Returns True and the details if the payment is successful, otherwise returns False.
        kwargs contains the purchase details like shipping and billing addresses, phone, email

        @input: string x string x string x string x string x string x Decimal x int ...
        @output: bool x dict

        Parameters:
        -----------
        @credit_card_number: 15-16 digits credit card number.
        @cvv: 3-4 digits cvv number
        @year: 2 digits expiry year of the card (fmt: '12' for the year 2012)
        @month: 2 digits expiry month of the card (fmt: '01' for January)
        @amount: amount to be purchased
        @installment: taksit
        @orderid: Order ID

        KWARGS:
        -------
        email = string
        ipaddress = string
        userid = string
        billing_address_name       = string
        billing_address_street1    = string
        billing_address_street2    = string
        billing_address_street3    = string
        billing_address_city       = string
        billing_address_company    = string
        billing_address_postalcode = string
        billing_address_telvoice   = string
        billing_address_state      = string

        shipping_address_name       = string
        shipping_address_street1    = string
        shipping_address_street2    = string
        shipping_address_street3    = string
        shipping_address_city       = string
        shipping_address_company    = string
        shipping_address_postalcode = string
        shipping_address_state      = string
        shipping_address_telvoice   = string
        """

        ###############
        # ASSTERTIONS #
        ###############
        cvv = int(cvv)
        assert type(amount) == Decimal, "The amount is not valid"
        assert isinstance(month, basestring) and isinstance(year, basestring), "Month value is not valid"
        assert isinstance(credit_card_number, basestring) and isinstance(cvv,
                                                                         int), "Credit card number or cvv is not string"
        assert len(credit_card_number) == 15 or len(credit_card_number) == 16, "Credit card number is not valid"
        assert cvv < 1000, "CVV is not valid"
        assert len(year) < 3 and len(month) < 3, "Year value is not valid"
        assert amount > Decimal(0), "Amount must be a positive value"

        #################
        # BEGIN ROUTINE #
        #################
        year = year.zfill(2)
        month = month.zfill(2)
        cvv = str(cvv).zfill(3)
        expires = "%s%s" % (month, year)

        amount = amount.quantize(Decimal("0.1"), rounding=ROUND_UP)

        c = self.credientials
        if self.debug:
            user = c.get('test_user')
            self.credientials.update({"company": user.get('company'), "username": user.get('username'), "password": user.get('password')})
        username = c.get("username")
        password = c.get("password")
        clientid = c.get("company")

        email = kwargs.get("email")
        ipaddress = kwargs.get("ipaddress")
        userid = kwargs.get("userid")

        document = XMLBuilder()
        elements = document.createElementsWithTextNodes(Name=username, Password=password, ClientId=clientid,
                                                        Mode="P", OrderId=orderid, Type=typ, Currency="949",
                                                        GroupId="", TransId="", UserId=userid, Extra="",
                                                        Taksit=installment,
                                                        Number=credit_card_number, Expires=expires, Cvv2Val=cvv,
                                                        Total=str(amount), Email=email, IPAddress=ipaddress)

        document.appendListOfElementsToElement(document.root(), elements)

        billto = document.createElement("BillTo")
        billing_address_name = kwargs.get("billing_address_name")
        billing_address_street1 = kwargs.get("billing_address_street1")
        billing_address_street2 = kwargs.get("billing_address_street2")
        billing_address_street3 = kwargs.get("billing_address_street3")
        billing_address_city = kwargs.get("billing_address_city")
        billing_address_company = kwargs.get("billing_address_company")
        billing_address_postalcode = kwargs.get("billing_address_postalcode")
        billing_address_telvoice = kwargs.get("billing_address_telvoice")
        billing_address_state = kwargs.get("billing_address_state")

        elements = document.createElementsWithTextNodes(Name=billing_address_telvoice, Street1=billing_address_street1,
                                                        Street2=billing_address_street2,
                                                        Street3=billing_address_street3,
                                                        City=billing_address_city, StateProv=billing_address_state,
                                                        PostalCode=billing_address_postalcode,
                                                        Country="Türkiye", Company=billing_address_company,
                                                        TelVoice=billing_address_telvoice)

        document.appendListOfElementsToElement(billto, elements)

        shipto = document.createElement("ShipTo")
        shipping_address_name = kwargs.get("shipping_address_name")
        shipping_address_street1 = kwargs.get("shipping_address_street1")
        shipping_address_street2 = kwargs.get("shipping_address_street2")
        shipping_address_street3 = kwargs.get("shipping_address_street3")
        shipping_address_city = kwargs.get("shipping_address_city")
        shipping_address_company = kwargs.get("shipping_address_company")
        shipping_address_postalcode = kwargs.get("shipping_address_postalcode")
        shipping_address_telvoice = kwargs.get("shipping_address_telvoice")
        shipping_address_state = kwargs.get("shipping_address_state")

        elements = document.createElementsWithTextNodes(Name=shipping_address_telvoice,
                                                        Street1=shipping_address_street1,
                                                        Street2=shipping_address_street2,
                                                        Street3=shipping_address_street3,
                                                        City=shipping_address_city, StateProv=shipping_address_state,
                                                        PostalCode=shipping_address_postalcode,
                                                        Country="Türkiye", Company=shipping_address_company,
                                                        TelVoice=shipping_address_telvoice)

        document.appendListOfElementsToElement(shipto, elements)
        document.appendListOfElementsToElement(document.root(), [billto, shipto])

        service = self.__connect()
        URL = c.get("purchaseOrderURL")
        method = "POST"
        headers = {'Content-type': 'application/x-www-form-urlencoded'}
        xml = document.toxml()
        body = urllib.urlencode({"DATA": xml})

        # If debug mode is enabled, dump the HTTP request!
        if self.debug:
            print "HTTP Request"
            print "HOST    : %s:%d%s" % (service.host, service.port, URL)
            print "Header  : %s" % str(headers)
            print "Request : %s" % xml
            # end of debugging request

        service.request(method=method, url=URL, body=body, headers=headers)
        httpresponse = service.getresponse()
        response = httpresponse.read()
        service.close()
        self.raw_response = response

        # If debug mode is enabled, dump the HTTP response!
        if self.debug:
            print
            print "HTTP Response"
            print "Header   : %s" % str(httpresponse.getheaders())
            print "Status   : %d" % httpresponse.status
            print "Response : %s" % response
            # end of debugging response

        try:
            result_dict = {}
            response_utf = minidom.parseString(response).toxml("utf-8")
            orderid = XMLBuilder.get_data(response_utf, "OrderId")
            groupid = XMLBuilder.get_data(response_utf, "GroupId")
            transid = XMLBuilder.get_data(response_utf, "TransId")
            response = XMLBuilder.get_data(response_utf, "Response")
            return_code = XMLBuilder.get_data(response_utf, "ProcReturnCode")
            error_msg = XMLBuilder.get_data(response_utf, "ErrMsg")
            host_msg = XMLBuilder.get_data(response_utf, "HOSTMSG")
            trx_date = XMLBuilder.get_data(response_utf, "TRXDATE")
            auth_code = XMLBuilder.get_data(response_utf, "AuthCode")
            try:
                result = not (True and int(return_code)) or False
            except:
                result = False

            try:
                trx_date = datetime.datetime.strptime(trx_date.split(".")[0], "%Y-%m-%d %H:%M:%S")
            except:
                pass

            result_dict.update({"orderid": orderid, "transid": transid, "groupid": groupid, "response": response,
                                "return_code": return_code, "error_msg": error_msg, "host_msg": host_msg,
                                "transaction_time": trx_date, "auth_code": auth_code})

            return result, result_dict['error_msg']
        except Exception, detail:
            return False, {"exception": str(detail)}
        return False, {}
        ###############
        # END ROUTINE #
        ###############


    @orderid_required
    def cancel(self, orderid=None, transid=None):
        """
        Sends a cancel request for the given orderid to the POS service. If successful, returns True.
        Otherwise returns False. Also gives the xml response sent from the POS service.
        If you want to cancel a refund request or a postAuth request, then you must give the transaction ID
        to this method.
        @input: string
        @output: dict
        """
        ##############
        # ASSERTIONS #
        ##############
        assert type(orderid) == str

        #################
        # BEGIN ROUTINE #
        #################

        c = self.credientials
        username = c.get("username")
        password = c.get("password")
        clientid = c.get("company")

        document = XMLBuilder()
        elements = document.createElementsWithTextNodes(Name=username, Password=password, ClientId=clientid,
                                                        Mode="P", OrderId=orderid, Type="Void", Currency="949")
        document.appendListOfElementsToElement(document.root(), elements)
        if transid:
            element = document.createElementWithTextNode("TransId", transid)
            document.root().appendChild(element)

        service = self.__connect()
        method = "POST"
        url = c.get("cancelOrderURL")
        headers = {'Content-type': 'application/x-www-form-urlencoded'}
        xml = document.toxml()

        # If debug mode is enabled, dump the HTTP request!
        if self.debug:
            print "HTTP Request"
            print "HOST    : %s:%d%s" % (service.host, service.port, url)
            print "Header  : %s" % str(headers)
            print "Request : %s" % xml
            # end of debugging request

        body = urllib.urlencode({"DATA": xml})
        service.request(method=method, url=url, body=body, headers=headers)
        httpresponse = service.getresponse()
        response = httpresponse.read()
        service.close()
        self.raw_response = response

        # If debug mode is enabled, dump the HTTP response!
        if self.debug:
            print
            print "HTTP Response"
            print "Header   : %s" % str(httpresponse.getheaders())
            print "Status   : %d" % httpresponse.status
            print "Response : %s" % response
            # end of debugging response


        ###################
        # PARSING PROCESS #
        ###################
        try:
            response_utf = minidom.parseString(response).toxml("utf-8")
            orderid = XMLBuilder.get_data(response_utf, "OrderId")
            groupid = XMLBuilder.get_data(response_utf, "GroupId")
            transid = XMLBuilder.get_data(response_utf, "TransId")
            resp = XMLBuilder.get_data(response_utf, "Response")
            return_code = XMLBuilder.get_data(response_utf, "ProcReturnCode")
            err_msg = XMLBuilder.get_data(response_utf, "ErrMsg")
            host_msg = XMLBuilder.get_data(response_utf, "HOSTMSG")
            host_ref_num = XMLBuilder.get_data(response_utf, "HostRefNum")
            auth_code = XMLBuilder.get_data(response_utf, "AuthCode")
            trx_date = XMLBuilder.get_data(response_utf, "TRXDATE")

            try:
                result = not (True and int(return_code)) or False
            except:
                result = False

            try:
                trx_date = datetime.datetime.strptime(trx_date.split(".")[0], "%Y-%m-%d %H:%M:%S")
            except:
                pass

            _dict = {"orderid": orderid, "transid": transid, "groupid": groupid, "response": resp, "error_msg": err_msg,
                     "host_msg": host_msg, "host_ref_num": host_ref_num, "return_code": return_code,
                     "auth_code": auth_code,
                     "transaction_time": trx_date}

            return result, _dict
        except Exception, detail:
            return False, {"exception": str(detail)}
            ###############
            # END ROUTINE #
            ###############


    @orderid_required
    def refund(self, amount, orderid=None):
        """
        Sends a refund request for the given orderid to the POS service. If successful, returns True.
        Otherwise returns False. Also gives the xml response sent from the POS service.
        @input: Decimal x string
        @output: dict
        """
        #################
        # BEGIN ROUTINE #
        #################

        c = self.credientials
        username = c.get("username")
        password = c.get("password")
        clientid = c.get("company")

        document = XMLBuilder()
        elements = document.createElementsWithTextNodes(Name=username, Password=password, ClientId=clientid,
                                                        Mode="P", OrderId=orderid, Type="Credit", Currency="949",
                                                        Total=str(amount))

        document.appendListOfElementsToElement(document.root(), elements)

        service = self.__connect()
        method = "POST"
        url = c.get("returnOrderURL")
        xml = document.toxml()
        body = urllib.urlencode({"DATA": xml})
        headers = {'Content-type': 'application/x-www-form-urlencoded'}

        # If debug mode is enabled, dump the HTTP request!
        if self.debug:
            print "HTTP Request"
            print "HOST    : %s:%d%s" % (service.host, service.port, url)
            print "Request : %s" % xml
            # end of debugging request

        service.request(method=method, url=url, body=body, headers=headers)
        httpresponse = service.getresponse()
        response = httpresponse.read()
        service.close()

        # If debug mode is enabled, dump the HTTP response!
        if self.debug:
            print
            print "HTTP Response"
            print "Header   : %s" % str(httpresponse.getheaders())
            print "Status   : %d" % httpresponse.status
            print "Response : %s" % response
            # end of debugging response


        ###################
        # PARSING PROCESS #
        ###################
        try:
            response_utf = minidom.parseString(response).toxml("utf-8")
            orderid = XMLBuilder.get_data(response_utf, "OrderId")
            groupid = XMLBuilder.get_data(response_utf, "GroupId")
            transid = XMLBuilder.get_data(response_utf, "TransId")
            resp = XMLBuilder.get_data(response_utf, "Response")
            return_code = XMLBuilder.get_data(response_utf, "ProcReturnCode")
            err_msg = XMLBuilder.get_data(response_utf, "ErrMsg")
            host_ref_num = XMLBuilder.get_data(response_utf, "HostRefNum")
            host_msg = XMLBuilder.get_data(response_utf, "HOSTMSG")
            trx_date = XMLBuilder.get_data(response_utf, "TRXDATE")
            auth_code = XMLBuilder.get_data(response_utf, "AuthCode")

            try:
                result = not (True and int(return_code)) or False
            except:
                result = False

            try:
                trx_date = datetime.datetime.strptime(trx_date.split(".")[0], "%Y-%m-%d %H:%M:%S")
            except:
                pass

            _dict = {"orderid": orderid, "transid": transid, "groupid": groupid, "response": resp, "error_msg": err_msg,
                     "host_msg": host_msg, "return_code": return_code, "host_ref_num": host_ref_num,
                     "auth_code": auth_code,
                     "transaction_time": trx_date}

            return result, _dict
        except Exception, detail:
            return False, {"exception": str(detail)}
            ###############
            # END ROUTINE #
            ###############


    @orderid_required
    def postAuth(self, amount, orderid=None, transid=None):
        """
        Issues a PostAuth request to the API server.
        Can be reversed by cancel() method.
        @input: Decimal, string
        @output: dict
        """
        ##############
        # ASSERTIONS #
        ##############
        assert type(amount) == Decimal and amount > Decimal(0)
        assert type(orderid) == str

        print orderid
        #################
        # BEGIN ROUTINE #
        #################
        c = self.credientials

        amount = amount.quantize(Decimal("0.01"), rounding=ROUND_UP)

        ##########################################################################
        # First of all, we need to get the credientials and relevant information #
        # to build up the HTTP body.                                             #
        ##########################################################################
        username = c.get("username")
        password = c.get("password")
        clientid = c.get("company")
        url = c.get("listOrdersURL")
        method = "POST"

        document = XMLBuilder()
        elements = document.createElementsWithTextNodes(Name=username, Password=password, ClientId=clientid,
                                                        Mode="P", OrderId=orderid, Type="PostAuth",
                                                        Total=str(amount), Extra=None, TransId=transid)
        document.appendListOfElementsToElement(document.root(), elements)

        service = self.__connect()
        method = "POST"
        url = c.get("returnOrderURL")
        headers = {'Content-type': 'application/x-www-form-urlencoded'}
        xml = document.toxml()
        # If debug mode is enabled, dump the HTTP request!
        if self.debug:
            print "HTTP Request"
            print "HOST    : %s:%d%s" % (service.host, service.port, url)
            print "Request : %s" % xml
            # end of debugging request

        body = urllib.urlencode({"DATA": xml})
        service.request(method=method, url=url, body=body, headers=headers)
        httpresponse = service.getresponse()
        response = httpresponse.read()
        service.close()

        # If debug mode is enabled, dump the HTTP response!
        if self.debug:
            print
            print "HTTP Response"
            print "Header   : %s" % str(httpresponse.getheaders())
            print "Status   : %d" % httpresponse.status
            print "Response : %s" % response
            # end of debugging response


        ###################
        # PARSING PROCESS #
        ###################
        try:
            response_utf = minidom.parseString(response).toxml("utf-8")
            orderid = XMLBuilder.get_data(response_utf, "OrderId")
            groupid = XMLBuilder.get_data(response_utf, "GroupId")
            transid = XMLBuilder.get_data(response_utf, "TransId")
            resp = XMLBuilder.get_data(response_utf, "Response")
            return_code = XMLBuilder.get_data(response_utf, "ProcReturnCode")
            err_msg = XMLBuilder.get_data(response_utf, "ErrMsg")
            host_ref_num = XMLBuilder.get_data(response_utf, "HostRefNum")
            host_msg = XMLBuilder.get_data(response_utf, "HOSTMSG")
            trx_date = XMLBuilder.get_data(response_utf, "TRXDATE")
            auth_code = XMLBuilder.get_data(response_utf, "AuthCode")

            try:
                result = not (True and int(return_code)) or False
            except:
                result = False

            try:
                trx_date = datetime.datetime.strptime(trx_date.split(".")[0], "%Y-%m-%d %H:%M:%S")
            except:
                pass

            _dict = {"orderid": orderid, "transid": transid, "groupid": groupid, "response": resp, "error_msg": err_msg,
                     "host_msg": host_msg, "return_code": return_code, "host_ref_num": host_ref_num,
                     "auth_code": auth_code,
                     "transaction_time": trx_date}

            return result, _dict
        except Exception, detail:
            return False, {"exception": str(detail)}
            ###############
            # END ROUTINE #
            ###############


    def getDetails(self, start_date=datetime.datetime.now() - datetime.timedelta(days=15),
                   end_date=datetime.datetime.now()):
        """
        Fetches the order details issued between the given dates.
        input: datetime, datetime (fmt: yyyy-mm-dd HH:MM:SS)
        output: dict
        The result is a dict which contains the list including the orderdetail instances,
        satis toplam, satis adet, iade toplam and iade adet values.
        """
        #################
        # BEGIN ROUTINE #
        #################
        c = self.credientials

        ##########################################################################
        # First of all, we need to get the credientials and relevant information #
        # to build up the HTTP body.                                             #
        ##########################################################################
        username = c.get("username")
        password = c.get("password")
        clientid = c.get("company")
        url = c.get("listOrdersURL")
        method = "POST"

        ###############################################
        # time format is different for each service.  #
        ###############################################

        # format is yyyy:mm:dd H:M:S
        if self.slug == "garanti":
            startDate = datetime.datetime.strftime(start_date, "%Y%m%d%H%M")
            endDate = datetime.datetime.strftime(end_date, "%Y%m%d%H%M")
        else:
            startDate = datetime.datetime.strftime(start_date, "%Y-%m-%d %H:%M:%S")
            endDate = datetime.datetime.strftime(end_date, "%Y-%m-%d %H:%M:%S")


            ###################################################################
            # <form method="{method}" action="https://{host}{url}">           #
        #     <input type="text"  name="clientid" value="{clientid}" />   #
        #     <input type="text"  name="username" value="{username}" />   #
        #     <input type="text"  name="password" value="{password}" />   #
        #     <input type="text"  name="startdate" value="{startDate}" /> #
        #     <input type="text"  name="enddate" value="{endDate}" />     #
        #     <input type="text"  name="fileformat" value="txt" />        #
        # </form>                                                         #
        ###################################################################

        post_dict = {"clientid": clientid, "username": username, "password": password, "fileformat": "txt"}
        if self.slug == "garanti":
            post_dict.update({"startdate": startDate, "enddate": endDate})
        else:
            post_dict.update({"startdatetime": startDate, "enddatetime": endDate})

        service = self.__connect()
        body = urllib.urlencode(post_dict)
        headers = {'Content-type': 'application/x-www-form-urlencoded'}

        # If debug mode is enabled, dump the HTTP request!
        if self.debug:
            print "HTTP Request"
            print "HOST    : %s:%d%s" % (service.host, service.port, url)
            print "Request : %s" % body
            # end of debugging request

        service.request(method=method, url=url, body=body, headers=headers)
        httpresponse = service.getresponse()
        response = httpresponse.read()
        service.close()
        self.raw_response = response

        # If debug mode is enabled, dump the HTTP response!
        if self.debug:
            print
            print "HTTP Response"
            print "Header   : %s" % str(httpresponse.getheaders())
            print "Status   : %d" % httpresponse.status
            print "Response : %s" % response
            # end of debugging response

        ############################################################################################################
        # PARSING PROCESS                                                                                          #
        # Resulting response is a weird text response.                                                             #
        # That can be parsed easily with csv or xlrd libraries so we are going to shape it in a from using regular #
        # expression library.                                                                                      #
        ############################################################################################################
        try:
            io = StringIO(response)
            reader = csv.reader(io, delimiter=";")
            reader.next()
            details = []
            for line in reader:
                detail_obj = OrderDetail()
                detail_obj.orderid = line[1]
                detail_obj.type = line[2]
                detail_obj.installment = line[3]
                detail_obj.amount = Decimal(str(line[5]))
                detail_obj.code = line[6]
                try:
                    detail_obj.date = datetime.datetime.strptime(line[8].split(".")[0], "%Y-%m-%d %H:%M:%S")
                except:
                    detail_obj.date = line[8]
                detail_obj.cardno = line[10]
                details.append(detail_obj)
            return {"details": details}
        except Exception, detail:
            return {"err_msg": str(detail)}
        finally:
            io.close()
            ###############
            # END ROUTINE #
            ###############


    @orderid_required
    def getDetail(self, orderid=None):
        """
        Fetches the order detail through the POS XML API.
        input: orderid: string
        The result is a OrderDetail instance which contains details of the order
        or None if it couldn't be found any information related to it.
        """
        #################
        # BEGIN ROUTINE #
        #################
        c = self.__get_credientials()
        username = c.get("username")
        password = c.get("password")
        clientid = c.get("company")

        ######################################################################
        # We need to build up the xml body of the request using dom library. #
        # The host and url is obvious and declared in credientials.          #
        ######################################################################

        document = XMLBuilder("CC5Request")
        ######################################
        # <CC5Request>                       #
        #   <Name>{username}</Name>SDSFDSF   #
        #   <Password>{password}</Password>  #
        #   <ClientId>{clientid}</ClientId>  #
        #   <Mode>P</Mode>                   #
        #   <OrderId>{orderid}</OrderId>     #
        #   <Extra>                          #
        #     <ORDERSTATUS>SOR</ORDERSTATUS> #
        #   </Extra>                         #
        # </CC5Request>                      #
        ######################################

        elements = document.createElementsWithTextNodes(Name=username, Password=password, ClientId=clientid, Mode="P",
                                                        OrderId=orderid)
        document.appendListOfElementsToElement(document.root(), elements)
        element = document.createElement("Extra")
        statusElement = document.createElement("ORDERSTATUS")
        statusElement.appendChild(document.createTextNode("SOR"))
        element.appendChild(statusElement)
        document.root().appendChild(element)

        service = self.__connect()
        url = c.get("detailOrderURL")
        method = "POST"
        headers = {'Content-type': 'application/x-www-form-urlencoded'}
        xml = document.toxml()

        # If debug mode is enabled, dump the HTTP request!
        if self.debug:
            print "HTTP Request"
            print "HOST    : %s:%d%s" % (service.host, service.port, url)
            print "Request : %s" % xml
            # end of debugging request

        body = urllib.urlencode({"DATA": xml})
        service.request(method=method, url=url, body=body, headers=headers)
        httpresponse = service.getresponse()
        response = httpresponse.read()
        service.close()
        self.raw_response = response

        # If debug mode is enabled, dump the HTTP response!
        if self.debug:
            print
            print "HTTP Response"
            print "Header   : %s" % str(httpresponse.getheaders())
            print "Status   : %d" % httpresponse.status
            print "Response : %s" % response
            # end of debugging response

        response_utf = minidom.parseString(response).toxml("utf-8")
        transid = XMLBuilder.get_data(response_utf, "TransId")
        return_code = XMLBuilder.get_data(response_utf, "ProcReturnCode")
        err_msg = XMLBuilder.get_data(response_utf, "ErrMsg")
        details = XMLBuilder.get_data(response_utf, "ORDERSTATUS")

        result_dict = {"transid": transid, "orderid": orderid, "return_code": return_code, "error_msg": err_msg,
                       "amount": "", "auth_code": "", "transaction_time": ""}

        detail_regexp = re.compile("^.*CAPTURE_AMT:(?P<capture_amt>[\d|\.]+).*CAPTURE_DTTM:(.*)AUTH_CODE:(.*)$")
        matched = detail_regexp.match(details)
        if matched:
            groups = matched.groups()
            amount = groups[0].strip()
            trx_date = groups[1].strip()
            auth_code = groups[2].strip()

            try:
                amount = Decimal(amount)
            except:
                pass

            try:
                trx_date = datetime.datetime.strptime(trx_date.split(".")[0], "%Y-%m-%d %H:%M:%S")
            except:
                pass

            result_dict.update({"auth_code": auth_code, "amount": amount, "transaction_time": trx_date})

        return result_dict
        ###############
        # END ROUTINE #
        ###############