from behave import when, then

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

H_HIGHLIGHT_CLASS = 'annotator-hl'
H_SIDEBAR_IFRAME_NAME = 'hyp_sidebar_frame'


@when('I visit "{url}" with Via')
def visit_url_with_proxy(context, url):
    proxy_root = context.config.userdata['proxy_root']
    proxied_url = '{}/{}'.format(proxy_root, url)
    context.browser.driver.get(proxied_url)


@then('I should see the Hypothesis sidebar')
def wait_for_hypothesis_sidebar(context):
    driver = context.browser.driver
    saw_sidebar = EC.presence_of_element_located((By.NAME,
                                                  H_SIDEBAR_IFRAME_NAME))
    WebDriverWait(driver, 30).until(saw_sidebar)


@then('I should see at least {count} annotations')
def wait_for_annotations(context, count):
    count = int(count)
    driver = context.browser.driver
    saw_highlight = EC.presence_of_element_located((By.CLASS_NAME,
                                                    H_HIGHLIGHT_CLASS))
    WebDriverWait(driver, 30).until(saw_highlight)

    highlights = driver.find_elements_by_class_name(H_HIGHLIGHT_CLASS)

    if len(highlights) < count:
        raise Exception('Found only {} annotations'.format(len(highlights)))
