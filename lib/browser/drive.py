import os
import yaml

from fabric.colors import green
from fabric.colors import yellow
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.wait import TimeoutException

from lib.site.info import INFO_FOLDER


class DriverError(Exception):

    def __init__(self, value):
        Exception.__init__(self)
        self.value = value

    def __str__(self):
        return repr('%s, %s' % (self.__class__.__name__, self.value))


class BrowserDriver(object):

    def __init__(self, site_name, post_deploy_folder=None):
        self.browser = None
        self.URL = 'url'
        self.TITLE = 'title'
        # Use the default location if not supplied
        if not post_deploy_folder:
            post_deploy_folder = os.path.join(INFO_FOLDER, 'post-deploy')
        file_name = os.path.join(
            post_deploy_folder, '{}.txt'.format(site_name)
        )
        self.urls = self._load(file_name)
        self._check_urls(file_name)

    def _create_browser(self):
        if not self.browser:
            self.browser = webdriver.Firefox()  # Get local session of firefox

    def _check_urls(self, file_name):
        for item in self.urls:
            if not self.URL in item:
                raise DriverError(
                    "Each item in the list of 'urls' should have a "
                    "'{}': {}".format(self.URL, file_name)
                )
            if not self.TITLE in item:
                raise DriverError(
                    "Each item in the list of 'urls' should have a "
                    "'{}': {}".format(self.TITLE, file_name)
                )

    def _get(self, url, title):
        print(yellow(url)),
        self.browser.get(url)
        self._wait_for_page_to_load(url, title)
        print(green("OK (found {})".format(title)))

    def _load(self, file_name):
        with open(file_name, 'r') as f:
            data = yaml.load(f)
        return data['urls']

    def _wait_for_page_to_load(self, url, title):
        try:
            WebDriverWait(self.browser, 10).until(
                lambda driver: title.lower() in driver.title.lower()
            )
        except TimeoutException:
            raise DriverError(
                "Time out waiting for page with title '{}' "
                "to load: {}".format(title, url)
            )

    def test(self):
        self._create_browser()
        for item in self.urls:
            url = item.get(self.URL)
            title = item.get(self.TITLE)
            self._get(url, title)

    def close(self):
        if self.browser:
            self.browser.close()
