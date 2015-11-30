from behave import given
from selenium import webdriver

SAUCE_WD_ENDPOINT = ('http://{username}:{access_key}@ondemand.saucelabs.com:80'
                     '/wd/hub')


class UnknownBrowserError(Exception):
    pass


class Browsers(object):
    # Local browsers
    FIREFOX = 'Firefox'
    CHROME = 'Chrome'

    # Sauce Labs Desktop browsers
    SAUCE_CHROME = 'Sauce-Chrome'
    SAUCE_FIREFOX = 'Sauce-Firefox'
    SAUCE_SAFARI = 'Sauce-Safari'
    SAUCE_EDGE = 'Sauce-Edge'


class Browser(object):

    """
    A wrapper around a WebDriver client for a specific browser.
    """

    def __init__(self, browser):
        self.name = browser

    def start(self, context):
        """
        Start the WebDriver instance.

        :param context: The behave execution context
        """
        # Enable browser logging so that we can capture JS errors.
        #
        # N.B. 'loggingPrefs' options are not currently supported for Internet
        # Explorer or Edge.
        self.caps = {'loggingPrefs': {'browser': 'ALL'}}

        # For each named browser, we use the minimal set of capabilities needed
        # to make Sauce Labs or the local WebDriver instance use that browser,
        # letting the testing service pick the appropriate platform, browser
        # version etc. That usually defaults to the current version of the
        # browser on the preferred platform for testing.
        #
        # See https://wiki.saucelabs.com/display/DOCS/Platform+Configurator for
        # Sauce Labs WebDriver configuration settings for various platforms
        if self.name == Browsers.FIREFOX:
            self.caps.update({'browserName': 'firefox'})
            self.driver = webdriver.Firefox(capabilities=self.caps)

        elif self.name == Browsers.CHROME:
            self.caps.update({'browserName': 'chrome'})
            self.driver = webdriver.Chrome(desired_capabilities=self.caps)

        elif self.name == Browsers.SAUCE_SAFARI:
            self.caps.update({'browserName': 'safari',
                              'platform': 'OS X 10.11'})
            self.driver = self._start_sauce_browser(context)

        elif self.name == Browsers.SAUCE_FIREFOX:
            self.caps.update({'browserName': 'firefox'})
            self.driver = self._start_sauce_browser(context)

        elif self.name == Browsers.SAUCE_CHROME:
            self.caps.update({'browserName': 'chrome'})
            self.driver = self._start_sauce_browser(context)

        elif self.name == Browsers.SAUCE_EDGE:
            self.caps.update({'browserName': 'MicrosoftEdge'})
            self.driver = self._start_sauce_browser(context)

        else:
            raise UnknownBrowserError(
                "can't start browser '{}'".format(self.name))

    def close(self):
        """Shut down the WebDriver instance."""
        self.driver.quit()

    def _start_sauce_browser(self, context):
        username = context.config.userdata['sauce_username']
        access_key = context.config.userdata['sauce_access_key']
        sauce_url = SAUCE_WD_ENDPOINT.format(username=username,
                                             access_key=access_key)
        return webdriver.Remote(desired_capabilities=self.caps,
                                command_executor=sauce_url)


@given('I am using supported browser "{browser}"')
def connect_browser(context, browser):
    context.browser = Browser(browser)
    context.browser.start(context)
