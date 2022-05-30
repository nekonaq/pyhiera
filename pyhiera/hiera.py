import pathlib

from .exceptions import HieraConfigError
from .hieradata import HieraData
from .yaml import load_yaml

from .backend import yaml_data as backend_yaml_data


class Hiera:
    HIERA_CONFIG_VERSION = 5

    @classmethod
    def load_data(cls, config_file, context=None):
        """ hiera 設定ファイルにもとづいた lookup を行うインスタンス  HieraData を返す
        """
        instance = cls(config_file)
        return instance.get_data(context)

    def __init__(self, config_file):
        self.config_file = pathlib.PosixPath(config_file).absolute()
        self.base_dir = self.config_file.parent

    def __repr__(self):
        return '<{0.__module__}.{0.__name__} config="{self.config_file}">'.format(
            self.__class__,
            self=self,
        )

    def get_data(self, context=None):
        """ hiera 設定ファイルにもとづいた lookup を行うインスタンス  HieraData を返す
        """
        context = context or {}
        with open(self.config_file, 'r') as fp:
            config = load_yaml(fp)

        try:
            self.identify_version(config.pop('version', 0))
            defaults = self.parse_defaults(config.pop('defaults', {}))
            backend_list = self.parse_hierarchy(config.pop('hierarchy', []), defaults, context)
            assert not config, (
                "hiera config has unrecognized key: {}"
                "; config={hiera.config_file}".format(
                    ' '.join(config.keys()),
                    hiera=self,
                )
            )
            # data = HieraData(self, list(itertools.chain(*backend_list)))
            data = HieraData(self, backend_list)

        except AssertionError as err:
            raise HieraConfigError(*err.args)

        return data

    def identify_version(self, version):
        """ hiera 設定ファイルの .version を確認する
        """
        assert version == self.HIERA_CONFIG_VERSION, (
            "unsupported hiera config version, should be '{0}'"
            "; config={hiera.config_file}".format(
                self.HIERA_CONFIG_VERSION,
                hiera=self,
            )
        )

    OPTIONS_DEFAULT = {
        'datadir': 'data',
        'data_hash': 'yaml_data',
    }

    def parse_defaults(self, conf):
        """ hiera 設定ファイルの .defaults を解析して .hierarchy のデフォルト値を得る
        """
        value = self.OPTIONS_DEFAULT.copy()
        value.update(conf)
        unknown_keys = value.keys() - {'datadir', 'data_hash'}
        assert not unknown_keys, (
            "hiera config entry 'defaults' has unrecognized key: {}"
            "; config={hiera.config_file}".format(
                ' '.join(unknown_keys),
                hiera=self,
            )
        )
        return value

    BACKENDS = {
        'yaml_data': backend_yaml_data.HieraBackend,
    }

    def parse_hierarchy(self, conf, defaults, context):
        """ hiera 設定ファイルの .hierarchy を解析してバックエンドのインスタンス列を得る
        """
        assert isinstance(conf, list) and conf, (
            "hiera config has wrong type, entry 'hierarchy' expects a list"
            "; config={hiera.config_file}".format(
                hiera=self,
            )
        )

        for item in conf:
            assert isinstance(item, dict), (
                "hiera config has wrong type, member of entry 'hierarchy' expects a dict"
                "; config={hiera.config_file}".format(
                    hiera=self,
                )

            )
            assert 'name' in item, (
                "hiera config has wrong type, member of entry 'hierarchy' expects a value for key 'name'"
                "; config={hiera.config_file}".format(
                    hiera=self,
                )
            )
            backend_opts = defaults.copy()
            backend_opts.update(item)
            data_hash = backend_opts['data_hash']
            try:
                backend_klass = self.BACKENDS[data_hash]
            except KeyError:
                raise HieraConfigError(
                    "unsupported hiera config data_hash: '{0}'"
                    "; config={hiera.config_file}".format(
                        data_hash,
                        hiera=self,
                    )
                )

            yield backend_klass.create(self, context=context, **backend_opts)
