import openreview
import pytest
import sys
import time
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import UnexpectedAlertPresentException
from urllib.parse import urlparse, parse_qs

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
            'preferredEmail': 'info@openreview.net' if email == 'openreview.net' else email,
            'homepage': f"https://{fullname.replace(' ', '')}{int(time.time())}.openreview.net",
        }
        profile_content['history'] = [{
            'position': 'PhD Student',
            'start': 2017,
            'end': None,
            'institution': {
                'country': 'US',
                'domain': institution if institution else email.split('@')[1],
            }
        }]
        res = client.activate_user(email, profile_content)
        assert res, "Res i none"
        return client

    @staticmethod
    def get_user(email):
        return openreview.api.OpenReviewClient(baseurl = 'http://localhost:3001', username = email, password = Helpers.strong_password)

    @staticmethod
    def await_queue():

        super_client = openreview.Client(baseurl='http://localhost:3000', username='openreview.net', password=Helpers.strong_password)
        counter = 0
        wait_time = 0.5
        cycles = 60 * 1 / wait_time # print every 1 minutes
        while True:
            jobs = super_client.get_jobs_status()
            jobCount = 0
            for jobName, job in jobs.items():
                if jobName == 'fileUploaderQueueStatus' or jobName == 'fileDeletionQueueStatus':
                    continue
                jobCount += job.get('waiting', 0) + job.get('active', 0) + job.get('delayed', 0)

            if jobCount == 0:
                break

            time.sleep(wait_time)
            if counter % cycles == 0:
                print(f'Jobs in API 1 queue: {jobCount}')
                sys.stdout.flush()

            counter += 1

        assert not [l for l in super_client.get_process_logs(status='error') if l['executedOn'] == 'openreview-api-1']

    @staticmethod
    def await_queue_edit(super_client, edit_id=None, invitation=None, count=1, error=False):
        super_client = Helpers.get_user('openreview.net')
        expected_status = 'error' if error else 'ok'
        counter = 0
        wait_time = 0.5
        cycles = 60 * 1 / wait_time # print every 1 minutes
        while True:
            process_logs = super_client.get_process_logs(id=edit_id, invitation=invitation)
            if len(process_logs) >= count and all(process_log['status'] == expected_status for process_log in process_logs):
                break

            time.sleep(wait_time)
            if counter % cycles == 0:
                print(f'Logs in API 2 queue: {len(process_logs)}', edit_id)
                sys.stdout.flush()

            counter += 1

        assert process_logs[0]['status'] == (expected_status), process_logs[0]['log']

    # This method is used to check if the count value passed as param is correct. It can directly be used to
    # replace the await_queue_edit method in the tests.
    @staticmethod
    def await_queue_edit_tester(super_client, edit_id=None, invitation=None, count=1, error=False, lineno=None):
        super_client = Helpers.get_user('openreview.net')
        expected_status = 'error' if error else 'ok'
        counter = 0
        wait_time = 0.5
        cycles = 60 * 1 / wait_time # print every 1 minutes
        while True:
            process_logs = super_client.get_process_logs(id=edit_id, invitation=invitation)
            if len(process_logs) >= count and all(process_log['status'] == expected_status for process_log in process_logs):
                break

            time.sleep(wait_time)
            if counter % cycles == 0:
                print(f'Logs in API 2 queue: {len(process_logs)}', edit_id)
                sys.stdout.flush()

            counter += 1

        assert process_logs[0]['status'] == (expected_status), process_logs[0]['log']

        counter = 0
        while True:
            process_logs = super_client.get_process_logs(id=edit_id, invitation=invitation)
            if len(process_logs) >= count + 1 and all(process_log['status'] == expected_status for process_log in process_logs):
                print('INCREASE COUNT!!!', edit_id, invitation, lineno)
                break

            time.sleep(wait_time)
            if counter > 10:
                break

            counter += 1


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
        retries = 5
        for retry in range(retries):
            try:
                request_page(selenium, url, by=By.CLASS_NAME, wait_for_element='note_editor')

                container = selenium.find_element(By.CLASS_NAME, 'note_editor')

                buttons = container.find_elements(By.TAG_NAME, "button")

                for button in buttons:
                    counter = 0
                    while not button.is_enabled() and counter < 10:
                        time.sleep(1)
                        counter += 1
                        print(f"Waiting for button to be enabled: {counter}")
                    # assert button.is_enabled()
                    if not button.is_enabled() and retry < retries - 1:
                        selenium.refresh()
                        break
            except Exception as e:
                if retry < retries - 1:
                    selenium.refresh()
                    continue
                else:
                    raise e
                    

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

    @staticmethod
    def respond_invitation_fast(url, accept, quota=None, comment=None):
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)

        invitation = query_params.get('id', [None])[0]
        user_value = query_params.get('user', [None])[0]
        key_value = query_params.get('key', [None])[0]
        submission_id = query_params.get('submission_id', [None])[0]
        inviter = query_params.get('inviter', [None])[0]

        content = {
            'user': {
                'value': user_value
            },
            'key':{
                'value': key_value
            },
            'response': {
                'value': 'Yes' if accept else 'No'
            }
        }

        if quota is not None:
            content['reduced_load'] = {
                'value': str(quota)
            }

        if comment is not None:
            content['comment'] = {
                'value': comment
            }

        if submission_id is not None:
            content['submission_id'] = {
                'value': submission_id
            }

        if inviter is not None:
            content['inviter'] = {
                'value': inviter
            }

        client = openreview.api.OpenReviewClient(baseurl='http://localhost:3001')
        edit = client.post_note_edit(
            invitation,
            None,
            note=openreview.api.Note(content=content),
        )

        super_client = Helpers.get_user('openreview.net')
        Helpers.await_queue_edit(super_client, edit_id=edit['id'])

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
