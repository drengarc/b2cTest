from hashlib import sha1
import json
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection as conn
from django.core.cache import cache as _cache
from simit.models import CustomArea
from django.core.cache import cache
from simit.templatetags.simit_tags import CACHE_TIMEOUT


class Connection:
    def __init__(self, db_conn=conn):
        self.cur = db_conn.cursor()
        # self.cur = conn.connection.cursor(cursor_factory=NamedTupleCursor)

    def _fetchall(self, query, params=[]):
        self.cur.execute(query, params)
        desc = self.cur.description
        return [
            dict(zip([col[0] for col in desc], row))
            for row in self.cur.fetchall()
        ]

    def fetchall(self, query, params=[], cache=False):
        if cache:
            key = "query_cache:" + sha1(query + str(params)).hexdigest()
            result = _cache.get(key)
            if result is None:
                result = self._fetchall(query, params)
                _cache.set(key, result, cache)
            return result
        else:
            return self._fetchall(query, params)

    def fetch(self, query, params=[], cache=False):
        q = self.fetchall(query, params, cache)
        return q[0] if (len(q) > 0) else None


# move to simit extension
def get_custom_variable(slug):
    cache_key = "simit:variable:%s" % slug
    c = cache.get(cache_key)
    if c is not None:
        return c
    try:
        val = CustomArea.objects.get(slug=slug)
        if val.type == 6:
            value = dict(json.loads(val.extra)).get(int(val.value))
        else:
            value = val.value
        if val.type == 5:
            value = True if val == "True" else False
        cache.set(cache_key, value, CACHE_TIMEOUT)
        return value
    except ObjectDoesNotExist:
        return ""

    cache.set(cache_key, val, CACHE_TIMEOUT)