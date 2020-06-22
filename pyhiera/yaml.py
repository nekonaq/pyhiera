import yaml

try:
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeLoader


def load_yaml(*args, Loader=SafeLoader, **kwargs):
    return yaml.load(*args, Loader=Loader, **kwargs)
