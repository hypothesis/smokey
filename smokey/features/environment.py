import logging
import os
import requests

logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO)

# Configuration default values
CONFIG_DEFAULTS = {
    'api_root': 'https://hypothes.is/api',
    'proxy_root': 'https://via.hypothes.is',
}

# Configuration configurable from the environment
CONFIG_ENV = [
    'api_root',
    'proxy_root',
    'sauce_access_key',
    'sauce_username',
]


def before_all(context):
    # Load config from system environment
    for k in CONFIG_ENV:
        envkey = k.upper()
        if envkey in os.environ:
            context.config.userdata.setdefault(k, os.environ.get(envkey))

    # Load config defaults
    for k, v in CONFIG_DEFAULTS.items():
        context.config.userdata.setdefault(k, v)

    # Set up an HTTP client session with some reasonable defaults (including
    # retrying requests that fail).
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(max_retries=3)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    context.http = session


def before_scenario(context, scenario):
    # Don't run scenarios that require Sauce configuration if it hasn't been
    # provided.
    if 'sauce' in scenario.tags and not _check_sauce_config(context):
        scenario.skip("Sauce config not provided")


def _check_sauce_config(context):
    if 'sauce_username' not in context.config.userdata:
        return False
    if 'sauce_access_key' not in context.config.userdata:
        return False
    return True
