from pyhiera import Hiera
import logging
import os

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


def load_settings_from_config(hiera_configs, **context):
    for confpath in hiera_configs if isinstance(hiera_configs, (list, tuple)) else (hiera_configs,):
        if not os.path.exists(confpath):
            continue
        logger.info("### config: {}".format(confpath))
        # print("### config:", confpath)
        hiera = Hiera.load_data(confpath, context=context)
        hiera_data = hiera.flatten()
        return hiera_data

    logger.warning("# WARNING -- no config file found.")
    return {}
