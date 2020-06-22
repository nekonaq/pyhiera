import itertools
from .exceptions import HieraConfigError


class HieraDataItem(dict):
    def __init__(self, backend, num=0, **kwargs):
        self.backend = backend
        self.num = num
        self.init_kwargs = kwargs

    def __repr__(self):
        return '<{0.__module__}.{0.__name__} config="{hiera.config_file}" name="{backend.name}" {self.num}>'.format(
            self.__class__,
            hiera=self.backend.hiera,
            backend=self.backend,
            self=self,
        )


class HieraData:
    DOESNOTEXIST = object()

    def __init__(self, hiera, backend_list):
        self.hiera = hiera
        self.backend_list = backend_list

    def __repr__(self):
        return '<{0.__module__}.{0.__name__} config="{hiera.config_file}">'.format(
            self.__class__,
            hiera=self.hiera,
        )

    def lookup_first(self, key, default=None):
        """ hiera 設定ファイルの .hierarchy から key の値を first merge で得る
        """
        ret = next((item[key] for item in self.values if key in item), default)
        return ret

    def lookup_hash(self, key, default=None):
        """ hiera 設定ファイルの .hierarchy から key の値を hash merge で得る
        """
        values = list(filter(
            lambda el: el is not self.DOESNOTEXIST,
            (el.get(key, self.DOESNOTEXIST) for el in self.values)
        ))
        ret = {}
        found = False
        for item in reversed(values):
            found = True
            if not isinstance(item, dict):
                raise HieraConfigError(
                    "all 'hash' merged matching values must be a hash, key: '{0}'"
                    "; config={hiera.config_file}".format(
                        key,
                        hiera=self.hiera,
                    )
                )
            ret.update(item)
        return ret if found else default

    def lookup_unique(self, key, default=None):
        """ hiera 設定ファイルの .hierarchy から key の値を unique merge で得る
        """
        values = list(filter(
            lambda el: el is not self.DOESNOTEXIST,
            (el.get(key, self.DOESNOTEXIST) for el in self.values)
        ))
        ret = []
        found = False
        for item in values:
            found = True
            if isinstance(item, list):
                ret.extend([el for el in item if el not in ret])
            elif isinstance(item, dict):
                raise HieraConfigError(
                    "all 'unique' merged matching values must not be a hash, key: '{0}'"
                    "; config={hiera.config_file}".format(
                        key,
                        hiera=self.hiera,
                    )
                )
            elif item not in ret:
                ret.append(item)

        return ret if found else default

    def merge_deep(self, lval, rval):
        if rval is self.DOESNOTEXIST:
            return lval

        if lval is self.DOESNOTEXIST:
            return rval.copy() if isinstance(rval, (dict, list)) else rval

        if isinstance(lval, dict) and isinstance(rval, dict):
            return {
                key: self.merge_deep(lval.get(key, self.DOESNOTEXIST), rval.get(key, self.DOESNOTEXIST))
                for key in set(lval) | set(rval)
            }

        if isinstance(lval, list) and isinstance(rval, list):
            lval.extend([el for el in rval if el not in lval])
            return lval

        return rval

    def lookup_deep(self, key, default=None):
        """ hiera 設定ファイルの .hierarchy から key の値を deep merge で得る
        """
        values = list(filter(
            lambda el: el is not self.DOESNOTEXIST,
            (el.get(key, self.DOESNOTEXIST) for el in self.values)
        ))
        ret = self.DOESNOTEXIST
        found = False
        for item in reversed(values):
            found = True
            if not isinstance(item, dict):
                raise HieraConfigError(
                    "all 'hash' merged matching values must be a hash, key: '{0}'"
                    "; config={hiera.config_file}".format(
                        key,
                        hiera=self.hiera,
                    )
                )
            ret = self.merge_deep(ret, item)
        return ret if found else default

    STRATEGY_METHOD = {
        'first': lookup_first,
        'hash': lookup_hash,
        'unique': lookup_unique,
        'deep': lookup_deep,
    }

    @property
    def lookup_options(self):
        """ hiera 設定ファイルの .hierarchy から 'lookup_options' の値を lookup first で得る
        """
        try:
            return self._looup_options
        except AttributeError:
            pass
        ret = self._looup_options = self.lookup_first('lookup_options', default={})
        return ret

    def lookup(self, key, default=None, strategy=None):
        strategy = strategy or self.lookup_options.get(key, {}).get('merge') or 'first'
        try:
            meth = self.STRATEGY_METHOD[strategy]
        except KeyError:
            raise HieraConfigError(
                "unknown hiera lookup strategy '{0}' for key: '{1}'"
                "; config={hiera.config_file}".format(
                    strategy,
                    key,
                    hiera=self.hiera,
                )
            )

        return meth(self, key, default=default)

    @property
    def values(self):
        try:
            return self._values
        except AttributeError:
            pass
        ret = self._values = list(itertools.chain(*[backend.data for backend in self.backend_list]))
        return ret

    def flatten(self):
        keys = set.union(*[set(el) for el in self.values]) - {'lookup_options'}
        return {
            key: self.lookup(key)
            for key in keys
        }
