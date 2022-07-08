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
    def create_user(email, first, last, alternates=[], institution=None):
        client = openreview.Client(baseurl = 'http://localhost:3000')
        assert client is not None, "Client is none"
        res = client.register_user(email = email, first = first, last = last, password = '1234')
        username = res.get('id')
        assert res, "Res i none"
        profile_content={
            'names': [
                    {
                        'first': first,
                        'last': last,
                        'username': username,
                        'preferred': True
                    }
                ],
            'emails': [email] + alternates,
            'preferredEmail': 'info@openreview.net' if email == 'openreview.net' else email
        }
        if institution:
            profile_content['history'] = [{
                'position': 'PhD Student',
                'start': 2017,
                'end': None,
                'institution': {
                    'domain': institution
                }
            }]
        res = client.activate_user(email, profile_content)
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

        assert not super_client.get_process_logs(status='error')

    @staticmethod
    def await_queue_edit(super_client, edit_id=None, invitation=None):
        print('await_queue_edit', edit_id)
        while True:
            process_logs = super_client.get_process_logs(id=edit_id, invitation=invitation)
            if process_logs:
                break

            time.sleep(0.5)

        assert process_logs[0]['status'] == 'ok'


    @staticmethod
    def create_reviewer_edge(client, conference, name, note, reviewer, label=None, weight=None):
        conference_id = conference.id
        sac = [conference.get_senior_area_chairs_id(number=note.number)] if conference.use_senior_area_chairs else []
        return client.post_edge(openreview.Edge(
            invitation=f'{conference.id}/Reviewers/-/{name}',
            readers = [conference_id] + sac + [conference.get_area_chairs_id(number=note.number), reviewer] ,
            nonreaders = [conference.get_authors_id(number=note.number)],
            writers = [conference_id] + sac + [conference.get_area_chairs_id(number=note.number)],
            signatures = [conference_id],
            head = note.id,
            tail = reviewer,
            label = label,
            weight = weight
        ))

    @staticmethod
    def respond_invitation(selenium, request_page, url, accept, quota=None):

        request_page(selenium, url, by=By.CLASS_NAME, wait_for_element='note_editor')

        container = selenium.find_element_by_class_name('note_editor')

        buttons = container.find_elements_by_tag_name("button")
        assert len(buttons) == 2

        if quota:
            buttons[1].click() ## Decline
            time.sleep(0.5)
            dropdown = selenium.find_element_by_class_name('dropdown-select__input-container')
            dropdown.click()
            time.sleep(0.5)
            values = selenium.find_elements_by_class_name('dropdown-select__option')
            assert len(values) > 0
            values[0].click()
            time.sleep(0.5)
            button = selenium.find_element_by_xpath('//button[text()="Accept with Reduced Quota"]')
            button.click()
        elif accept:
            buttons[0].click()
        else:
            buttons[1].click()

        time.sleep(1)

        Helpers.await_queue()        

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
    client = Helpers.create_user('test@mail.com', 'SomeFirstName', 'User')
    yield client

@pytest.fixture(scope="session")
def peter_client():
    client = Helpers.create_user('peter@mail.com', 'Peter', 'SomeLastName')
    yield client

@pytest.fixture
def firefox_options(firefox_options):
    firefox_options.add_argument('--headless')
    return firefox_options

@pytest.fixture
def request_page():
    def request(selenium, url, token = None, alert=False, by=By.ID, wait_for_element='content'):
        if token:
            selenium.get('http://localhost:3030')
            selenium.add_cookie({'name': 'openreview.accessToken', 'value': token.replace('Bearer ', ''), 'path': '/', 'sameSite': 'Lax'})
        else:
            selenium.delete_all_cookies()
        selenium.get(url)
        timeout = 8
        if alert:
            try:
                WebDriverWait(selenium, timeout).until(EC.alert_is_present())
                alert = selenium.switch_to.alert
                alert.accept()
            except TimeoutException:
                print("No alert is present")

        try:
            element_present = EC.presence_of_element_located((by, wait_for_element))
            WebDriverWait(selenium, timeout).until(element_present)
            time.sleep(5) ## temporally sleep time to wait until the whole page is loaded
        except TimeoutException:
            print("Timed out waiting for page to load")

    return request
