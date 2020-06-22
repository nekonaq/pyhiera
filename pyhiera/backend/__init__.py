# import itertools
from ..exceptions import HieraConfigError
from . import yaml_data as backend_yaml_data


class HieraBackendBase:
    pass


class HieraData:
    BACKENDS = {
        'yaml_data': backend_yaml_data.HieraBackend,
    }

    @classmethod
    def parse_hierarchy(cls, hiera, conf, defaults):
        assert isinstance(conf, list) and conf, (
            "hiera config has wrong type, entry 'hierarchy' expects a list"
        )
        for item in conf:
            assert isinstance(item, dict), (
                "hiera config has wrong type, member of entry 'hierarchy' expects a dict"
            )
            assert 'name' in item, (
                "hiera config has wrong type, member of entry 'hierarchy' expects a value for key 'name'"
            )
            item.update(defaults)
            data_hash = item['data_hash']
            try:
                backend_klass = cls.BACKENDS[data_hash]
            except KeyError:
                raise HieraConfigError("unsupported hiera config data_hash: '{}'".format(data_hash))

            yield backend_klass(hiera, **item).load()

    def flatten(self):
        return {}
