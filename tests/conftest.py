import openreview
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

@pytest.fixture(scope="session")
def client():
    client = openreview.Client(baseurl = 'http://localhost:3000')
    assert client is not None, "Client is none"
    res = client.register_user(email = 'openreview.net', first = 'Super', last = 'User', password = '1234')
    assert res, "Res i none"
    res = client.activate_user('openreview.net', {
        'names': [
                {
                    'first': 'Super',
                    'last': 'User',
                    'username': '~Super_User1'
                }
            ],
        'emails': ['openreview.net'],
        'preferredEmail': 'info@openreview.net'
        })
    assert res, "Res i none"
    group = client.get_group(id = 'openreview.net')
    assert group
    assert group.members == ['~Super_User1']
    yield client

@pytest.fixture(scope="session")
def test_client():
    test_client = openreview.Client(baseurl = 'http://localhost:3000')
    assert test_client is not None, "Client is none"
    res = test_client.register_user(email = 'test@mail.com', first = 'Test', last = 'User', password = '1234')
    assert res, "Res i none"
    res = test_client.activate_user('test@mail.com', {
        'names': [
                {
                    'first': 'Test',
                    'last': 'User',
                    'username': '~Test_User1'
                }
            ],
        'emails': ['test@mail.com'],
        'preferredEmail': 'test@mail.com'
        })
    assert res, "Res i none"
    group = test_client.get_group(id = 'test@mail.com')
    assert group
    assert group.members == ['~Test_User1']
    yield test_client

@pytest.fixture(scope="session")
def peter_client():
    peter_client = openreview.Client(baseurl = 'http://localhost:3000')
    assert peter_client is not None, "Client is none"
    res = peter_client.register_user(email = 'peter@mail.com', first = 'Peter', last = 'Test', password = '1234')
    assert res, "Res i none"
    res = peter_client.activate_user('peter@mail.com', {
        'names': [
                {
                    'first': 'Peter',
                    'last': 'Test',
                    'username': '~Peter_Test1'
                }
            ],
        'emails': ['peter@mail.com'],
        'preferredEmail': 'peter@mail.com'
        })
    assert res, "Res i none"
    group = peter_client.get_group(id = 'peter@mail.com')
    assert group
    assert group.members == ['~Peter_Test1']
    yield peter_client


@pytest.fixture
def firefox_options(firefox_options):
    firefox_options.add_argument('--headless')
    return firefox_options

@pytest.fixture
def request_page():
    def request(selenium, url, token = None):
        if token:
            selenium.get('http://localhost:3000')
            selenium.add_cookie({'name': 'openreview_sid', 'value': token.replace('Bearer ', '')})
        else:
            selenium.delete_all_cookies()
        selenium.get(url)
        timeout = 5
        try:
            element_present = EC.presence_of_element_located((By.ID, 'container'))
            WebDriverWait(selenium, timeout).until(element_present)
        except TimeoutException:
            print("Timed out waiting for page to load")
    return request
