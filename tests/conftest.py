import openreview
import pytest

@pytest.fixture(scope='session')
def client():
    client = openreview.Client()
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
