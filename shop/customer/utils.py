import decimal
import json


class DecimalJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return [obj.real, obj.imag]
        return super(DecimalJSONEncoder, self).default(obj)