import decimal
import json


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return round(float(obj), 2)
        return json.JSONEncoder.default(self, obj)

json.encoder.FLOAT_REPR = lambda o: format(o, '.1f')