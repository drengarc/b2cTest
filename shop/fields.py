from django import forms
from django.db import models


class IntegerRangeField(models.IntegerField):
    def __init__(self, verbose_name=None, name=None, min_value=None, max_value=None, **kwargs):
        self.min_value, self.max_value = min_value, max_value
        models.IntegerField.__init__(self, verbose_name, name, **kwargs)

    def formfield(self, **kwargs):
        defaults = {'min_value': self.min_value, 'max_value': self.max_value}
        defaults.update(kwargs)
        return super(IntegerRangeField, self).formfield(**defaults)


class VectorField(models.Field):
    def __init__(self, *args, **kwargs):
        kwargs['null'] = kwargs.get('null', True)
        kwargs['default'] = kwargs.get('default', '')
        kwargs['editable'] = kwargs.get('editable', False)
        kwargs['serialize'] = kwargs.get('serialize', False)
        kwargs['db_index'] = kwargs.get('db_index', True)
        super(VectorField, self).__init__(*args, **kwargs)

    def db_type(self, *args, **kwargs):
        return 'tsvector'

    def formfield(self, **kwargs):
        defaults = {'widget': forms.TextInput}
        defaults.update(kwargs)
        return super(VectorField, self).formfield(**defaults)

    def get_db_prep_lookup(self, lookup_type, value, connection, prepared=False):
        return self.get_prep_lookup(lookup_type, value)

    def get_prep_value(self, value):
        return value