import os


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
