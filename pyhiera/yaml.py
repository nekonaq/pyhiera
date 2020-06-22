import yaml

try:
    from yaml import (
        CSafeLoader as SafeLoader,
        CSafeDumper as SafeDumper,
    )
except ImportError:
    from yaml import (
        SafeLoader,
        SafeDumper,
    )


def load_yaml(*args, Loader=SafeLoader, **kwargs):
    return yaml.load(*args, Loader=Loader, **kwargs)


def dump_yaml(*args, Dumper=SafeDumper, **kwargs):
    return yaml.dump(*args, Dumper=Dumper, **kwargs)
