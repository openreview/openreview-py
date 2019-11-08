import openreview
import pytest
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
    client = Helpers.create_user('openreview.net', 'Super', 'User')
    yield client

@pytest.fixture(scope="session")
def test_client():
    client = Helpers.create_user('test@mail.com', 'Test', 'User')
    yield client

@pytest.fixture(scope="session")
def peter_client():
    client = Helpers.create_user('peter@mail.com', 'Peter', 'Test')
    yield client

@pytest.fixture
def firefox_options(firefox_options):
    firefox_options.add_argument('--headless')
    return firefox_options

@pytest.fixture
def request_page():
    def request(selenium, url, token = None, alert=False):
        if token:
            selenium.get('http://localhost:3000')
            selenium.add_cookie({'name': 'openreview_sid', 'value': token.replace('Bearer ', '')})
        else:
            selenium.delete_all_cookies()
        selenium.get(url)
        if alert:
            try:
                WebDriverWait(selenium, 5).until(EC.alert_is_present(),
                                            'Timed out waiting for PA creation ' +
                                            'confirmation popup to appear.')

                alert = selenium.switch_to.alert
                alert.accept()
                print("alert accepted")
            except TimeoutException:
                print("no alert")

        timeout = 5
        try:
            element_present = EC.presence_of_element_located((By.ID, 'container'))
            WebDriverWait(selenium, timeout).until(element_present)
        except TimeoutException:
            print("Timed out waiting for page to load")

    return request
