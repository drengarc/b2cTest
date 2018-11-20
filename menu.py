# coding: utf-8
"""
This file was generated with the custommenu management command, it contains
the classes for the admin menu, you can customize this class as you want.

To activate your custom menu add the following to your settings.py::
    ADMIN_TOOLS_MENU = 'b2ctest.menu.CustomMenu'
"""
import copy

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from admin_tools.menu import items, Menu

menus = []
lastmenus = []


def register_menu_item(func):
    menus.append(func())
    return func


def register_last_menu_item(func):
    lastmenus.append(func())
    return func


class CustomMenu(Menu):

    def init_with_context(self, context):

        self.children += [
            items.MenuItem(_('Dashboard'), reverse('admin:index')),
        ]

        for menufunc in menus:
            self.children.append(copy.deepcopy(menufunc))

        self.children += [
            items.ModelList(
                _('User'),
                models=('django.contrib.auth.*',)
            ),
        ]

        for menufunc in lastmenus:
            self.children.append(copy.deepcopy(menufunc))