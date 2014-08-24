import os
import yaml

from fabric.colors import green
from fabric.colors import yellow
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.wait import TimeoutException

from lib.dev.folder import get_test_folder
from lib.error import TaskError
from lib.site.info import SiteInfo


class BrowserDriver(object):

    def __init__(self, site_info, test_folder=None):
        self.browser = None
        self._site_info = site_info
        self.URL = 'url'
        self.TITLE = 'title'
        # Use the default location if not supplied
        if not test_folder:
            test_folder = get_test_folder()
        file_name = os.path.join(
            test_folder, '{}.yaml'.format(self._site_info.site_name)
        )
        self.data = self._load(file_name)
        self._check_urls(file_name)

    def _create_browser(self):
        if not self.browser:
            self.browser = webdriver.Firefox()  # Get local session of firefox

    def _check_urls(self, file_name):
        for item in self.data['urls']:
            if not self.URL in item:
                raise TaskError(
                    "Each item in the list of 'urls' should have a "
                    "'{}': {}".format(self.URL, file_name)
                )
            if not self.TITLE in item:
                raise TaskError(
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
        return data

    def _wait_for_page_to_load(self, url, title):
        try:
            WebDriverWait(self.browser, 10).until(
                lambda driver: title.lower() in driver.title.lower()
            )
        except TimeoutException:
            raise TaskError(
                "Time out waiting for page with title '{}' "
                "to load: {}".format(title, url)
            )

    def test(self):
        self._create_browser()
        # get the home URL
        self._get(self._site_info.url, 'home')
        # get the other URLs
        for item in self.data['urls']:
            url = '{}{}/'.format(self._site_info.url, item.get(self.URL))
            title = item.get(self.TITLE)
            self._get(url, title)

    def close(self):
        if self.browser:
            self.browser.close()
