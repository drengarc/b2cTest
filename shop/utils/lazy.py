class LazyWrapper:
    def __init__(self, f, args=[], kwargs={}):
        self._override = True
        self._isset = False
        self._value = None
        self._func = f
        self._args = args
        self._kwargs = kwargs
        self._override = False

    def _checkset(self):
        if not self._isset:
            self._override = True
            if isinstance(self._func, str):
                module = self._func.split('.')
                self._func = getattr(__import__(".".join(module[:-1])), module[-1])
            self._value = self._func(*self._args, **self._kwargs)
            self._isset = True
            self._checkset = lambda: True
            self._override = False

    def __getattr__(self, name):
        if getattr(self, '_override'):
            return self.__dict__[name]
        self._checkset()
        return self._value.__getattribute__(name)

    def __setattr__(self, name, val):
        if name == '_override' or self._override:
            self.__dict__[name] = val
            return
        self._checkset()
        setattr(self._value, name, val)
        return


def lazy(f):
    def newf(*args, **kwargs):
        return LazyWrapper(f, args, kwargs)

    return newf