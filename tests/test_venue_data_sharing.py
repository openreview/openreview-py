import csv
import datetime
import io
import openreview
import pytest
from openreview.api import OpenReviewClient
from openreview.api import Note
from openreview.venue import Venue
from openreview.stages import SubmissionStage


class TestVenueDataSharing():

    venue_id = 'DataSharingA.cc/2026/Conference'
    alternate_venue_id = 'DataSharingB.cc/2026/Conference'
    support_group_id = 'openreview.net/Support'

    @pytest.fixture(scope="class")
    def data_sharing(self, openreview_client):
        return openreview.venue.VenueDataSharing(openreview_client, self.support_group_id)

    def create_venue(self, openreview_client, venue_id, short_name, program_chair_emails):

        venue = Venue(openreview_client, venue_id, self.support_group_id)
        venue.invitation_builder.update_wait_time = 2000
        venue.invitation_builder.update_date_string = "#{4/mdate} + 2000"
        venue.name = f'{short_name} Conference'
        venue.short_name = short_name
        venue.website = 'openreview.net'
        venue.contact = f'{short_name.replace(" ", "").lower()}@contact.com'
        venue.submission_stage = SubmissionStage(
            double_blind=True,
            due_date=datetime.datetime.now() + datetime.timedelta(days=1)
        )
        venue.setup(program_chair_ids=program_chair_emails)
        venue.create_submission_stage()
        return venue

    def post_submission(self, author_client, venue, title, abstract, helpers):

        edit = author_client.post_note_edit(
            invitation=venue.get_submission_id(),
            signatures=['~Celeste_Sharing1'],
            note=Note(
                content={
                    'title': { 'value': title },
                    'abstract': { 'value': abstract },
                    'authors': { 'value': ['Celeste Sharing'] },
                    'authorids': { 'value': ['~Celeste_Sharing1'] },
                    'pdf': { 'value': '/pdf/' + 'p' * 40 + '.pdf' },
                    'keywords': { 'value': ['dual submission'] }
                }
            ))
        helpers.await_queue_edit(author_client, edit_id=edit['id'])

    def test_setup(self, openreview_client, data_sharing, helpers):

        helpers.create_user('chris@datasharing.org', 'Chris', 'Sharing')
        openreview_client.post_group_edit(
            invitation='openreview.net/-/Edit',
            signatures=['openreview.net'],
            group=openreview.api.Group(
                id=self.support_group_id,
                members={
                    'append': ['~Chris_Sharing1']
                }
            )
        )

        helpers.create_user('pc@datasharinga.cc', 'ProgramChair', 'SharingA')
        helpers.create_user('pc2@datasharinga.cc', 'ProgramChair', 'SharingATwo')
        helpers.create_user('pc@datasharingb.cc', 'ProgramChair', 'SharingB')
        helpers.create_user('celeste@datasharing.org', 'Celeste', 'Sharing')

        venue = self.create_venue(openreview_client, self.venue_id, 'DSA 2026', ['pc@datasharinga.cc', 'pc2@datasharinga.cc'])
        alternate_venue = self.create_venue(openreview_client, self.alternate_venue_id, 'DSB 2026', ['pc@datasharingb.cc'])

        ## a venue without submission_venue_id in its domain, like a journal
        openreview_client.post_group_edit(
            invitation='openreview.net/-/Edit',
            signatures=['openreview.net'],
            group=openreview.api.Group(
                id='DataSharingJournal.cc',
                readers=['everyone'],
                writers=['DataSharingJournal.cc'],
                signatures=['~Super_User1'],
                signatories=['DataSharingJournal.cc'],
                members=[]
            )
        )
        openreview_client.add_members_to_group('venues', 'DataSharingJournal.cc')

        venues = openreview_client.get_group('venues').members
        assert self.venue_id in venues
        assert self.alternate_venue_id in venues

        author_client = OpenReviewClient(username='celeste@datasharing.org', password=helpers.strong_password)
        self.post_submission(author_client, venue, 'Dual Submission Paper', 'This paper was submitted to both venues.', helpers)
        self.post_submission(author_client, venue, 'Another Paper', 'This paper was only submitted to venue A.', helpers)
        self.post_submission(author_client, alternate_venue, 'Dual Submission Paper', 'This paper was submitted to both venues.', helpers)

        data_sharing.setup()

        group = openreview_client.get_group(data_sharing.group_id)
        assert group.web
        assert 'VenueHomepage' in group.web

        request_invitation = openreview_client.get_invitation(data_sharing.request_invitation_id)
        assert request_invitation.invitees == ['~']
        assert request_invitation.signatures == [self.support_group_id]
        run_invitation = openreview_client.get_invitation(data_sharing.run_invitation_id)
        assert run_invitation.signatures == ['~Super_User1']
        assert run_invitation.post_processes[0]['timeout'] == 86400000

    def test_request_validation(self, openreview_client, data_sharing, helpers):

        pc_client = OpenReviewClient(username='pc@datasharinga.cc', password=helpers.strong_password)
        author_client = OpenReviewClient(username='celeste@datasharing.org', password=helpers.strong_password)

        def post_request(client, venue_id, alternate_venue_id):
            return client.post_note_edit(
                invitation=data_sharing.request_invitation_id,
                signatures=[venue_id],
                note=Note(
                    content={
                        'venue_id': { 'value': venue_id },
                        'alternate_venue_id': { 'value': alternate_venue_id },
                        'top_percent_cutoff': { 'value': 1 },
                        'author_overlap_only': { 'value': False }
                    }
                ))

        ## the other venue must be a venue
        with pytest.raises(openreview.OpenReviewException, match=r'is not a venue'):
            post_request(pc_client, self.venue_id, f'{self.alternate_venue_id}/Authors')

        ## the requesting venue must be a venue
        with pytest.raises(openreview.OpenReviewException):
            post_request(pc_client, f'{self.venue_id}/Program_Chairs', self.alternate_venue_id)

        ## the venues must be different
        with pytest.raises(openreview.OpenReviewException, match=r'The other venue must be different from your venue'):
            post_request(pc_client, self.venue_id, self.venue_id)

        ## journals are not supported yet
        with pytest.raises(openreview.OpenReviewException, match=r'DataSharingJournal.cc is not supported yet'):
            post_request(pc_client, self.venue_id, 'DataSharingJournal.cc')

        ## only the program chairs can sign as the venue
        with pytest.raises(openreview.OpenReviewException):
            post_request(author_client, self.venue_id, self.alternate_venue_id)

        assert openreview_client.get_notes(invitation=data_sharing.request_invitation_id) == []

    def test_request(self, openreview_client, data_sharing, helpers):

        pc_client = OpenReviewClient(username='pc@datasharinga.cc', password=helpers.strong_password)

        edit = pc_client.post_note_edit(
            invitation=data_sharing.request_invitation_id,
            signatures=[self.venue_id],
            note=Note(
                content={
                    'venue_id': { 'value': self.venue_id },
                    'alternate_venue_id': { 'value': self.alternate_venue_id },
                    'top_percent_cutoff': { 'value': 5 },
                    'author_overlap_only': { 'value': False },
                    'submission_statuses': { 'value': ['Active', 'Withdrawn'] },
                    'results_recipients': { 'value': ['~ProgramChair_SharingA1'] },
                    'comment': { 'value': 'We would like to check for papers submitted to both venues.' }
                }
            ))
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        request = openreview_client.get_note(edit['note']['id'])
        assert request.number == 1
        assert request.signatures == [self.venue_id]
        assert request.readers == [self.support_group_id, self.venue_id, self.alternate_venue_id]
        assert request.content['title']['value'] == f'Dual Submission Check: {self.venue_id} and {self.alternate_venue_id}'
        assert request.content['status']['value'] == 'Pending Approval'

        approval_invitation = openreview_client.get_invitation(data_sharing.get_approval_invitation_id(1))
        assert approval_invitation.invitees == [self.alternate_venue_id]
        assert approval_invitation.edit['note']['forum'] == request.id

        comment_invitation = openreview_client.get_invitation(data_sharing.get_comment_invitation_id(1))
        assert comment_invitation.invitees == [self.support_group_id, self.venue_id, self.alternate_venue_id]

        results_invitation = openreview_client.get_invitation(data_sharing.get_results_invitation_id(1))
        assert results_invitation.invitees == [self.support_group_id]
        assert results_invitation.edit['note']['forum'] == request.id

        ## the program chairs of both venues can read the request
        alternate_pc_client = OpenReviewClient(username='pc@datasharingb.cc', password=helpers.strong_password)
        assert pc_client.get_note(request.id)
        assert alternate_pc_client.get_note(request.id)

        author_client = OpenReviewClient(username='celeste@datasharing.org', password=helpers.strong_password)
        with pytest.raises(openreview.OpenReviewException, match=r'does not have permission to see Note'):
            author_client.get_note(request.id)

        messages = openreview_client.get_messages(to='pc@datasharingb.cc', subject='DSA 2026 requests a dual submission check with DSB 2026')
        assert len(messages) == 1
        assert 'The program chairs of DSA 2026 (DataSharingA.cc/2026/Conference) request a dual submission check' in messages[0]['content']['text']
        assert 'the 5% most similar pairs of submissions' in messages[0]['content']['text']
        assert 'We would like to check for papers submitted to both venues.' in messages[0]['content']['text']
        ## the other venue sees what the requesting venue shares and who gets the results before approving
        assert 'Submissions of DSA 2026 to compare: Active, Withdrawn' in messages[0]['content']['text']
        assert 'Results recipients of DSA 2026: ~ProgramChair_SharingA1' in messages[0]['content']['text']
        assert f'forum?id={request.id}' in messages[0]['content']['text']

        messages = openreview_client.get_messages(to='pc@datasharinga.cc', subject='Your dual submission check request with DSB 2026 has been sent')
        assert len(messages) == 1

    def test_comments(self, openreview_client, data_sharing, helpers):

        pc_client = OpenReviewClient(username='pc@datasharinga.cc', password=helpers.strong_password)
        alternate_pc_client = OpenReviewClient(username='pc@datasharingb.cc', password=helpers.strong_password)
        request = openreview_client.get_notes(invitation=data_sharing.request_invitation_id, number=1)[0]
        subject = 'New comment on the dual submission check request: DSA 2026 and DSB 2026'

        edit = alternate_pc_client.post_note_edit(
            invitation=data_sharing.get_comment_invitation_id(1),
            signatures=[self.alternate_venue_id],
            note=Note(
                replyto=request.id,
                content={
                    'comment': { 'value': 'Do you want to include the withdrawn submissions?' }
                }
            ))
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        comment = openreview_client.get_note(edit['note']['id'])
        assert comment.readers == [self.support_group_id, self.venue_id, self.alternate_venue_id]

        messages = openreview_client.get_messages(to='pc@datasharinga.cc', subject=subject)
        assert len(messages) == 1
        assert 'A comment was posted by the program chairs of DSB 2026' in messages[0]['content']['text']
        assert 'Do you want to include the withdrawn submissions?' in messages[0]['content']['text']
        assert len(openreview_client.get_messages(to='chris@datasharing.org', subject=subject)) == 1
        assert len(openreview_client.get_messages(to='pc@datasharingb.cc', subject=subject)) == 0

        edit = pc_client.post_note_edit(
            invitation=data_sharing.get_comment_invitation_id(1),
            signatures=[self.venue_id],
            note=Note(
                replyto=comment.id,
                content={
                    'comment': { 'value': 'Only the active submissions, thanks.' }
                }
            ))
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        assert len(openreview_client.get_messages(to='pc@datasharinga.cc', subject=subject)) == 1
        assert len(openreview_client.get_messages(to='pc@datasharingb.cc', subject=subject)) == 1
        assert len(openreview_client.get_messages(to='chris@datasharing.org', subject=subject)) == 2

        ## the program chairs can only sign as their own venue
        with pytest.raises(openreview.OpenReviewException):
            pc_client.post_note_edit(
                invitation=data_sharing.get_comment_invitation_id(1),
                signatures=[self.alternate_venue_id],
                note=Note(
                    replyto=request.id,
                    content={
                        'comment': { 'value': 'Signed as the other venue.' }
                    }
                ))

    def test_approval(self, openreview_client, data_sharing, helpers):

        pc_client = OpenReviewClient(username='pc@datasharinga.cc', password=helpers.strong_password)
        alternate_pc_client = OpenReviewClient(username='pc@datasharingb.cc', password=helpers.strong_password)
        request = openreview_client.get_notes(invitation=data_sharing.request_invitation_id, number=1)[0]

        ## the requesting venue can not approve its own request
        with pytest.raises(openreview.OpenReviewException):
            pc_client.post_note_edit(
                invitation=data_sharing.get_approval_invitation_id(1),
                signatures=[self.venue_id],
                note=Note(
                    content={
                        'status': { 'value': 'Approved' }
                    }
                ))

        edit = alternate_pc_client.post_note_edit(
            invitation=data_sharing.get_approval_invitation_id(1),
            signatures=[self.alternate_venue_id],
            note=Note(
                content={
                    'status': { 'value': 'Rejected' },
                    'approval_comment': { 'value': 'We need to check with our committee first.' }
                }
            ))
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        approval = openreview_client.get_note(edit['note']['id'])
        assert approval.forum == request.id
        assert approval.replyto == request.id
        assert approval.signatures == [self.alternate_venue_id]

        request = openreview_client.get_note(request.id)
        assert request.content['status']['value'] == 'Rejected'

        messages = openreview_client.get_messages(to='pc@datasharinga.cc', subject='DSB 2026 rejected your dual submission check request')
        assert len(messages) == 1
        assert 'We need to check with our committee first.' in messages[0]['content']['text']
        assert 'If the program chairs of DSB 2026 suggested different settings, submit a new request with them.' in messages[0]['content']['text']

        ## only one approval per request
        with pytest.raises(openreview.OpenReviewException):
            alternate_pc_client.post_note_edit(
                invitation=data_sharing.get_approval_invitation_id(1),
                signatures=[self.alternate_venue_id],
                note=Note(
                    content={
                        'status': { 'value': 'Approved' }
                    }
                ))

        ## the approval can be changed before the check runs
        edit = alternate_pc_client.post_note_edit(
            invitation=data_sharing.get_approval_invitation_id(1),
            signatures=[self.alternate_venue_id],
            note=Note(
                id=approval.id,
                content={
                    'status': { 'value': 'Approved' },
                    'submission_statuses': { 'value': ['Active'] },
                    'approval_comment': { 'value': 'Our committee agreed.' }
                }
            ))
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        request = openreview_client.get_note(request.id)
        assert request.content['status']['value'] == 'Approved'

        messages = openreview_client.get_messages(to='pc@datasharinga.cc', subject='DSB 2026 approved your dual submission check request')
        assert len(messages) == 1
        assert 'Our committee agreed.' in messages[0]['content']['text']
        assert 'Submissions of DSB 2026 to compare: Active' in messages[0]['content']['text']
        assert 'Results recipients of DSB 2026: all the program chairs of DSB 2026' in messages[0]['content']['text']

        messages = openreview_client.get_messages(to='chris@datasharing.org', subject='Dual submission check ready to run: DSA 2026 and DSB 2026')
        assert len(messages) == 1

    def test_run(self, openreview_client, data_sharing, helpers):

        support_client = OpenReviewClient(username='chris@datasharing.org', password=helpers.strong_password)
        request = openreview_client.get_notes(invitation=data_sharing.request_invitation_id, number=1)[0]

        ## the program chairs can not run the check
        pc_client = OpenReviewClient(username='pc@datasharinga.cc', password=helpers.strong_password)
        with pytest.raises(openreview.OpenReviewException):
            pc_client.post_note_edit(
                invitation=data_sharing.run_invitation_id,
                signatures=[self.venue_id],
                note=Note(id=request.id)
            )

        ## use an existing job id: the scores are not computed in the test environment
        edit = support_client.post_note_edit(
            invitation=data_sharing.run_invitation_id,
            signatures=[self.support_group_id],
            note=Note(
                id=request.id,
                content={
                    'job_id': { 'value': 'test-job-id' }
                }
            ))
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        request = openreview_client.get_note(request.id)
        assert request.content['status']['value'] == 'Completed'
        assert 'results' not in request.content
        assert 'status_message' not in request.content

        results_notes = openreview_client.get_notes(invitation=data_sharing.get_results_invitation_id(1))
        assert len(results_notes) == 1
        results_note = results_notes[0]
        assert results_note.forum == request.id
        assert results_note.replyto == request.id
        assert results_note.signatures == [self.support_group_id]
        ## venue A chose one recipient, venue B shares the results with all its program chairs
        assert results_note.readers == [self.support_group_id, '~ProgramChair_SharingA1', self.alternate_venue_id]

        ## the approval can not change after the check runs
        approval_invitation = openreview_client.get_invitation(data_sharing.get_approval_invitation_id(1))
        assert approval_invitation.expdate < openreview.tools.datetime_millis(datetime.datetime.now())

        ## the results recipients of both venues can download the results
        alternate_pc_client = OpenReviewClient(username='pc@datasharingb.cc', password=helpers.strong_password)
        for client in [pc_client, alternate_pc_client]:
            results = client.get_attachment(id=results_note.id, field_name='results')
            rows = list(csv.reader(io.StringIO(results.decode('utf-8'))))
            assert rows[0][:3] == ['DSA 2026 id', 'DSB 2026 id', 'Score']
            assert len(rows) == 1

        ## the other program chair of venue A can read the request but not the results
        other_pc_client = OpenReviewClient(username='pc2@datasharinga.cc', password=helpers.strong_password)
        assert other_pc_client.get_note(request.id)
        with pytest.raises(openreview.OpenReviewException, match=r'does not have permission to see Note'):
            other_pc_client.get_note(results_note.id)
        with pytest.raises(openreview.OpenReviewException):
            other_pc_client.get_attachment(id=results_note.id, field_name='results')

        ## job_id and status_message are only visible to support
        assert 'job_id' not in pc_client.get_note(request.id).content

        messages = openreview_client.get_messages(to='pc@datasharinga.cc', subject='Dual submission check started: DSA 2026 and DSB 2026')
        assert len(messages) == 1
        messages = openreview_client.get_messages(to='pc@datasharingb.cc', subject='Dual submission check started: DSA 2026 and DSB 2026')
        assert len(messages) == 1

        for email in ['pc@datasharinga.cc', 'pc@datasharingb.cc', 'chris@datasharing.org']:
            messages = openreview_client.get_messages(to=email, subject='Dual submission check completed: DSA 2026 and DSB 2026')
            assert len(messages) == 1
            assert f'forum?id={request.id}&noteId={results_note.id}' in messages[0]['content']['text']
        assert openreview_client.get_messages(to='pc2@datasharinga.cc', subject='Dual submission check completed: DSA 2026 and DSB 2026') == []

    def test_run_failure(self, openreview_client, data_sharing, helpers):

        pc_client = OpenReviewClient(username='pc@datasharinga.cc', password=helpers.strong_password)
        support_client = OpenReviewClient(username='chris@datasharing.org', password=helpers.strong_password)

        edit = pc_client.post_note_edit(
            invitation=data_sharing.request_invitation_id,
            signatures=[self.venue_id],
            note=Note(
                content={
                    'venue_id': { 'value': self.venue_id },
                    'alternate_venue_id': { 'value': self.alternate_venue_id },
                    'top_percent_cutoff': { 'value': 1 },
                    'author_overlap_only': { 'value': True }
                }
            ))
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])
        request = openreview_client.get_note(edit['note']['id'])
        assert request.number == 2

        alternate_pc_client = OpenReviewClient(username='pc@datasharingb.cc', password=helpers.strong_password)
        edit = alternate_pc_client.post_note_edit(
            invitation=data_sharing.get_approval_invitation_id(2),
            signatures=[self.alternate_venue_id],
            note=Note(
                content={
                    'status': { 'value': 'Approved' }
                }
            ))
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        ## break the alternate venue so the check fails: its submission invitation can not be found
        openreview_client.post_group_edit(
            invitation=f'{self.alternate_venue_id}/-/Edit',
            signatures=[self.alternate_venue_id],
            group=openreview.api.Group(
                id=self.alternate_venue_id,
                content={
                    'submission_name': { 'value': 'Missing_Submission' }
                }
            )
        )

        edit = support_client.post_note_edit(
            invitation=data_sharing.run_invitation_id,
            signatures=[self.support_group_id],
            note=Note(
                id=request.id,
                content={
                    'job_id': { 'value': 'test-job-id' }
                }
            ))
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'], error=True)

        request = openreview_client.get_note(request.id)
        assert request.content['status']['value'] == 'Failed'
        assert 'Missing_Submission' in request.content['status_message']['value']
        assert request.content['status_message']['readers'] == [self.support_group_id]

        ## only support can see why the check failed
        assert 'status_message' not in pc_client.get_note(request.id).content

        assert openreview_client.get_notes(invitation=data_sharing.get_results_invitation_id(2)) == []

        messages = openreview_client.get_messages(to='chris@datasharing.org', subject='Dual submission check failed: DSA 2026 and DSB 2026')
        assert len(messages) == 1
        assert f'forum?id={request.id}' in messages[0]['content']['text']
        assert openreview_client.get_messages(to='pc@datasharinga.cc', subject='Dual submission check failed: DSA 2026 and DSB 2026') == []

        ## support fixes the problem and runs the check again
        openreview_client.post_group_edit(
            invitation=f'{self.alternate_venue_id}/-/Edit',
            signatures=[self.alternate_venue_id],
            group=openreview.api.Group(
                id=self.alternate_venue_id,
                content={
                    'submission_name': { 'value': 'Submission' }
                }
            )
        )

        edit = support_client.post_note_edit(
            invitation=data_sharing.run_invitation_id,
            signatures=[self.support_group_id],
            note=Note(
                id=request.id,
                content={
                    'job_id': { 'value': 'test-job-id' }
                }
            ))
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        ## the message of the failed run is removed
        request = openreview_client.get_note(request.id)
        assert request.content['status']['value'] == 'Completed'
        assert 'status_message' not in request.content

        results_notes = openreview_client.get_notes(invitation=data_sharing.get_results_invitation_id(2))
        assert len(results_notes) == 1

        messages = openreview_client.get_messages(to='chris@datasharing.org', subject='Dual submission check completed: DSA 2026 and DSB 2026')
        assert len(messages) == 2
        assert any(f'forum?id={request.id}&noteId={results_notes[0].id}' in m['content']['text'] for m in messages)

    def test_run_failure_on_venue_lookup(self, openreview_client, data_sharing, helpers):

        pc_client = OpenReviewClient(username='pc@datasharinga.cc', password=helpers.strong_password)
        support_client = OpenReviewClient(username='chris@datasharing.org', password=helpers.strong_password)

        edit = pc_client.post_note_edit(
            invitation=data_sharing.request_invitation_id,
            signatures=[self.venue_id],
            note=Note(
                content={
                    'venue_id': { 'value': self.venue_id },
                    'alternate_venue_id': { 'value': self.alternate_venue_id },
                    'top_percent_cutoff': { 'value': 1 },
                    'author_overlap_only': { 'value': False }
                }
            ))
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])
        request = openreview_client.get_note(edit['note']['id'])
        assert request.number == 3

        ## point the request to a venue that does not exist so the venue lookup fails
        openreview_client.post_note_edit(
            invitation=f'{self.support_group_id}/-/Edit',
            readers=[self.support_group_id],
            writers=[self.support_group_id],
            signatures=[self.support_group_id],
            note=Note(
                id=request.id,
                content={
                    'alternate_venue_id': { 'value': 'Missing.cc/2026/Conference' }
                }
            ))

        edit = support_client.post_note_edit(
            invitation=data_sharing.run_invitation_id,
            signatures=[self.support_group_id],
            note=Note(
                id=request.id,
                content={
                    'job_id': { 'value': 'test-job-id' }
                }
            ))
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'], error=True)

        request = openreview_client.get_note(request.id)
        assert request.content['status']['value'] == 'Failed'
        assert 'Missing.cc/2026/Conference' in request.content['status_message']['value']

        ## nothing was shared, so the approval is still open
        approval_invitation = openreview_client.get_invitation(data_sharing.get_approval_invitation_id(3))
        assert approval_invitation.expdate is None

        ## the venue id is used when the venue can not be found
        messages = openreview_client.get_messages(to='chris@datasharing.org', subject='Dual submission check failed: DSA 2026 and Missing.cc/2026/Conference')
        assert len(messages) == 1
        assert f'forum?id={request.id}' in messages[0]['content']['text']

    def test_run_checks(self, openreview_client, data_sharing, helpers):

        pc_client = OpenReviewClient(username='pc@datasharinga.cc', password=helpers.strong_password)
        alternate_pc_client = OpenReviewClient(username='pc@datasharingb.cc', password=helpers.strong_password)
        support_client = OpenReviewClient(username='chris@datasharing.org', password=helpers.strong_password)

        edit = pc_client.post_note_edit(
            invitation=data_sharing.request_invitation_id,
            signatures=[self.venue_id],
            note=Note(
                content={
                    'venue_id': { 'value': self.venue_id },
                    'alternate_venue_id': { 'value': self.alternate_venue_id },
                    'top_percent_cutoff': { 'value': 1 },
                    'author_overlap_only': { 'value': False }
                }
            ))
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])
        request = openreview_client.get_note(edit['note']['id'])
        assert request.number == 4

        def run(error=False):
            edit = support_client.post_note_edit(
                invitation=data_sharing.run_invitation_id,
                signatures=[self.support_group_id],
                note=Note(
                    id=request.id,
                    content={
                        'job_id': { 'value': 'test-job-id' }
                    }
                ))
            helpers.await_queue_edit(openreview_client, edit_id=edit['id'], error=error)
            return openreview_client.get_note(request.id)

        ## the check does not run before the other venue approves it
        request = run(error=True)
        assert request.content['status']['value'] == 'Failed'
        assert 'DSB 2026 has not approved the request.' in request.content['status_message']['value']
        assert openreview_client.get_invitation(data_sharing.get_approval_invitation_id(4)).expdate is None

        edit = alternate_pc_client.post_note_edit(
            invitation=data_sharing.get_approval_invitation_id(4),
            signatures=[self.alternate_venue_id],
            note=Note(
                content={
                    'status': { 'value': 'Approved' }
                }
            ))
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        ## once approved, the check runs
        request = run()
        assert request.content['status']['value'] == 'Completed'
        assert 'status_message' not in request.content
        assert len(openreview_client.get_notes(invitation=data_sharing.get_results_invitation_id(4))) == 1
