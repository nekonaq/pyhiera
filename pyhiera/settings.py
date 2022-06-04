from pyhiera import Hiera
import logging
import os

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


def load_settings_from_config(hiera_configs, namespace=None, **context):
    for confpath in hiera_configs if isinstance(hiera_configs, (list, tuple)) else (hiera_configs,):
        if not os.path.exists(confpath):
            continue
        logger.info("### config: {}".format(confpath))
        hiera = Hiera.load_data(confpath, context=context)
        hiera_data = hiera.flatten()
        if namespace:
            prefix = '{}_'.format(namespace.upper())
            return {
                key.replace(prefix, ''): val
                for key, val in hiera_data.items()
                if key.startswith(prefix) or key in ('ENVIRONMENT', 'CONFIG')
            }

        return hiera_data

    logger.warning("# WARNING -- no config file found.")
    return {}
