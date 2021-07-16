import openreview
import pytest
import requests
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import UnexpectedAlertPresentException

class Helpers:
    @staticmethod
    def create_user(email, first, last, alternates=[]):
        client = openreview.Client(baseurl = 'http://localhost:3000')
        assert client is not None, "Client is none"
        res = client.register_user(email = email, first = first, last = last, password = '1234')
        assert res, "Res i none"
        res = client.activate_user(email, {
            'names': [
                    {
                        'first': first,
                        'last': last,
                        'username': '~' + first + '_' + last + '1'
                    }
                ],
            'emails': [email] + alternates,
            'preferredEmail': 'info@openreview.net' if email == 'openreview.net' else email
            })
        assert res, "Res i none"
        return client

    @staticmethod
    def get_user(email):
        return openreview.Client(baseurl = 'http://localhost:3000', username = email, password = '1234')

    @staticmethod
    def await_queue(super_client=None):
        if super_client is None:
            super_client = openreview.Client(baseurl='http://localhost:3000', username='openreview.net', password='1234')
            assert super_client is not None, 'Super Client is none'

        while True:
            jobs = super_client.get_jobs_status()
            jobCount = 0
            for jobName, job in jobs.items():
                jobCount += job.get('waiting', 0) + job.get('active', 0) + job.get('delayed', 0)

            if jobCount == 0:
                break

            time.sleep(0.5)

@pytest.fixture(scope="class")
def helpers():
    return Helpers

@pytest.fixture(scope="session")
def client():
    yield openreview.Client(baseurl = 'http://localhost:3000', username='openreview.net', password='1234')

@pytest.fixture(scope="session")
def openreview_client():
    yield openreview.api.OpenReviewClient(baseurl = 'http://localhost:3001', username='openreview.net', password='1234')

@pytest.fixture(scope="session")
def test_client():
    client = Helpers.create_user('test@mail.com', 'Test', 'User')
    yield client

@pytest.fixture(scope="session")
def peter_client():
    client = Helpers.create_user('peter@mail.com', 'Peter', 'Test')
    yield client

@pytest.fixture(scope="session")
def support_client():
    client = Helpers.create_user('support_user@mail.com', 'Support', 'User')
    yield client

@pytest.fixture
def firefox_options(firefox_options):
    firefox_options.add_argument('--headless')
    return firefox_options

@pytest.fixture
def request_page():
    def request(selenium, url, token = None, alert=False, wait_for_element='content'):
        if token:
            selenium.get('http://localhost:3030')
            selenium.add_cookie({'name': 'openreview.accessToken', 'value': token.replace('Bearer ', ''), 'path': '/', 'sameSite': 'Lax'})
        else:
            selenium.delete_all_cookies()
        selenium.get(url)
        timeout = 5
        if alert:
            try:
                WebDriverWait(selenium, timeout).until(EC.alert_is_present())
                alert = selenium.switch_to.alert
                alert.accept()
            except TimeoutException:
                print("No alert is present")

        try:
            element_present = EC.presence_of_element_located((By.ID, wait_for_element))
            WebDriverWait(selenium, timeout).until(element_present)
            time.sleep(2) ## temporally sleep time to wait until the whole page is loaded
        except TimeoutException:
            print("Timed out waiting for page to load")

    return request
