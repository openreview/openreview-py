import openreview
import pytest

@pytest.fixture(scope='session')
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
        'preferredEmail': 'openreview.net'
        })
    assert res, "Res i none"
    group = client.get_group(id = 'openreview.net')
    assert group
    assert group.members == ['~Super_User1']
    yield client

@pytest.fixture(scope='session')
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


@pytest.fixture
def firefox_options(firefox_options):
    firefox_options.add_argument('--headless')
    return firefox_options
