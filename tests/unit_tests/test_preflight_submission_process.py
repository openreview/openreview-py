from unittest.mock import MagicMock, patch

import pytest
import requests

import openreview
from openreview.journal.invitation import InvitationBuilder
from openreview.journal.process import under_review_submission_process
from openreview.journal.process.preflight_submission_process import process

VENUE_ID = 'SLADS'
DEV_URL = 'https://preflight-dev.example.invalid/api/submissions'
PROD_URL = 'https://preflight-prod.example.invalid/api/submissions'
DEV_TOKEN = 'dummy-dev-token'
PROD_TOKEN = 'dummy-prod-token'
FORUM_ID = 'forum_abc123'
PREFLIGHT_INVITATION_ID = 'SLADS/-/Preflight_Submission'


def make_settings(enabled=True, url=DEV_URL, token=DEV_TOKEN):
    return {'enable_preflight_submission': enabled, 'preflight_url': url, 'preflight_token': token}


def make_journal(settings=None):
    return openreview.journal.Journal(MagicMock(), VENUE_ID, 'secret', 'contact@example.com',
        'SLADS Journal', 'SLADS', 'sladsfour.com', 'Submission', settings or make_settings())


def make_note(venueid='SLADS/Under_Review', forum=FORUM_ID):
    note = MagicMock()
    note.id = forum
    note.forum = forum
    note.number = 1
    note.content = {
        'title': {'value': 'Paper title'},
        'venueid': {'value': venueid},
    }
    return note


def make_response(status_code=200, text='ok'):
    response = MagicMock()
    response.status_code = status_code
    response.ok = status_code < 400
    response.text = text
    return response


def run_process(settings=None, venueid='SLADS/Under_Review', forum=FORUM_ID):
    journal = make_journal(settings)
    client = MagicMock()
    client.get_note.return_value = make_note(venueid=venueid, forum=forum)
    edit = MagicMock()
    edit.note.id = forum
    with patch('openreview.journal.Journal', return_value=journal):
        process(client, edit, MagicMock())


class TestPreflightSubmissionProcess:

    @patch('requests.post')
    def test_successful_invocation_posts_to_preflight(self, mock_post):
        mock_post.return_value = make_response(200)

        run_process()

        mock_post.assert_called_once()

    @patch('requests.post')
    def test_request_contains_forum_id(self, mock_post):
        mock_post.return_value = make_response(200)

        run_process(forum=FORUM_ID)

        assert mock_post.call_args.kwargs['json'] == {'forum_id': FORUM_ID}

    @patch('requests.post')
    def test_request_method_url_headers_and_timeout(self, mock_post):
        mock_post.return_value = make_response(200)

        run_process()

        args, kwargs = mock_post.call_args
        assert args == (DEV_URL,)
        assert kwargs['headers'] == {'Authorization': f'Bearer {DEV_TOKEN}'}
        assert 'X-API-Key' not in kwargs['headers']
        assert kwargs['timeout'] == 30

    @patch('requests.post')
    def test_dev_journal_uses_dev_url_and_token(self, mock_post):
        mock_post.return_value = make_response(200)

        run_process(make_settings(url=DEV_URL, token=DEV_TOKEN))

        assert mock_post.call_args.args[0] == DEV_URL
        assert mock_post.call_args.kwargs['headers']['Authorization'] == f'Bearer {DEV_TOKEN}'
        assert PROD_URL not in str(mock_post.call_args)
        assert PROD_TOKEN not in str(mock_post.call_args)

    @patch('requests.post')
    def test_prod_journal_uses_prod_url_and_token(self, mock_post):
        mock_post.return_value = make_response(200)

        run_process(make_settings(url=PROD_URL, token=PROD_TOKEN))

        assert mock_post.call_args.args[0] == PROD_URL
        assert mock_post.call_args.kwargs['headers']['Authorization'] == f'Bearer {PROD_TOKEN}'
        assert DEV_URL not in str(mock_post.call_args)
        assert DEV_TOKEN not in str(mock_post.call_args)

    @patch('requests.post')
    def test_disabled_journal_does_not_call_preflight(self, mock_post):
        run_process(make_settings(enabled=False))

        mock_post.assert_not_called()

    @patch('requests.post')
    def test_missing_enable_flag_does_not_call_preflight(self, mock_post):
        run_process({'preflight_url': DEV_URL, 'preflight_token': DEV_TOKEN})

        mock_post.assert_not_called()

    @patch('requests.post')
    def test_missing_url_fails_without_sending_request(self, mock_post):
        with pytest.raises(openreview.OpenReviewException) as exc_info:
            run_process(make_settings(url=None))

        assert exc_info.value.args[0]['name'] == 'PreflightConfigurationError'
        assert 'preflight_url' in exc_info.value.args[0]['message']
        mock_post.assert_not_called()

    @patch('requests.post')
    def test_missing_token_fails_without_sending_request(self, mock_post):
        with pytest.raises(openreview.OpenReviewException) as exc_info:
            run_process(make_settings(token=None))

        assert exc_info.value.args[0]['name'] == 'PreflightConfigurationError'
        assert 'preflight_token' in exc_info.value.args[0]['message']
        mock_post.assert_not_called()

    @patch('requests.post')
    def test_http_error_raises_openreview_exception(self, mock_post):
        mock_post.return_value = make_response(500, text='internal error')

        with pytest.raises(openreview.OpenReviewException) as exc_info:
            run_process()

        assert exc_info.value.args[0] == {
            'name': 'PreflightServiceError',
            'message': 'internal error',
            'status': 500,
        }

    @patch('requests.post')
    def test_connection_failure_raises_openreview_exception(self, mock_post):
        mock_post.side_effect = requests.ConnectionError('connection refused')

        with pytest.raises(openreview.OpenReviewException) as exc_info:
            run_process()

        assert exc_info.value.args[0]['name'] == 'PreflightConnectionError'

    @patch('requests.post')
    def test_timeout_raises_openreview_exception_without_retry(self, mock_post):
        mock_post.side_effect = requests.Timeout('timed out')

        with pytest.raises(openreview.OpenReviewException) as exc_info:
            run_process()

        assert exc_info.value.args[0]['name'] == 'PreflightTimeoutError'
        assert mock_post.call_count == 1

    @pytest.mark.parametrize('venueid', [
        'SLADS/Submitted',
        'SLADS/Desk_Rejected',
        'SLADS/Withdrawn_Submission',
        'SLADS/Rejected',
    ])
    @patch('requests.post')
    def test_unsupported_stages_do_not_trigger_preflight(self, mock_post, venueid):
        run_process(venueid=venueid)

        mock_post.assert_not_called()

    @patch('requests.post')
    def test_duplicate_invocation_sends_one_request_per_run(self, mock_post):
        # The process itself does not retry or dedupe. Duplicate protection comes from
        # the Preflight invitation's maxReplies=1, which the server enforces per submission.
        mock_post.return_value = make_response(200)

        run_process()
        run_process()

        assert mock_post.call_count == 2
        assert all(c.kwargs['json'] == {'forum_id': FORUM_ID} for c in mock_post.call_args_list)

    @pytest.mark.parametrize('error', [
        requests.ConnectionError(f'failed to reach {DEV_URL}'),
        requests.Timeout('timed out'),
    ])
    @patch('requests.post')
    def test_token_not_exposed_in_exception_messages(self, mock_post, error):
        mock_post.side_effect = error

        with pytest.raises(openreview.OpenReviewException) as exc_info:
            run_process()

        assert DEV_TOKEN not in str(exc_info.value)

    @patch('requests.post')
    def test_token_not_exposed_in_http_error_message(self, mock_post):
        mock_post.return_value = make_response(401, text='unauthorized')

        with pytest.raises(openreview.OpenReviewException) as exc_info:
            run_process()

        assert DEV_TOKEN not in str(exc_info.value)


class TestUnderReviewTriggersPreflight:

    def run_under_review(self, settings):
        journal = MagicMock()
        journal.venue_id = VENUE_ID
        journal.should_enable_preflight_submission.return_value = settings['enable_preflight_submission']
        journal.get_preflight_submission_id.return_value = PREFLIGHT_INVITATION_ID
        client = MagicMock()
        client.get_note.return_value = make_note()
        edit = MagicMock()
        edit.note.id = FORUM_ID
        ## the server injects `openreview` into process scripts; mirror that for the module import
        with patch.object(under_review_submission_process, 'openreview', openreview, create=True), \
                patch('openreview.journal.Journal', return_value=journal):
            under_review_submission_process.process(client, edit, MagicMock())
        return client

    def test_under_review_posts_preflight_edit_when_enabled(self):
        client = self.run_under_review(make_settings(enabled=True))

        client.post_note_edit.assert_called_once()
        kwargs = client.post_note_edit.call_args.kwargs
        assert kwargs['invitation'] == PREFLIGHT_INVITATION_ID
        assert kwargs['signatures'] == [VENUE_ID]
        assert kwargs['note'].id == FORUM_ID

    def test_under_review_does_not_post_preflight_edit_when_disabled(self):
        client = self.run_under_review(make_settings(enabled=False))

        client.post_note_edit.assert_not_called()

    def test_under_review_still_sends_action_editor_email(self):
        client = self.run_under_review(make_settings(enabled=True))

        client.post_message.assert_called_once()

    def test_preflight_invitation_has_process_and_one_reply_per_submission(self):
        builder = InvitationBuilder.__new__(InvitationBuilder)
        builder.journal = make_journal(make_settings(enabled=True))

        with patch.object(InvitationBuilder, 'save_invitation') as mock_save:
            builder.set_preflight_submission_invitation()

        invitation = mock_save.call_args.args[0]
        assert invitation.id == PREFLIGHT_INVITATION_ID
        assert invitation.maxReplies == 1
        assert 'def process(client, edit, invitation)' in invitation.process
        assert 'requests.post(' in invitation.process
