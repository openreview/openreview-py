import openreview
import pytest
import time
import datetime
from openreview.api import OpenReviewClient
from openreview.api import Note
from openreview.api import Invitation

from openreview.venue import Venue
from openreview.stages import SubmissionStage

class TestVenueSubmissionUnifiedAuthors():

    @pytest.fixture(scope="class")
    def venue(self, openreview_client):
        venue = Venue(openreview_client, 'UnifiedAuthorsVenue.cc', 'openreview.net/Support')
        venue.name = 'Unified Authors Venue 2026'
        venue.short_name = 'UAV 26'
        venue.website = 'uav.org'
        venue.contact = 'uav@contact.com'

        now = datetime.datetime.now()
        venue.submission_stage = SubmissionStage(
            double_blind=True,
            due_date=now + datetime.timedelta(minutes = 30),
            readers=[SubmissionStage.Readers.EVERYONE],
            force_profiles=True,
            unified_authors=True,
            email_pcs=True
        )

        return venue

    def test_setup(self, venue, openreview_client, helpers):

        helpers.create_user('uav_pc@mail.com', 'PC UAV', 'One')
        venue.setup(program_chair_ids=['uav_pc@mail.com'])
        venue.create_submission_stage()

        submission_invitation = openreview_client.get_invitation('UnifiedAuthorsVenue.cc/-/Submission')
        assert submission_invitation.edit['note']['content']['authors']['value']['param']['type'] == 'author{}'
        assert 'authorids' not in submission_invitation.edit['note']['content']

        helpers.create_user('ana@unified.com', 'Ana', 'UnifiedOne')
        helpers.create_user('bea@unified.com', 'Bea', 'UnifiedTwo')

    def test_delete_submission_edits(self, venue, openreview_client, helpers):
        '''Deleting every edit of a submission leaves a note with ddate and no content. The submission
        process must notify the authors, taken from the deleted edit, and keep the authors group.'''

        author_client = OpenReviewClient(username='ana@unified.com', password=helpers.strong_password)
        submission_edit = author_client.post_note_edit(
            invitation='UnifiedAuthorsVenue.cc/-/Submission',
            signatures=['~Ana_UnifiedOne1'],
            note=Note(
                content={
                    'title': { 'value': 'Paper To Be Deleted' },
                    'abstract': { 'value': 'This is an abstract' },
                    'authors': {
                        'value': [
                            {
                                'fullname': 'Ana UnifiedOne',
                                'username': '~Ana_UnifiedOne1',
                                'institutions': [{ 'domain': 'unified.com', 'country': 'US' }]
                            },
                            {
                                'fullname': 'Bea UnifiedTwo',
                                'username': '~Bea_UnifiedTwo1',
                                'institutions': [{ 'domain': 'unified.com', 'country': 'US' }]
                            }
                        ]
                    },
                    'keywords': { 'value': ['aa'] },
                    'pdf': { 'value': '/pdf/' + 'p' * 40 +'.pdf' }
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=submission_edit['id'])

        note_id = submission_edit['note']['id']
        note = openreview_client.get_note(note_id)
        assert note.authorids == ['~Ana_UnifiedOne1', '~Bea_UnifiedTwo1']

        authors_group = openreview_client.get_group(f'UnifiedAuthorsVenue.cc/Submission{note.number}/Authors')
        assert set(authors_group.members) == {'~Ana_UnifiedOne1', '~Bea_UnifiedTwo1'}
        assert authors_group.id in openreview_client.get_group('UnifiedAuthorsVenue.cc/Authors').members

        messages = openreview_client.get_messages(subject='UAV 26 has received your submission titled Paper To Be Deleted')
        assert len(messages) == 2
        messages = openreview_client.get_messages(to='uav_pc@mail.com', subject='UAV 26 has received a new submission titled Paper To Be Deleted')
        assert len(messages) == 1

        # delete every edit of the note, the Submission edit last and by the author
        edits = openreview_client.get_note_edits(note_id=note_id)
        assert len(edits) >= 1
        now = openreview.tools.datetime_millis(datetime.datetime.now())
        for edit in [e for e in edits if e.invitation != 'UnifiedAuthorsVenue.cc/-/Submission']:
            edit.invitation = 'UnifiedAuthorsVenue.cc/-/Edit'
            edit.ddate = now
            deleted_edit = openreview_client.post_edit(edit)
            assert deleted_edit['id'] == edit.id

        submission_edits = [e for e in edits if e.invitation == 'UnifiedAuthorsVenue.cc/-/Submission']
        assert len(submission_edits) == 1
        submission_edits[0].ddate = now
        deleted_edit = author_client.post_edit(submission_edits[0])
        assert deleted_edit['id'] == submission_edits[0].id

        # the note is now deleted and has no content
        deleted_note = openreview_client.get_note(note_id)
        assert deleted_note.ddate
        assert deleted_note.content is None
        assert deleted_note.authorids == []

        # process_update runs a second time for the submission edit id, this time for the deletion
        process_logs = []
        for _ in range(120):
            process_logs = openreview_client.get_process_logs(id=submission_edits[0].id)
            if len(process_logs) == 2 and all(log['status'] in ['ok', 'error'] for log in process_logs):
                break
            time.sleep(0.5)
        assert len(process_logs) == 2
        errors = [log['error'] for log in process_logs if log['status'] == 'error']
        assert not errors, errors

        # the authors group keeps the authors of the deleted edit and is removed from the venue authors group
        authors_group = openreview_client.get_group(f'UnifiedAuthorsVenue.cc/Submission{deleted_note.number}/Authors')
        assert set(authors_group.members) == {'~Ana_UnifiedOne1', '~Bea_UnifiedTwo1'}
        assert authors_group.id not in openreview_client.get_group('UnifiedAuthorsVenue.cc/Authors').members

        # the author who deleted the submission and the co-author are notified, the title comes from the deleted edit
        deleted_message = f'''Your submission to UAV 26 has been deleted.

Submission Number: {deleted_note.number}

Title: Paper To Be Deleted 

To view your submission, click here: https://openreview.net/forum?id={note_id}'''

        messages = openreview_client.get_messages(to='ana@unified.com', subject='UAV 26 has received your submission titled Paper To Be Deleted')
        assert len(messages) == 2
        deleted_messages = [m for m in messages if 'has been deleted' in m['content']['text']]
        assert len(deleted_messages) == 1
        assert deleted_message in deleted_messages[0]['content']['text']
        assert 'If you are not an author of this submission' not in deleted_messages[0]['content']['text']

        messages = openreview_client.get_messages(to='bea@unified.com', subject='UAV 26 has received your submission titled Paper To Be Deleted')
        assert len(messages) == 2
        deleted_messages = [m for m in messages if 'has been deleted' in m['content']['text']]
        assert len(deleted_messages) == 1
        assert deleted_message in deleted_messages[0]['content']['text']
        assert 'If you are not an author of this submission and would like to be removed, please contact the author who added you at ana@unified.com' in deleted_messages[0]['content']['text']

        # the program chairs are notified too
        messages = openreview_client.get_messages(to='uav_pc@mail.com', subject='UAV 26 has received a new submission titled Paper To Be Deleted')
        assert len(messages) == 2
        deleted_messages = [m for m in messages if 'A submission to UAV 26 has been deleted.' in m['content']['text']]
        assert len(deleted_messages) == 1

    def test_submission_with_renamed_title_field(self, venue, openreview_client, helpers):
        '''PCs can rename the title field of the submission form. The submission process
        must not assume note.content['title'] exists.'''

        openreview_client.post_invitation_edit(
            invitations='UnifiedAuthorsVenue.cc/-/Edit',
            readers=['UnifiedAuthorsVenue.cc'],
            writers=['UnifiedAuthorsVenue.cc'],
            signatures=['UnifiedAuthorsVenue.cc'],
            invitation=Invitation(
                id='UnifiedAuthorsVenue.cc/-/Submission',
                edit={
                    'note': {
                        'content': {
                            'title': { 'delete': True },
                            'paper_title': {
                                'order': 1,
                                'description': 'Title of paper.',
                                'value': {
                                    'param': {
                                        'type': 'string',
                                        'regex': '^.{1,250}$'
                                    }
                                }
                            }
                        }
                    }
                }
            )
        )

        invitation = openreview_client.get_invitation('UnifiedAuthorsVenue.cc/-/Submission')
        assert 'title' not in invitation.edit['note']['content']
        assert 'paper_title' in invitation.edit['note']['content']

        author_client = OpenReviewClient(username='ana@unified.com', password=helpers.strong_password)
        submission_edit = author_client.post_note_edit(
            invitation='UnifiedAuthorsVenue.cc/-/Submission',
            signatures=['~Ana_UnifiedOne1'],
            note=Note(
                content={
                    'paper_title': { 'value': 'Paper With Renamed Title' },
                    'abstract': { 'value': 'This is an abstract' },
                    'authors': {
                        'value': [
                            {
                                'fullname': 'Ana UnifiedOne',
                                'username': '~Ana_UnifiedOne1',
                                'institutions': [{ 'domain': 'unified.com', 'country': 'US' }]
                            },
                            {
                                'fullname': 'Bea UnifiedTwo',
                                'username': '~Bea_UnifiedTwo1',
                                'institutions': [{ 'domain': 'unified.com', 'country': 'US' }]
                            }
                        ]
                    },
                    'keywords': { 'value': ['aa'] },
                    'pdf': { 'value': '/pdf/' + 'p' * 40 +'.pdf' }
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=submission_edit['id'])

        note = openreview_client.get_note(submission_edit['note']['id'])
        assert note.content['paper_title']['value'] == 'Paper With Renamed Title'
        assert 'title' not in note.content

        posted_message = f'''Your submission to UAV 26 has been posted.

Submission Number: {note.number}

Title:  

Abstract: This is an abstract

To view your submission, click here: https://openreview.net/forum?id={note.id}'''

        # the notifications are sent without a title
        for email in ['ana@unified.com', 'bea@unified.com']:
            messages = openreview_client.get_messages(to=email, subject='UAV 26 has received your submission')
            messages = [m for m in messages if f'Submission Number: {note.number}' in m['content']['text']]
            assert len(messages) == 1
            assert messages[0]['content']['subject'] == 'UAV 26 has received your submission'
            assert posted_message in messages[0]['content']['text']

        messages = openreview_client.get_messages(to='uav_pc@mail.com', subject='UAV 26 has received a new submission')
        messages = [m for m in messages if f'Submission Number: {note.number}' in m['content']['text']]
        assert len(messages) == 1
        assert messages[0]['content']['subject'] == 'UAV 26 has received a new submission'
        assert 'A submission to UAV 26 has been posted.' in messages[0]['content']['text']

        authors_group = openreview_client.get_group(f'UnifiedAuthorsVenue.cc/Submission{note.number}/Authors')
        assert set(authors_group.members) == {'~Ana_UnifiedOne1', '~Bea_UnifiedTwo1'}
        assert authors_group.id in openreview_client.get_group('UnifiedAuthorsVenue.cc/Authors').members
