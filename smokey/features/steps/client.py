from behave import *

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class Browsers(object):
    """ Enum of the available browser configurations to test with """
    # Local browsers
    FIREFOX = 'Firefox'
    CHROME = 'Chrome'

    # Sauce Labs Desktop browsers
    SAUCE_CHROME = 'Sauce-Chrome'
    SAUCE_FIREFOX = 'Sauce-Firefox'
    SAUCE_SAFARI = 'Sauce-Safari'
    SAUCE_EDGE = 'Sauce-Edge'


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
        elif browser == Browsers.SAUCE_EDGE:
            start_sauce_browser({'browserName':'MicrosoftEdge'})
        else:
            raise Exception('Unsupported browser')

    def close(self):
        self.driver.quit()


@given('I am using a supported browser')
def connect_browser(context):
    sauce_username = context.config.userdata['sauce_username']
    sauce_access_key = context.config.userdata['sauce_access_key']
    context.browsers = {}
    for row in context.table:
        browser_name = row['browser']
        browser = Browser(browser_name, sauce_username, sauce_access_key)
        context.browsers[browser_name] = browser


@when('I visit "{url}" with Via')
def visit_url_with_proxy(context, url):
    proxy_url = context.config.userdata['proxy_url']
    proxied_url = '{}/{}'.format(proxy_url, url)
    for _, browser in context.browsers.iteritems():
        browser.driver.get(proxied_url)


@then('I should see the Hypothesis sidebar')
def wait_for_hypothesis_sidebar(context):
    SIDEBAR_IFRAME_NAME = 'hyp_sidebar_frame'
    for _, browser in context.browsers.iteritems():
        WebDriverWait(browser.driver, 30).until(
          EC.presence_of_element_located((By.NAME, SIDEBAR_IFRAME_NAME))
        )


@then('I should see at least {count} annotations')
def wait_for_annotations(context, count):
    count = int(count)
    ANNOTATOR_HIGHLIGHT_CLASS = 'annotator-hl'
    for _, browser in context.browsers.iteritems():
        WebDriverWait(browser.driver, 30).until(
          EC.presence_of_element_located((By.CLASS_NAME, ANNOTATOR_HIGHLIGHT_CLASS))
        )
        highlights = browser.driver.find_elements_by_class_name(ANNOTATOR_HIGHLIGHT_CLASS)
        if len(highlights) < count:
            raise Exception('Found only {} annotations'.format(len(highlights)))

