import re
from pyhiera.exceptions import HieraConfigError
from pyhiera.yaml import load_yaml
from pyhiera.hieradata import HieraDataItem


class HieraBackend:
    backend_name = 'yaml_data'

    def __init__(self, hiera, name=None, datadir=None, data_hash=None, context=None, **kwargs):
        self.hiera = hiera
        self.name = name
        self.datadir = datadir
        self.context = context or {}       # global context from Hiera
        try:
            self.paths = kwargs.pop('paths')
        except KeyError:
            try:
                self.paths = [kwargs.pop('path')]
            except KeyError:
                raise HieraConfigError(
                    "hiera config has wrong type, member of entry 'hierarchy' expects a value for key 'path' or 'paths'"
                    "; config={hiera.config_file}".format(
                        hiera=self.hiera,
                    )
                )

        assert not kwargs, (
            "hiera config member '{self.name}' of entry 'hierarchy' has unrecognized key: {0}"
            "; config={hiera.config_file}".format(
                ' '.join(kwargs.keys()),
                self=self,
                hiera=self.hiera,
            )
        )

    RE_INTERPOLATE = re.compile(r'%\x1b(?:::)?([.\w\[\]]+)\x1d')
    CHAR_LB = chr(ord('{') & 0x1f)         # '\x1b'
    CHAR_RB = chr(ord('}') & 0x1f)         # '\x1d'
    TRANS_BRACES = str.maketrans('{}', ''.join([CHAR_LB, CHAR_RB]))

    def resolve_str(self, value):
        ret = value.translate(self.TRANS_BRACES)
        ret = self.RE_INTERPOLATE.sub('{\g<1>}', ret)  # noqa: W605
        ret = ret.replace(self.CHAR_LB, '{{').replace(self.CHAR_RB, '}}')
        return ret.format(**self.context)

    def resolve_data(self, value):
        if isinstance(value, str):
            return self.resolve_str(value)

        if isinstance(value, list):
            return [self.resolve_data(el) for el in value]

        if isinstance(value, dict):
            return {
                key: self.resolve_data(val)
                for key, val in value.items()
            }
        return value

    def load(self):
        for num, path in enumerate(self.paths):
            resolved = self.resolve_str(path)
            realpath = self.hiera.base_dir.joinpath(self.datadir, resolved)
            try:
                with realpath.open('r') as fp:
                    data = load_yaml(fp)
            except IOError:
                data = {}
            data_item = HieraDataItem(self, num=num, path=realpath)
            data_item.update(data or {})
            yield data_item

    @property
    def data(self):
        try:
            return self._data
        except AttributeError:
            pass
        data = self.load()
        ret = self._data = self.resolve_data(list(data))
        return ret
