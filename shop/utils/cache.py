from django.core.cache import cache
from hashlib import sha1

DEFAULT_CACHE_TIMEOUT = 60


def get_cache(key, lamb, timeout=DEFAULT_CACHE_TIMEOUT):
    c = cache.get(key)
    if c is not None:
        return c

    f = lamb()
    cache.set(key, f, timeout)
    return f


def cache_func(seconds=DEFAULT_CACHE_TIMEOUT):
    def do_cache(f):
        def x(*args, **kwargs):
            key = sha1(str(f.__module__) + str(f.__name__) + str(args) + str(kwargs)).hexdigest()
            result = cache.get(key)
            if result is None:
                result = f(*args, **kwargs)
                cache.set(key, result, seconds)
            return result

        return x

    return do_cache
