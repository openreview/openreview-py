from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
import requests

import openreview
from openreview.journal.invitation import InvitationBuilder
from openreview.journal.process import under_review_submission_process

VENUE_ID = 'SLADS'
PREFLIGHT_URL = 'https://preflight-dev.example.invalid/api/submissions'
PREFLIGHT_TOKEN = 'dummy-preflight-token'
FORUM_ID = 'forum_abc123'


def make_journal(enabled=True, url=PREFLIGHT_URL, token=PREFLIGHT_TOKEN):
    journal = MagicMock()
    journal.venue_id = VENUE_ID
    journal.under_review_venue_id = f'{VENUE_ID}/Under_Review'
    journal.should_enable_preflight_submission.return_value = enabled
    journal.get_preflight_url.return_value = url
    journal.get_preflight_token.return_value = token
    return journal


def make_note(venueid='SLADS/Under_Review', mdate=1234567890, forum=FORUM_ID):
    note = MagicMock()
    note.id = FORUM_ID
    note.forum = forum
    note.number = 1
    note.mdate = mdate
    note.content = {
        'title': {'value': 'Paper title'},
        'venueid': {'value': venueid},
    }
    return note


def make_invitation(url=PREFLIGHT_URL, token=PREFLIGHT_TOKEN):
    invitation = MagicMock()
    invitation.content = {
        'preflight_url': {'value': url},
        'preflight_token': {'value': token},
    }
    return invitation


@pytest.fixture(autouse=True)
def inject_openreview_module():
    with patch.object(under_review_submission_process, 'openreview', openreview, create=True):
        yield


class TestPreflightRequest:

    @patch('requests.post')
    def test_posts_forum_id_with_bearer_token_and_idempotency_key(self, mock_post):
        response = mock_post.return_value
        response.status_code = 200
        response.json.side_effect = AssertionError('accepted response must not be parsed')
        journal = make_journal()
        note = make_note(forum='forum_root456')

        under_review_submission_process._submit_preflight_request(
            make_invitation(), journal, note
        )

        mock_post.assert_called_once_with(
            PREFLIGHT_URL,
            json={'forum_id': 'forum_root456'},
            headers={
                'Authorization': f'Bearer {PREFLIGHT_TOKEN}',
                'Idempotency-Key': f'openreview-preflight:forum_root456:{note.mdate}',
            },
            timeout=30,
        )
        response.json.assert_not_called()

    @patch('requests.post')
    def test_same_revision_reuses_idempotency_key_and_revision_change_gets_new_key(self, mock_post):
        mock_post.return_value.status_code = 200
        journal = make_journal()

        under_review_submission_process._submit_preflight_request(
            make_invitation(), journal, make_note()
        )
        under_review_submission_process._submit_preflight_request(
            make_invitation(), journal, make_note()
        )
        under_review_submission_process._submit_preflight_request(
            make_invitation(), journal, make_note(mdate=1234567891)
        )

        keys = [call.kwargs['headers']['Idempotency-Key'] for call in mock_post.call_args_list]
        assert keys[0] == keys[1]
        assert keys[2] != keys[0]

    @pytest.mark.parametrize('token', [None, ''])
    @patch('requests.post')
    def test_missing_token_fails_without_sending_request(self, mock_post, token):
        with pytest.raises(openreview.OpenReviewException) as exc_info:
            under_review_submission_process._submit_preflight_request(
                make_invitation(token=token), make_journal(), make_note()
            )

        assert exc_info.value.args[0]['name'] == 'PreflightConfigurationError'
        assert 'preflight_token' in exc_info.value.args[0]['message']
        mock_post.assert_not_called()

    @patch('requests.post')
    def test_missing_url_fails_without_sending_request(self, mock_post):
        with pytest.raises(openreview.OpenReviewException) as exc_info:
            under_review_submission_process._submit_preflight_request(
                make_invitation(url=None), make_journal(), make_note()
            )

        assert exc_info.value.args[0]['name'] == 'PreflightConfigurationError'
        mock_post.assert_not_called()

    @patch('requests.post')
    def test_non_200_response_raises_openreview_exception_without_echoing_body(self, mock_post):
        mock_post.return_value.status_code = 503
        mock_post.return_value.text = PREFLIGHT_TOKEN

        with pytest.raises(openreview.OpenReviewException) as exc_info:
            under_review_submission_process._submit_preflight_request(
                make_invitation(), make_journal(), make_note()
            )

        assert exc_info.value.args[0] == {
            'name': 'PreflightServiceError',
            'message': 'Preflight request failed with HTTP status 503',
            'status': 503,
        }
        assert PREFLIGHT_TOKEN not in str(exc_info.value)
        mock_post.return_value.json.assert_not_called()

    @patch('requests.post')
    def test_connection_error_raises_openreview_exception(self, mock_post):
        mock_post.side_effect = requests.ConnectionError('connection refused')

        with pytest.raises(openreview.OpenReviewException) as exc_info:
            under_review_submission_process._submit_preflight_request(
                make_invitation(), make_journal(), make_note()
            )

        assert exc_info.value.args[0]['name'] == 'PreflightConnectionError'
        assert PREFLIGHT_TOKEN not in str(exc_info.value)

    @patch('requests.post')
    def test_timeout_raises_openreview_exception_without_exposing_token(self, mock_post):
        mock_post.side_effect = requests.Timeout('timed out')

        with pytest.raises(openreview.OpenReviewException) as exc_info:
            under_review_submission_process._submit_preflight_request(
                make_invitation(), make_journal(), make_note()
            )

        assert exc_info.value.args[0]['name'] == 'PreflightTimeoutError'
        assert PREFLIGHT_TOKEN not in str(exc_info.value)

    @pytest.mark.parametrize('venueid', [
        'SLADS/Submitted',
        'SLADS/Desk_Rejected',
        'SLADS/Withdrawn_Submission',
        'SLADS/Rejected',
    ])
    @patch('requests.post')
    def test_non_under_review_stages_do_not_send_request(self, mock_post, venueid):
        under_review_submission_process._submit_preflight_request(
            make_invitation(), make_journal(), make_note(venueid=venueid)
        )

        mock_post.assert_not_called()


class TestUnderReviewProcess:

    def test_under_review_invitation_stores_preflight_configuration_in_private_content(self):
        journal = MagicMock()
        journal.venue_id = VENUE_ID
        journal.get_under_review_id.return_value = f'{VENUE_ID}/-/Under_Review'
        journal.should_enable_preflight_submission.return_value = True
        journal.get_preflight_url.return_value = PREFLIGHT_URL
        journal.get_preflight_token.return_value = PREFLIGHT_TOKEN
        journal.get_under_review_submission_readers.return_value = [VENUE_ID]
        journal.get_author_submission_id.return_value = f'{VENUE_ID}/-/Submission'
        journal.under_review_venue_id = f'{VENUE_ID}/Under_Review'
        journal.short_name = VENUE_ID
        journal.is_action_editor_anonymous.return_value = True
        builder = InvitationBuilder.__new__(InvitationBuilder)
        builder.journal = journal
        builder.save_invitation = MagicMock()

        builder.set_under_review_invitation()

        invitation = builder.save_invitation.call_args.args[0]
        assert invitation.content == {
            'preflight_url': {'value': PREFLIGHT_URL},
            'preflight_token': {'value': PREFLIGHT_TOKEN},
        }
        assert invitation.readers == [VENUE_ID]

    @pytest.mark.parametrize('enabled', [True, False])
    def test_under_review_process_submits_only_when_preflight_is_enabled(self, enabled):
        journal = make_journal(enabled=enabled)
        journal.get_due_date.return_value = datetime(2026, 1, 1)
        journal.get_action_editors_id.return_value = f'{VENUE_ID}/Action_Editors'
        journal.get_number_of_reviewers.return_value = 2
        journal.get_reviewers_max_papers.return_value = 5
        journal.get_reviewer_assignment_period_length.return_value = 2
        journal.get_meta_invitation_id.return_value = f'{VENUE_ID}/-/Edit'
        journal.get_message_sender.return_value = {}
        journal.contact_info = 'contact@example.com'
        journal.short_name = VENUE_ID
        journal.website = 'sladsfour.com'
        journal.invitation_builder = MagicMock()
        journal.client = MagicMock()

        note = make_note()
        client = MagicMock()
        client.get_note.return_value = note
        client.get_group.return_value.content = {
            'reviewer_assignment_starts_email_template_script': {'value': '{short_name}'}
        }
        edit = MagicMock()
        edit.note.id = FORUM_ID
        invitation = make_invitation()

        with patch('openreview.journal.Journal', return_value=journal), \
                patch.object(
                    under_review_submission_process, '_submit_preflight_request'
                ) as submit:
            under_review_submission_process.process(client, edit, invitation)

        if enabled:
            submit.assert_called_once_with(invitation, journal, note)
        else:
            submit.assert_not_called()
        client.post_note_edit.assert_not_called()
        client.post_message.assert_called_once()
