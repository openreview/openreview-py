import csv
import openreview
import pytest
import time
import json
import datetime
import random
import os
import re
from openreview.api import OpenReviewClient
from openreview.api import Note
from openreview.api import Group
from openreview.api import Invitation
from openreview.api import Edge

from openreview.venue import Venue
from openreview.stages import SubmissionStage, BidStage

class TestVenueSubmissionARR():

    @pytest.fixture(scope="class")
    def venue(self, openreview_client):
        conference_id = 'ARR'

        venue = Venue(openreview_client, conference_id, 'openreview.net/Support')

        # Set journal names
        venue.program_chairs_name = 'Editors_In_Chief'
        venue.area_chair_roles = ['Action_Editors']
        venue.senior_area_chair_roles = ['Senior_Action_Editors']
        venue.area_chairs_name = 'Action_Editors'
        venue.senior_area_chairs_name = 'Senior_Action_Editors'

        venue.use_area_chairs = True
        venue.name = 'ARR'
        venue.short_name = 'ARR'
        venue.website = 'aclrollingreview.org'
        venue.contact = 'support@aclrollingreview.org'
        venue.reviewer_identity_readers = [openreview.stages.IdentityReaders.PROGRAM_CHAIRS, openreview.stages.IdentityReaders.AREA_CHAIRS_ASSIGNED]

        now = datetime.datetime.utcnow()
        venue.submission_stage = SubmissionStage(
            double_blind=True,
            due_date=now + datetime.timedelta(minutes = 30),
            withdrawn_submission_reveal_authors=True,
            force_profiles=True
        )
    
        venue.review_stage = openreview.stages.ReviewStage(start_date=now + datetime.timedelta(minutes = 4), due_date=now + datetime.timedelta(minutes = 40))
        venue.meta_review_stage = openreview.stages.MetaReviewStage(start_date=now + datetime.timedelta(minutes = 10), due_date=now + datetime.timedelta(minutes = 40))

        venue.review_rebuttal_stage = openreview.ReviewRebuttalStage(
            start_date=now + datetime.timedelta(minutes = 10),
            due_date=now + datetime.timedelta(minutes = 35),
            single_rebuttal = True,
            readers = [openreview.stages.ReviewRebuttalStage.Readers.AREA_CHAIRS_ASSIGNED, openreview.stages.ReviewRebuttalStage.Readers.REVIEWERS_ASSIGNED],
            additional_fields={
                "pdf": {
                    "value": {
                    "param": {
                        "type": "file",
                        "extensions": [ "pdf" ],
                        "maxSize": 50,
                        "optional": True
                    }
                    },
                    "description": "Upload a PDF file that ends with .pdf",
                    "order": 9
                }
            }
        )
        return venue

    def test_setup(self, venue, openreview_client, helpers):
        cycle = '2023_March'
        cycleid = f"{cycle}/Submission"

        venue.setup(program_chair_ids=['editors@aclrollingreview.org'], partial_submission_venue_id=cycleid)
        venue.create_submission_stage(sub_venue_id=cycle)
        venue.create_review_stage(sub_venue_id=cycle)
        venue.create_meta_review_stage(sub_venue_id=cycle)
        venue.create_review_rebuttal_stage(sub_venue_id=cycle)
        assert openreview_client.get_group('ARR')
        assert openreview_client.get_group('ARR/Authors')

        helpers.create_user('editors@aclrollingreview.org', 'ARR EiC', 'One')

    def test_recruitment_stage(self, venue, openreview_client, selenium, request_page, helpers):

        #recruit reviewers and area chairs to create groups
        message = 'Dear {{fullname}},\n\nYou have been nominated by the program chair committee of ARR to serve as {{invitee_role}}.\n\nTo respond to the invitation, please click on the following link:\n\n{{invitation_url}}\n\nCheers!\n\nProgram Chairs'
        
        helpers.create_user('arr_reviewer_venue_one@mail.com', 'ARR Reviewer Venue', 'One')
        
        venue.recruit_reviewers(title='[ARR] Invitation to serve as Reviewer',
            message=message,
            invitees = ['~ARR_Reviewer_Venue_One1'],
            contact_info='editors@aclrollingreview.org',
            reduced_load_on_decline = ['1','2','3'])

        venue.recruit_reviewers(title='[ARR] Invitation to serve as Action Editor',
            message=message,
            invitees = ['~ARR_Reviewer_Venue_One1'],
            reviewers_name = 'Action_Editors',
            contact_info='editors@aclrollingreview.org',
            allow_overlap_official_committee = True)

        messages = openreview_client.get_messages(to='arr_reviewer_venue_one@mail.com')
        assert messages
        invitation_url = re.search('https://.*\n', messages[1]['content']['text']).group(0).replace('https://openreview.net', 'http://localhost:3030')[:-1]
        helpers.respond_invitation(selenium, request_page, invitation_url, accept=True, quota=1)

        reviewer_group = openreview_client.get_group('ARR/Reviewers')
        assert reviewer_group
        assert '~ARR_Reviewer_Venue_One1' in reviewer_group.members    
    
    def test_submission_stage(self, venue, openreview_client, helpers):

        assert openreview_client.get_invitation('ARR/-/Submission')

        helpers.create_user('harold@maileleven.com', 'Harold', 'Eleven')
        author_client = OpenReviewClient(username='harold@maileleven.com', password='1234')

        submission_note_1 = author_client.post_note_edit(
            invitation='ARR/-/Submission',
            signatures= ['~Harold_Eleven1'],
            note=Note(
                content={
                    'title': { 'value': 'Paper 1 Title' },
                    'abstract': { 'value': 'Paper abstract' },
                    'authors': { 'value': ['Harold Eleven']},
                    'authorids': { 'value': ['~Harold_Eleven1']},
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                    'keywords': {'value': ['aa'] }
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=submission_note_1['id']) 

        submission = openreview_client.get_note(submission_note_1['note']['id'])
        assert len(submission.readers) == 2
        assert 'ARR' in submission.readers
        assert ['ARR', '~Harold_Eleven1'] == submission.readers

        #TODO: check emails, check author console

        submission_note_2 = author_client.post_note_edit(
            invitation='ARR/-/Submission',
            signatures= ['~Harold_Eleven1'],
            note=Note(
                content={
                    'title': { 'value': 'Paper 2 Title' },
                    'abstract': { 'value': 'Paper abstract' },
                    'authors': { 'value': ['Harold Eleven']},
                    'authorids': { 'value': ['~Harold_Eleven1']},
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                    'keywords': {'value': ['aa'] }
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=submission_note_2['id']) 

    def test_post_submission_stage(self, venue, openreview_client, helpers):
        cycle = '2023_March'
    
        venue.submission_stage.readers = [SubmissionStage.Readers.REVIEWERS, SubmissionStage.Readers.AREA_CHAIRS]
        venue.submission_stage.exp_date = datetime.datetime.utcnow() + datetime.timedelta(seconds = 60)
        venue.create_submission_stage(sub_venue_id=cycle)

        helpers.await_queue_edit(openreview_client, 'ARR/-/Post_Submission-0-0')
        helpers.await_queue_edit(openreview_client, 'ARR/Reviewers/-/Submission_Group-0-0')
        helpers.await_queue_edit(openreview_client, 'ARR/Action_Editors/-/Submission_Group-0-0')

        #print(openreview_client.get_all_groups(prefix='ARR/Submission1/.*'))
        assert openreview_client.get_group('ARR/Submission1/Authors')
        assert openreview_client.get_group('ARR/Submission1/Reviewers')
        assert openreview_client.get_group('ARR/Submission1/Action_Editors')

        submissions = venue.get_submissions(sort='number:asc', submission_venue_id=venue.get_submission_venue_id(f'{cycle}/Submission'))
        assert len(submissions) == 2
        submission = submissions[0]
        assert len(submission.readers) == 4
        assert 'ARR' in submission.readers
        assert 'ARR/Submission1/Authors' in submission.readers        
        assert 'ARR/Reviewers' in submission.readers
        assert 'ARR/Action_Editors' in submission.readers

        assert openreview_client.get_invitation('ARR/Submission1/-/Withdrawal')
        assert openreview_client.get_invitation('ARR/Submission2/-/Withdrawal')

        assert openreview_client.get_invitation('ARR/Submission1/-/Desk_Rejection')
        assert openreview_client.get_invitation('ARR/Submission2/-/Desk_Rejection')

    def test_review_stage(self, venue, openreview_client, helpers):
        cycle = '2023_March'

        assert openreview_client.get_invitation(f'ARR/-/{cycle}/Official_Review')
        with pytest.raises(openreview.OpenReviewException, match=rf'The Invitation ARR/Submission1/-/{cycle}/Official_Review was not found'):
            assert openreview_client.get_invitation(f'ARR/Submission1/-/{cycle}/Official_Review')

        openreview_client.post_invitation_edit(
            invitations='ARR/-/Official_Review',
            readers=['ARR'],
            writers=['ARR'],
            signatures=['ARR'],
            content={
                'subvenueid': {
                    'value': cycle
                }
            },
            invitation=openreview.api.Invitation(id=f'ARR/-/{cycle}/Official_Review',
                cdate=openreview.tools.datetime_millis(datetime.datetime.utcnow()) + 2000,
                signatures=['ARR']
            )
        )

        helpers.await_queue_edit(openreview_client, f'ARR/-/{cycle}/Official_Review-0-0')
        helpers.await_queue_edit(openreview_client, f'ARR/-/{cycle}/Official_Review-0-1', count=2)

        assert openreview_client.get_invitation(f'ARR/-/{cycle}/Official_Review')
        assert openreview_client.get_invitation(f'ARR/Submission1/-/{cycle}/Official_Review')

    def test_meta_review_stage(self, venue, openreview_client, helpers):
        cycle = '2023_March'

        assert openreview_client.get_invitation(f'ARR/-/{cycle}/Meta_Review')
        with pytest.raises(openreview.OpenReviewException, match=rf'The Invitation ARR/Submission1/-/{cycle}/Meta_Review was not found'):
            assert openreview_client.get_invitation(f'ARR/Submission1/-/{cycle}/Meta_Review')

        openreview_client.post_invitation_edit(
            invitations='ARR/-/Meta_Review',
            readers=['ARR'],
            writers=['ARR'],
            signatures=['ARR'],
            content={
                'subvenueid': {
                    'value': cycle
                }
            },
            invitation=openreview.api.Invitation(id=f'ARR/-/{cycle}/Meta_Review',
                cdate=openreview.tools.datetime_millis(datetime.datetime.utcnow()) + 2000,
                signatures=['ARR']
            )
        )

        helpers.await_queue_edit(openreview_client, f'ARR/-/{cycle}/Meta_Review-0-0')
        
        assert openreview_client.get_invitation(f'ARR/-/{cycle}/Meta_Review')
        assert openreview_client.get_invitation(f'ARR/Submission1/-/{cycle}/Meta_Review')

    def test_review_rebuttal_stage(self, venue, openreview_client, helpers):
        cycle = '2023_March'

        assert openreview_client.get_invitation(f'ARR/-/{cycle}/Rebuttal')
        with pytest.raises(openreview.OpenReviewException, match=rf'The Invitation ARR/Submission1/-/{cycle}/Rebuttal was not found'):
            assert openreview_client.get_invitation(f'ARR/Submission1/-/{cycle}/Rebuttal')

        openreview_client.post_invitation_edit(
            invitations='ARR/-/Rebuttal',
            readers=['ARR'],
            writers=['ARR'],
            signatures=['ARR'],
            content={
                'subvenueid': {
                    'value': cycle
                }
            },
            invitation=openreview.api.Invitation(id=f'ARR/-/{cycle}/Rebuttal',
                signatures=['ARR'],
                cdate=openreview.tools.datetime_millis(datetime.datetime.utcnow()) + 2000,
            )
        )

        helpers.await_queue_edit(openreview_client, f'ARR/-/{cycle}/Rebuttal-0-0')

        assert openreview_client.get_invitation(f'ARR/-/{cycle}/Rebuttal')
        assert openreview_client.get_invitation(f'ARR/Submission1/-/{cycle}/Rebuttal')

    def test_withdraw_submission(self, venue, openreview_client, helpers):
        cycle = '2023_March'

        author_client = OpenReviewClient(username='harold@maileleven.com', password='1234')

        withdraw_note = author_client.post_note_edit(invitation='ARR/Submission2/-/Withdrawal',
                                    signatures=['ARR/Submission2/Authors'],
                                    note=Note(
                                        content={
                                            'withdrawal_confirmation': { 'value': 'I have read and agree with the venue\'s withdrawal policy on behalf of myself and my co-authors.' },
                                        }
                                    ))

        helpers.await_queue_edit(openreview_client, edit_id=withdraw_note['id'])

        note = author_client.get_note(withdraw_note['note']['forum'])
        assert note
        assert note.invitations == ['ARR/-/Submission', 'ARR/-/Post_Submission', 'ARR/-/Withdrawn_Submission']
        assert note.readers == ['ARR', 'ARR/Action_Editors', 'ARR/Reviewers', 'ARR/Submission2/Authors']
        assert note.writers == ['ARR', 'ARR/Submission2/Authors']
        assert note.signatures == ['ARR/Submission2/Authors']
        assert note.content['venue']['value'] == 'ARR Withdrawn Submission'
        assert note.content['venueid']['value'] == 'ARR/Withdrawn_2023_March_Submission'
        assert 'readers' not in note.content['authors']
        assert 'readers' not in note.content['authorids']

        helpers.await_queue_edit(openreview_client, invitation='ARR/-/Withdrawn_Submission')

        invitation = openreview_client.get_invitation(f'ARR/Submission2/-/2023_March/Meta_Review')
        assert invitation.expdate and invitation.expdate < openreview.tools.datetime_millis(datetime.datetime.utcnow())
        invitation =  openreview_client.get_invitation('ARR/Submission2/-/2023_March/Official_Review')
        assert invitation.expdate and invitation.expdate < openreview.tools.datetime_millis(datetime.datetime.utcnow())

        messages = openreview_client.get_messages(to='harold@maileleven.com', subject='[ARR]: Paper #2 withdrawn by paper authors')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == f'The ARR paper \"Paper 2 Title\" has been withdrawn by the paper authors.\n\nFor more information, click here https://openreview.net/forum?id={note.id}&noteId={withdraw_note["note"]["id"]}\n'

        assert openreview_client.get_invitation('ARR/Submission2/-/Withdrawal_Reversion')

        withdrawal_reversion_note = openreview_client.post_note_edit(invitation='ARR/Submission2/-/Withdrawal_Reversion',
                                    signatures=['ARR/Editors_In_Chief'],
                                    note=Note(
                                        content={
                                            'revert_withdrawal_confirmation': { 'value': 'We approve the reversion of withdrawn submission.' },
                                        }
                                    ))

        helpers.await_queue_edit(openreview_client, edit_id=withdrawal_reversion_note['id'])

        invitation = openreview_client.get_invitation('ARR/Submission2/-/2023_March/Meta_Review')
        assert invitation.expdate and invitation.expdate > openreview.tools.datetime_millis(datetime.datetime.utcnow())

        invitation =  openreview_client.get_invitation('ARR/Submission2/-/2023_March/Official_Review')
        assert invitation.expdate and invitation.expdate > openreview.tools.datetime_millis(datetime.datetime.utcnow())

        note = author_client.get_note(withdraw_note['note']['forum'])
        assert note
        assert note.invitations == ['ARR/-/Submission', 'ARR/-/Post_Submission']
        assert note.content['venue']['value'] == 'ARR 2023 March Submission'
        assert note.content['venueid']['value'] == 'ARR/2023_March/Submission'


        messages = openreview_client.get_messages(to='harold@maileleven.com', subject='[ARR]: Paper #2 restored by venue organizers')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == f'The ARR paper \"Paper 2 Title\" has been restored by the venue organizers.\n\nFor more information, click here https://openreview.net/forum?id={note.id}\n'

    def test_desk_reject_submission(self, venue, openreview_client, helpers):

        pc_client = OpenReviewClient(username='editors@aclrollingreview.org', password='1234')

        desk_reject_note = pc_client.post_note_edit(invitation='ARR/Submission2/-/Desk_Rejection',
                                    signatures=['ARR/Editors_In_Chief'],
                                    note=Note(
                                        content={
                                            'desk_reject_comments': { 'value': 'No PDF' },
                                        }
                                    ))

        helpers.await_queue_edit(openreview_client, edit_id=desk_reject_note['id'])

        note = pc_client.get_note(desk_reject_note['note']['forum'])
        assert note
        assert note.invitations == ['ARR/-/Submission', 'ARR/-/Post_Submission', 'ARR/-/Desk_Rejected_Submission']
        assert note.readers == ['ARR', 'ARR/Action_Editors', 'ARR/Reviewers', 'ARR/Submission2/Authors']
        assert note.writers == ['ARR', 'ARR/Submission2/Authors']
        assert note.signatures == ['ARR/Submission2/Authors']
        assert note.content['venue']['value'] == 'ARR Desk Rejected Submission'
        assert note.content['venueid']['value'] == 'ARR/Desk_Rejected_2023_March_Submission'
        assert 'readers' in note.content['authors']
        assert 'readers' in note.content['authorids']
        assert note.content['authors']['readers'] == ["ARR", "ARR/Submission2/Authors"]
        assert note.content['authorids']['readers'] == ["ARR", "ARR/Submission2/Authors"]

        helpers.await_queue_edit(openreview_client, invitation='ARR/-/Desk_Rejected_Submission')

        invitation = openreview_client.get_invitation('ARR/Submission2/-/2023_March/Meta_Review')
        assert invitation.expdate and invitation.expdate < openreview.tools.datetime_millis(datetime.datetime.utcnow())
        invitation =  openreview_client.get_invitation('ARR/Submission2/-/2023_March/Official_Review')
        assert invitation.expdate and invitation.expdate < openreview.tools.datetime_millis(datetime.datetime.utcnow())

        messages = openreview_client.get_messages(to='harold@maileleven.com', subject='[ARR]: Paper #2 desk-rejected by program chairs')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == f'The ARR paper \"Paper 2 Title\" has been desk-rejected by the program chairs.\n\nFor more information, click here https://openreview.net/forum?id={note.id}\n'

        messages = openreview_client.get_messages(to='editors@aclrollingreview.org', subject='[ARR]: Paper #2 desk-rejected by program chairs')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == f'The ARR paper \"Paper 2 Title\" has been desk-rejected by the program chairs.\n\nFor more information, click here https://openreview.net/forum?id={note.id}\n'

        assert openreview_client.get_invitation('ARR/Submission2/-/Desk_Rejection_Reversion')

        desk_rejection_reversion_note = openreview_client.post_note_edit(invitation='ARR/Submission2/-/Desk_Rejection_Reversion',
                                    signatures=['ARR/Editors_In_Chief'],
                                    note=Note(
                                        content={
                                            'revert_desk_rejection_confirmation': { 'value': 'We approve the reversion of desk-rejected submission.' },
                                        }
                                    ))

        helpers.await_queue_edit(openreview_client, edit_id=desk_rejection_reversion_note['id'])

        invitation = openreview_client.get_invitation('ARR/Submission2/-/2023_March/Meta_Review')
        assert invitation.expdate and invitation.expdate > openreview.tools.datetime_millis(datetime.datetime.utcnow())

        invitation =  openreview_client.get_invitation('ARR/Submission2/-/2023_March/Official_Review')
        assert invitation.expdate and invitation.expdate > openreview.tools.datetime_millis(datetime.datetime.utcnow())

        note = pc_client.get_note(desk_reject_note['note']['forum'])
        assert note
        assert note.invitations == ['ARR/-/Submission', 'ARR/-/Post_Submission']
        assert note.content['venue']['value'] == 'ARR 2023 March Submission'
        assert note.content['venueid']['value'] == 'ARR/2023_March/Submission'

        messages = openreview_client.get_messages(to='harold@maileleven.com', subject='[ARR]: Paper #2 restored by venue organizers')
        assert len(messages) == 2
        assert messages[0]['content']['text'] == f'The ARR paper \"Paper 2 Title\" has been restored by the venue organizers.\n\nFor more information, click here https://openreview.net/forum?id={note.id}\n'

        messages = openreview_client.get_messages(to='editors@aclrollingreview.org', subject='[ARR]: Paper #2 restored by venue organizers')
        assert len(messages) == 2
        assert messages[1]['content']['text'] == f'The desk-rejected ARR paper \"Paper 2 Title\" has been restored by the venue organizers.\n\nFor more information, click here https://openreview.net/forum?id={note.id}\n'

    def test_comment_stage(self, venue, openreview_client, helpers):

        #release papers to the public
        venue.submission_stage = SubmissionStage(double_blind=True, readers=[openreview.builder.SubmissionStage.Readers.EVERYONE])
        cycle = '2023_March'

        venue.create_submission_stage(sub_venue_id=cycle)

        submissions = venue.get_submissions(submission_venue_id=venue.get_submission_venue_id(f'{cycle}/Submission'))
        assert submissions and len(submissions) == 2
        assert submissions[0].readers == ['everyone']
        assert submissions[1].readers == ['everyone']

        now = datetime.datetime.utcnow()
        venue.comment_stage = openreview.CommentStage(
            allow_public_comments=True,
            reader_selection=True,
            email_pcs=True,
            check_mandatory_readers=True,
            readers=[openreview.CommentStage.Readers.REVIEWERS_ASSIGNED,openreview.CommentStage.Readers.AREA_CHAIRS_ASSIGNED,openreview.CommentStage.Readers.SENIOR_AREA_CHAIRS_ASSIGNED,openreview.CommentStage.Readers.AUTHORS,openreview.CommentStage.Readers.EVERYONE],
            invitees=[openreview.CommentStage.Readers.REVIEWERS_ASSIGNED,openreview.CommentStage.Readers.AREA_CHAIRS_ASSIGNED,openreview.CommentStage.Readers.SENIOR_AREA_CHAIRS_ASSIGNED,openreview.CommentStage.Readers.AUTHORS])
        venue.create_comment_stage(sub_venue_id=cycle)

        invitation = openreview_client.get_invitation(venue.id + '/Submission1/-/2023_March/Public_Comment') ## TODO: Also make public comments?
        assert not invitation.expdate
        invitation = openreview_client.get_invitation(venue.id + '/Submission1/-/2023_March/Official_Comment')
        assert not invitation.expdate