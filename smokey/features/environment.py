import logging
import functools
import os
import requests

from behave.model import ScenarioOutline


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


def autoretry_scenario(scenario_or_outline):
    """
    Monkey-patches Scenario.run() to auto-retry a scenario that fails.

    This has been accepted upstream for Behave 1.2.6 as
    behave.contrib.scenario_autoretry (see
    https://github.com/behave/behave/commit/ca7259b7)
    """
    def run_scenario(original_run, *args, **kwargs):
        max_attempts = 3
        passed = False
        for attempt in range(1, max_attempts+1):
            if original_run(*args, **kwargs):
                print('Auto-retrying scenario (attempt {})'.format(attempt))
            else:
                passed = True
                break

        if passed:
            return False

        print('Scenario failed after {} attempts'.format(max_attempts))
        return True

    if isinstance(scenario_or_outline, ScenarioOutline):
        for scenario in scenario_or_outline.scenarios:
            original_run = scenario.run
            scenario.run = functools.partial(run_scenario, original_run)
    else:
        original_run = scenario.run
        scenario_or_outline.run = functools.partial(run_scenario, original_run)


def before_feature(context, feature):
    for scenario in feature.scenarios:
        if 'autoretry' in scenario.tags:
            autoretry_scenario(scenario)


def before_scenario(context, scenario):
    # Don't run scenarios that require Sauce configuration if it hasn't been
    # provided.
    if 'sauce' in scenario.tags and not _check_sauce_config(context):
        scenario.skip("Sauce config not provided")


def after_scenario(context, scenario):
    # Shut down any webdriver instances that were started by the scenario.
    if hasattr(context, 'browser'):
        context.browser.close()


def _check_sauce_config(context):
    if 'sauce_username' not in context.config.userdata:
        return False
    if 'sauce_access_key' not in context.config.userdata:
        return False
    return True
