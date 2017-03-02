#!/usr/bin/env python

from __future__ import print_function

from argparse import ArgumentParser
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import functools
import logging
import os
from Queue import Queue
import sys
import threading
import yaml


class Browsers(object):
    """ Enum of the available browser configurations to test with """
    # Local browsers
    FIREFOX = 'firefox'
    CHROME = 'chrome'

    # Sauce Labs Desktop browsers
    SAUCE_CHROME = 'sauce/chrome'
    SAUCE_FIREFOX = 'sauce/firefox'
    SAUCE_SAFARI = 'sauce/safari'

    # Sauce Labs Windows Desktop browsers
    SAUCE_IE = 'sauce/ie'
    SAUCE_EDGE = 'sauce/edge'

    # Sauce Labs mobile browsers
    SAUCE_IPHONE = 'sauce/iphone'
    SAUCE_ANDROID = 'sauce/android'


# Returns true if an error message reported by a browser
# should be ignored when checking for JavaScript errors
def _should_ignore_console_error(msg):
    IGNORED_ERRORS = [
      # Chrome requests $HOST/favicon.ico for each page it fetches
      # and logs an error if not found
      'favicon.ico'
    ]
    for ignore_pattern in IGNORED_ERRORS:
        if ignore_pattern in msg:
            return True
    return False


class Browser(object):
    """ Browser handles initialization of the WebDriver client
        for a given browser.

        :browser: Name of the browser from the Browsers enum.
    """
    def __init__(self, browser, sauce_username=None, sauce_access_key=None):
        self.name = browser
        """The name of the connected browser"""

        # enable browser logging so that we can capture JS
        # errors.
        #
        # 'loggingPrefs' options are not currently
        # supported for Internet Explorer or Edge
        caps = {'loggingPrefs' : {'browser':'ALL'}}

        # see https://wiki.saucelabs.com/display/DOCS/Platform+Configurator
        # for Sauce Labs WebDriver configuration settings for various
        # platforms
        def start_sauce_browser(platform_caps):
            if not sauce_username:
                raise ValueError('Cannot connect to Sauce Labs without a Sauce username')
            if not sauce_access_key:
                raise ValueError('Cannot connect to Sauce Labs without a Sauce access key')

            sauce_url = 'http://%s:%s@ondemand.saucelabs.com:80/wd/hub' % \
              (sauce_username, sauce_access_key)

            caps.update(platform_caps)
            self.driver = webdriver.Remote(
              desired_capabilities=caps,
              command_executor=sauce_url
            )

        # for each named browser, we use the minimal set
        # of capabilities needed to make Sauce Labs or the
        # local WebDriver instance use that browser - letting
        # the testing service pick the appropriate platform,
        # browser version etc. since that usually defaults
        # to the current version of the browser on the preferred
        # platform for testing.

        if browser == Browsers.FIREFOX:
            caps.update({'browserName':'firefox'})
            self.driver = webdriver.Firefox(capabilities=caps)
        elif browser == Browsers.CHROME:
            caps.update({'browserName':'chrome'})
            self.driver = webdriver.Chrome(desired_capabilities=caps)
        elif browser == Browsers.SAUCE_SAFARI:
            start_sauce_browser({
                'browserName': 'safari',
                'platform': 'OS X 10.11',
            })
        elif browser == Browsers.SAUCE_FIREFOX:
            start_sauce_browser({'browserName':'firefox'})
        elif browser == Browsers.SAUCE_CHROME:
            start_sauce_browser({'browserName':'chrome'})
        elif browser == Browsers.SAUCE_IE:
            start_sauce_browser({'browserName':'internet explorer'})
        elif browser == Browsers.SAUCE_EDGE:
            start_sauce_browser({'browserName':'MicrosoftEdge'})
        elif browser == Browsers.SAUCE_IPHONE:
            start_sauce_browser({'browserName':'iPhone'})
        elif browser == Browsers.SAUCE_ANDROID:
            start_sauce_browser({'browserName':'android'})
        else:
            raise Exception('Unsupported browser')

        # flush the logging on startup.
        # Firefox for example logs a large number of debug and info
        # messages on startup
        if self.supports_js_error_reporting():
            self.list_js_errors()

    def close(self):
        self.driver.quit()

    def supports_js_error_reporting(self):
        if self.name in [Browsers.SAUCE_IE, Browsers.SAUCE_EDGE]:
            return False
        else:
            return True

    def list_js_errors(self):
        """Parses the console log from WebDriver and returns a list
           of JS errors reported since the previous list_js_errors() call.

           Not all browsers support this command. Use supports_js_error_reporting()
           to test for JS error reporting support before calling this.
        """
        if not self.supports_js_error_reporting():
            raise Exception('{0} does not support JS error reporting'.format(self.name))

        """ Checks whether the browser reported any JavaScript errors. """
        errors = [entry['message'] for entry in self.driver.get_log('browser')
                  if entry['level'] == 'SEVERE']
        return filter(lambda error: not _should_ignore_console_error(error), errors)


def test_url_in_browser(url, browser):
    """ Tests that the given URL loads in Via with a specified browser """

    browser.driver.get(url)
    errors = []

    # wait for the Hypothesis sidebar to load
    SIDEBAR_IFRAME_NAME = 'hyp_sidebar_frame'
    try:
        WebDriverWait(browser.driver, 10).until(
          EC.presence_of_element_located((By.NAME, SIDEBAR_IFRAME_NAME))
        )
    except Exception as ex:
        errors.append('Failed to detect sidebar: {0}'.format(ex))

    # check for JS errors
    if browser.supports_js_error_reporting():
        js_errors = browser.list_js_errors()
        for error in js_errors:
            errors.append('JavaScript error reported: {0}'.format(error))

    return errors


def test_browser(browser_name, config, result_queue, sauce_username=None, sauce_access_key=None):
    """ Connects to a given browser and runs the set of tests specified in 'config' against it """
    logger = logging.getLogger(browser_name)
    logger.info('Connecting to browser')
    browser = Browser(browser_name, sauce_username, sauce_access_key)
    had_error = False
    for url in config['urls']:
        logger.info('Testing {url}'.format(url=url))
        via_url = '%s/%s' % (config['service_url'], url)
        try:
            errors = test_url_in_browser(via_url, browser)
            if len(errors) > 0:
                for error in errors:
                    logger.error('ERROR: {0}'.format(error))
                logger.error('FAIL: {url}'.format(url=url))
                had_error = True
            else:
                logger.info('PASS: {url}'.format(url=url))
        except Exception as ex:
            logger.exception('FAIL: {url}'.format(url=url))
            had_error = True
    logger.info('Shutting down browser')
    result_queue.put((browser_name, not had_error))


def main():
    parser = ArgumentParser(description=
"""Performs an end-to-end test of the Via service
against a set of URLs and with a given set of browsers.
""")
    parser.add_argument('-c,--config', dest='config',
                        help='Specifies the configuration to use for the test run',
                        required=True)
    parser.add_argument('-l,--log-level', dest='loglevel',
                        help='Specifies the logging level',
                        choices=['debug', 'info', 'warning', 'error'],
                        default='info')
    args = parser.parse_args()

    loglevel = getattr(logging, args.loglevel.upper())
    logging.basicConfig(level=loglevel)

    sauce_username = os.environ.get('SAUCE_USERNAME')
    sauce_access_key = os.environ.get('SAUCE_ACCESS_KEY')

    # start a thread for each browser we want to test
    config = yaml.load(open(args.config))
    threads = []
    result_queue = Queue()
    for browser_name in config['browsers']:
        thread = threading.Thread(target=functools.partial(test_browser,
          browser_name, config, sauce_username=sauce_username,
          sauce_access_key=sauce_access_key,
          result_queue=result_queue))
        threads.append(thread)
        thread.start()

    # wait for all browser threads to exit and check
    # whether any reported errors
    for thread in threads:
        thread.join()

    while not result_queue.empty():
        (browser, ok) = result_queue.get()
        if not ok:
            sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    main()
