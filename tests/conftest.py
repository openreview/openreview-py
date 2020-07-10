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
    def create_user(email, first, last):
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
            'emails': [email],
            'preferredEmail': 'info@openreview.net' if email == 'openreview.net' else email
            })
        assert res, "Res i none"
        return client

    @staticmethod
    def get_user(email):
        return openreview.Client(baseurl = 'http://localhost:3000', username = email, password = '1234')

@pytest.fixture
def helpers():
    return Helpers

@pytest.fixture(scope="session")
def client():
    requests.put('http://localhost:3000/reset/openreview.net', json = {'password': '1234'})
    client = openreview.Client(baseurl = 'http://localhost:3000', username='openreview.net', password='1234')
    yield client

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
            selenium.add_cookie({'name': 'openreview.accessToken', 'value': token.replace('Bearer ', ''), 'path': '/', 'sameSite': True})
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
