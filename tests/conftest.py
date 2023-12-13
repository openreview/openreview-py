import openreview
import pytest
import requests
import time
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import UnexpectedAlertPresentException

class Helpers:
    strong_password = 'Or$3cur3P@ssw0rd'

    @staticmethod
    def create_user(email, first, last, alternates=[], institution=None, fullname=None):

        fullname = f'{first} {last}' if fullname is None else fullname

        super_client = openreview.api.OpenReviewClient(baseurl='http://localhost:3001', username='openreview.net', password=Helpers.strong_password)
        profile = openreview.tools.get_profile(super_client, email)
        if profile:
            return Helpers.get_user(email)

        client = openreview.api.OpenReviewClient(baseurl = 'http://localhost:3001')
        assert client is not None, "Client is none"

        res = client.register_user(email = email, fullname = fullname, password = Helpers.strong_password)
        username = res.get('id')
        assert res, "Res i none"
        profile_content={
            'names': [
                    {
                        'fullname': fullname,
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
        return openreview.api.OpenReviewClient(baseurl = 'http://localhost:3001', username = email, password = Helpers.strong_password)

    @staticmethod
    def await_queue(super_client=None):
        if super_client is None:
            super_client = openreview.Client(baseurl='http://localhost:3000', username='openreview.net', password=Helpers.strong_password)
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
    def await_queue_edit(super_client, edit_id=None, invitation=None, count=1):
        while True:
            process_logs = super_client.get_process_logs(id=edit_id, invitation=invitation)
            if len(process_logs) >= count:
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
    def respond_invitation(selenium, request_page, url, accept, quota=None, comment=None):

        request_page(selenium, url, by=By.CLASS_NAME, wait_for_element='note_editor')

        container = selenium.find_element(By.CLASS_NAME, 'note_editor')

        buttons = container.find_elements(By.TAG_NAME, "button")

        if quota and accept:
            if len(buttons) == 3: ## Accept with quota
                buttons[1].click()
                time.sleep(1)
                dropdown = selenium.find_element(By.CLASS_NAME, 'dropdown-select__input-container')
                dropdown.click()
                time.sleep(1)
                values = selenium.find_elements(By.CLASS_NAME, 'dropdown-select__option')
                assert len(values) > 0
                values[0].click()
                time.sleep(1)
                button = selenium.find_element(By.XPATH, '//button[text()="Submit"]')
                button.click()
            if len(buttons) == 2: ## Decline with quota
                buttons[1].click()
                time.sleep(1)
                reduce_quota_link = selenium.find_element(By.CLASS_NAME, 'reduced-load-link')
                reduce_quota_link.click()
                time.sleep(1)
                dropdown = selenium.find_element(By.CLASS_NAME, 'dropdown-select__input-container')
                dropdown.click()
                time.sleep(1)
                values = selenium.find_elements(By.CLASS_NAME, 'dropdown-select__option')
                assert len(values) > 0
                values[0].click()
                time.sleep(1)
                button = selenium.find_element(By.XPATH, '//button[text()="Submit"]')
                button.click()
        elif comment:
            buttons[2].click() if len(buttons) == 3 else buttons[1].click()
            time.sleep(1)
            text_area = selenium.find_element(By.CSS_SELECTOR, ".note_content_value, [class*='TextareaWidget_textarea']")
            text_area.send_keys("I am too busy.")
            button = selenium.find_element(By.XPATH, '//button[text()="Submit"]')
            button.click()
        elif accept:
            buttons[0].click()
        else:
            buttons[2].click() if len(buttons) == 3 else buttons[1].click()

        time.sleep(2)

        Helpers.await_queue()        

@pytest.fixture(scope="class")
def helpers():
    return Helpers

@pytest.fixture(scope="session")
def client():
    yield openreview.Client(baseurl = 'http://localhost:3000', username='openreview.net', password=Helpers.strong_password)

@pytest.fixture(scope="session")
def openreview_client():
    client = openreview.api.OpenReviewClient(baseurl = 'http://localhost:3001', username='openreview.net', password=Helpers.strong_password)
    yield client

@pytest.fixture(scope="session")
def journal_request():
    client = openreview.api.OpenReviewClient(baseurl = 'http://localhost:3001', username='openreview.net', password=Helpers.strong_password)
    journal_request = openreview.journal.JournalRequest(client, 'openreview.net/Support')
    journal_request.setup_journal_request()
    yield journal_request

@pytest.fixture(scope="session")
def test_client():
    Helpers.create_user('test@mail.com', 'SomeFirstName', 'User')
    yield openreview.Client(baseurl = 'http://localhost:3000', username='test@mail.com', password=Helpers.strong_password)

@pytest.fixture(scope="session")
def peter_client():
    Helpers.create_user('peter@mail.com', 'Peter', 'SomeLastName')
    yield openreview.Client(baseurl = 'http://localhost:3000', username='peter@mail.com', password=Helpers.strong_password)

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
