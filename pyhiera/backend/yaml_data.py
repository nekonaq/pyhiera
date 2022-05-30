import re
import pprint
# from pyhiera.exceptions import HieraConfigError
from pyhiera.hieradata import HieraDataItem
from pyhiera.log import logger
from pyhiera.yaml import load_yaml


class HieraYamlPaths:
    name = 'paths'

    def __init__(self, hiera, args, name=None, datadir=None, data_hash=None, context=None):
        self.hiera = hiera
        self.args = args
        self.name = name
        self.datadir = datadir
        self.data_hash = data_hash
        self.context = context or {}       # global context from Hiera

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
        for num, path in enumerate(self.args):
            resolved = self.resolve_str(path)
            realpath = self.hiera.base_dir.joinpath(self.datadir, resolved)
            logger.debug('realpath={}'.format(realpath))
            try:
                with realpath.open('r') as fp:
                    data = load_yaml(fp)
            except IOError:
                data = {}
            logger.debug('data={}'.format(pprint.pformat(data)))
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


class HieraYamlPath(HieraYamlPaths):
    name = 'path'

    def __init__(self, hiera, args, name=None, datadir=None, data_hash=None, context=None):
        super().__init__(hiera, [args], name=name, datadir=datadir, data_hash=data_hash, context=context)


class HieraYamlGlobs(HieraYamlPaths):
    name = 'globs'

    def load(self):
        for num, path in enumerate(self.args):
            resolved = self.resolve_str(path)
            for realpath in self.hiera.base_dir.joinpath(self.datadir).glob(resolved):
                logger.debug('realpath={}'.format(realpath))
                try:
                    with realpath.open('r') as fp:
                        data = load_yaml(fp)
                except IOError:
                    data = {}

                logger.debug('data={}'.format(pprint.pformat(data)))
                data_item = HieraDataItem(self, num=num, path=realpath)
                data_item.update(data or {})
                yield data_item


class HieraYamlGlob(HieraYamlGlobs):
    name = 'glob'

    def __init__(self, hiera, args, name=None, datadir=None, data_hash=None, context=None):
        super().__init__(hiera, [args], name=name, datadir=datadir, data_hash=data_hash, context=context)


class HieraBackend:
    name = 'yaml_data'

    BACKEND_CLASSES = [
        HieraYamlPaths,
        HieraYamlPath,
        HieraYamlGlobs,
        HieraYamlGlob,
    ]

    @classmethod
    def create(self, hiera, name=None, datadir=None, data_hash=None, context=None, **kwargs):
        backend = None
        args = []
        for item in self.BACKEND_CLASSES:
            if item.name in kwargs:
                args = kwargs.pop(item.name)
                backend = item
                break

        assert backend is not None, (
            "hiera config has wrong hierarchy type"
            "; config={hiera.config_file}".format(
                hiera=hiera,
            )
        )

        assert not kwargs, (
            "hiera config member '{name}' of entry 'hierarchy' has unrecognized key: {0}"
            "; config={hiera.config_file}".format(
                ' '.join(kwargs.keys()),
                name=self.name,
                hiera=hiera,
            )
        )

        return backend(hiera, args, name=name, datadir=datadir, data_hash=data_hash, context=context)


    '''
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
    '''
