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

class TestVenueSubmission():

    @pytest.fixture(scope="class")
    def venue(self, openreview_client):
        conference_id = 'TestVenue.cc'

        venue = Venue(openreview_client, conference_id, 'openreview.net/Support')
        venue.use_area_chairs = True
        venue.name = 'Test Venue V2'
        venue.short_name = 'TV 22'
        venue.website = 'testvenue.org'
        venue.contact = 'testvenue@contact.com'
        venue.reviewer_identity_readers = [openreview.stages.IdentityReaders.PROGRAM_CHAIRS, openreview.stages.IdentityReaders.AREA_CHAIRS_ASSIGNED]

        now = datetime.datetime.utcnow()
        venue.submission_stage = SubmissionStage(double_blind=True, readers=[SubmissionStage.Readers.EVERYONE], withdrawn_submission_public=True, withdrawn_submission_reveal_authors=True, desk_rejected_submission_public=True)

        venue.bid_stages = [
            BidStage(due_date=now + datetime.timedelta(minutes = 30), committee_id=venue.get_reviewers_id()),
            BidStage(due_date=now + datetime.timedelta(minutes = 30), committee_id=venue.get_area_chairs_id())
        ]        
        venue.review_stage = openreview.stages.ReviewStage(start_date=now + datetime.timedelta(minutes = 4), due_date=now + datetime.timedelta(minutes = 40))
        venue.meta_review_stage = openreview.stages.MetaReviewStage(start_date=now + datetime.timedelta(minutes = 10), due_date=now + datetime.timedelta(minutes = 40))
        venue.submission_revision_stage = openreview.SubmissionRevisionStage(
            name='Camera_Ready_Revision',
            due_date=now + datetime.timedelta(minutes = 40),
            only_accepted=True
        )

        return venue

    def test_setup(self, venue, openreview_client, helpers):

        venue.setup(program_chair_ids=['venue_pc@mail.com'])
        venue.create_submission_stage()
        venue.create_review_stage()
        venue.create_meta_review_stage()
        venue.create_submission_revision_stage()
        assert openreview_client.get_group('TestVenue.cc')
        assert openreview_client.get_group('TestVenue.cc/Authors')

        helpers.create_user('venue_pc@mail.com', 'PC Venue', 'One')

    def test_recruitment_stage(self, venue, openreview_client, selenium, request_page, helpers):

        #recruit reviewers and area chairs to create groups
        message = 'Dear {{fullname}},\n\nYou have been nominated by the program chair committee of Test Venue V2 to serve as {{invitee_role}}.\n\nTo respond to the invitation, please click on the following link:\n\n{{invitation_url}}\n\nCheers!\n\nProgram Chairs'
        
        helpers.create_user('reviewer_venue_one@mail.com', 'Reviewer Venue', 'One')
        
        venue.recruit_reviewers(title='[TV 22] Invitation to serve as Reviewer',
            message=message,
            invitees = ['~Reviewer_Venue_One1'],
            contact_info='testvenue@contact.com',
            reduced_load_on_decline = ['1','2','3'])

        venue.recruit_reviewers(title='[TV 22] Invitation to serve as Area Chair',
            message=message,
            invitees = ['~Reviewer_Venue_One1'],
            reviewers_name = 'Area_Chairs',
            contact_info='testvenue@contact.com',
            allow_overlap_official_committee = True)

        messages = openreview_client.get_messages(to='reviewer_venue_one@mail.com')
        assert messages
        invitation_url = re.search('https://.*\n', messages[1]['content']['text']).group(0).replace('https://openreview.net', 'http://localhost:3030')[:-1]
        helpers.respond_invitation(selenium, request_page, invitation_url, accept=True, quota=1)

        reviewer_group = openreview_client.get_group('TestVenue.cc/Reviewers')
        assert reviewer_group
        assert '~Reviewer_Venue_One1' in reviewer_group.members    
    
    def test_submission_stage(self, venue, openreview_client, helpers):

        assert openreview_client.get_invitation('TestVenue.cc/-/Submission')

        helpers.create_user('celeste@maileleven.com', 'Celeste', 'MartinezEleven')
        author_client = OpenReviewClient(username='celeste@maileleven.com', password='1234')

        submission_note_1 = author_client.post_note_edit(
            invitation='TestVenue.cc/-/Submission',
            signatures= ['~Celeste_MartinezEleven1'],
            note=Note(
                content={
                    'title': { 'value': 'Paper 1 Title' },
                    'abstract': { 'value': 'Paper abstract' },
                    'authors': { 'value': ['Celeste MartinezEleven']},
                    'authorids': { 'value': ['~Celeste_MartinezEleven1']},
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                    'keywords': {'value': ['aa'] }
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=submission_note_1['id']) 

        submission = openreview_client.get_note(submission_note_1['note']['id'])
        assert len(submission.readers) == 2
        assert 'TestVenue.cc' in submission.readers
        assert ['TestVenue.cc', '~Celeste_MartinezEleven1'] == submission.readers

        #TODO: check emails, check author console

        submission_note_2 = author_client.post_note_edit(
            invitation='TestVenue.cc/-/Submission',
            signatures= ['~Celeste_MartinezEleven1'],
            note=Note(
                content={
                    'title': { 'value': 'Paper 2 Title' },
                    'abstract': { 'value': 'Paper abstract' },
                    'authors': { 'value': ['Celeste MartinezEleven']},
                    'authorids': { 'value': ['~Celeste_MartinezEleven1']},
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                    'keywords': {'value': ['aa'] }
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=submission_note_2['id']) 

    def test_post_submission_stage(self, venue, openreview_client):
                
        venue.submission_stage.readers = [SubmissionStage.Readers.REVIEWERS, SubmissionStage.Readers.AREA_CHAIRS]
        venue.setup_post_submission_stage()
        assert openreview_client.get_group('TestVenue.cc/Submission1/Authors')
        assert openreview_client.get_group('TestVenue.cc/Submission1/Reviewers')
        assert openreview_client.get_group('TestVenue.cc/Submission1/Area_Chairs')

        submissions = venue.get_submissions(sort='number:asc')
        assert len(submissions) == 2
        submission = submissions[0]
        assert len(submission.readers) == 4
        assert 'TestVenue.cc' in submission.readers
        assert 'TestVenue.cc/Submission1/Authors' in submission.readers        
        assert 'TestVenue.cc/Reviewers' in submission.readers
        assert 'TestVenue.cc/Area_Chairs' in submission.readers

        assert openreview_client.get_invitation('TestVenue.cc/Submission1/-/Withdrawal')
        assert openreview_client.get_invitation('TestVenue.cc/Submission2/-/Withdrawal')

        assert openreview_client.get_invitation('TestVenue.cc/Submission1/-/Desk_Rejection')
        assert openreview_client.get_invitation('TestVenue.cc/Submission2/-/Desk_Rejection')

    def test_bid_stage(self, venue, openreview_client):
        
        reviewer_client = OpenReviewClient(username='reviewer_venue_one@mail.com', password='1234')
        venue.create_bid_stages()

        assert openreview_client.get_invitation(venue.id + '/Reviewers/-/Bid')
        assert openreview_client.get_invitation(venue.id + '/Area_Chairs/-/Bid')

        submissions = venue.get_submissions()

        bid_edge = reviewer_client.post_edge(Edge(invitation = venue.id + '/Reviewers/-/Bid',
            head = submissions[0].id,
            tail = '~Reviewer_Venue_One1',
            readers = ['TestVenue.cc', 'TestVenue.cc/Area_Chairs', '~Reviewer_Venue_One1'],
            writers = ['TestVenue.cc', '~Reviewer_Venue_One1'],
            signatures = ['~Reviewer_Venue_One1'],
            label = 'High'
        ))

        bid_edges = openreview_client.get_edges_count(invitation=venue.id + '/Reviewers/-/Bid')
        assert bid_edges == 1

        ## after bidding stage the submissions should be visible to the assigned committee
        venue.submission_stage.readers = [SubmissionStage.Readers.EVERYONE]
        venue.setup_post_submission_stage()
        submissions = venue.get_submissions(sort='number:asc')
        assert len(submissions) == 2
        submission = submissions[0]
        assert len(submission.readers) == 1
        assert 'everyone' in submission.readers
    
    def test_setup_matching(self, venue, openreview_client, helpers):

        venue.setup_committee_matching(committee_id='TestVenue.cc/Reviewers', compute_conflicts=True)

        submissions = venue.get_submissions(sort='number:asc')
        # #test posting proposed assignment edge
        proposed_assignment_edge = openreview_client.post_edge(Edge(
            invitation = venue.id + '/Reviewers/-/Proposed_Assignment',
            # signatures = ['TestVenue.cc'],
            signatures = ['TestVenue.cc/Submission1/Area_Chairs'],
            head = submissions[0].id,
            tail = '~Reviewer_Venue_One1',
            readers = ['TestVenue.cc','TestVenue.cc/Submission1/Area_Chairs','~Reviewer_Venue_One1'],
            writers = ['TestVenue.cc','TestVenue.cc/Submission1/Area_Chairs'],
            weight = 0.92,
            label = 'test-matching-1'
        ))

        assert proposed_assignment_edge
        assert proposed_assignment_edge.nonreaders == ['TestVenue.cc/Submission1/Authors']

        custom_load_edges = openreview_client.get_edges_count(invitation='TestVenue.cc/Reviewers/-/Custom_Max_Papers')
        assert custom_load_edges == 1

    def test_review_stage(self, venue, openreview_client, helpers):

        assert openreview_client.get_invitation('TestVenue.cc/-/Official_Review')
        with pytest.raises(openreview.OpenReviewException, match=r'The Invitation TestVenue.cc/Submission1/-/Official_Review was not found'):
            assert openreview_client.get_invitation('TestVenue.cc/Submission1/-/Official_Review')

        openreview_client.post_invitation_edit(
            invitations='TestVenue.cc/-/Edit',
            readers=['TestVenue.cc'],
            writers=['TestVenue.cc'],
            signatures=['TestVenue.cc'],
            invitation=openreview.api.Invitation(id='TestVenue.cc/-/Official_Review',
                cdate=openreview.tools.datetime_millis(datetime.datetime.utcnow()) + 2000,
                signatures=['TestVenue.cc']
            )
        )

        helpers.await_queue_edit(openreview_client, 'TestVenue.cc/-/Official_Review-0-0')

        assert openreview_client.get_invitation('TestVenue.cc/-/Official_Review')
        assert openreview_client.get_invitation('TestVenue.cc/Submission1/-/Official_Review')

    def test_meta_review_stage(self, venue, openreview_client, helpers):

        assert openreview_client.get_invitation('TestVenue.cc/-/Meta_Review')
        with pytest.raises(openreview.OpenReviewException, match=r'The Invitation TestVenue.cc/Submission1/-/Meta_Review was not found'):
            assert openreview_client.get_invitation('TestVenue.cc/Submission1/-/Meta_Review')

        openreview_client.post_invitation_edit(
            invitations='TestVenue.cc/-/Edit',
            readers=['TestVenue.cc'],
            writers=['TestVenue.cc'],
            signatures=['TestVenue.cc'],
            invitation=openreview.api.Invitation(id='TestVenue.cc/-/Meta_Review',
                cdate=openreview.tools.datetime_millis(datetime.datetime.utcnow()) + 2000,
                signatures=['TestVenue.cc']
            )
        )

        helpers.await_queue_edit(openreview_client, 'TestVenue.cc/-/Meta_Review-0-0')
        
        assert openreview_client.get_invitation('TestVenue.cc/-/Meta_Review')
        assert openreview_client.get_invitation('TestVenue.cc/Submission1/-/Meta_Review')

    def test_withdraw_submission(self, venue, openreview_client, helpers):

        author_client = OpenReviewClient(username='celeste@maileleven.com', password='1234')

        withdraw_note = author_client.post_note_edit(invitation='TestVenue.cc/Submission2/-/Withdrawal',
                                    signatures=['TestVenue.cc/Submission2/Authors'],
                                    note=Note(
                                        content={
                                            'withdrawal_confirmation': { 'value': 'I have read and agree with the venue\'s withdrawal policy on behalf of myself and my co-authors.' },
                                        }
                                    ))

        helpers.await_queue_edit(openreview_client, edit_id=withdraw_note['id'])

        note = author_client.get_note(withdraw_note['note']['forum'])
        assert note
        assert note.invitations == ['TestVenue.cc/-/Submission', 'TestVenue.cc/-/Edit', 'TestVenue.cc/-/Withdrawn_Submission']
        assert note.readers == ['everyone']
        assert note.writers == ['TestVenue.cc', 'TestVenue.cc/Submission2/Authors']
        assert note.signatures == ['TestVenue.cc/Submission2/Authors']
        assert note.content['venue']['value'] == 'TestVenue Withdrawn Submission'
        assert note.content['venueid']['value'] == 'TestVenue.cc/Withdrawn_Submission'
        assert 'readers' not in note.content['authors']
        assert 'readers' not in note.content['authorids']

        helpers.await_queue_edit(openreview_client, invitation='TestVenue.cc/-/Withdrawn_Submission')

        invitation = openreview_client.get_invitation('TestVenue.cc/Submission2/-/Meta_Review')
        assert invitation.expdate and invitation.expdate < openreview.tools.datetime_millis(datetime.datetime.utcnow())
        invitation =  openreview_client.get_invitation('TestVenue.cc/Submission2/-/Official_Review')
        assert invitation.expdate and invitation.expdate < openreview.tools.datetime_millis(datetime.datetime.utcnow())

        messages = openreview_client.get_messages(to='celeste@maileleven.com', subject='[TV 22]: Paper #2 withdrawn by paper authors')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == f'The TV 22 paper \"Paper 2 Title\" has been withdrawn by the paper authors.\n\nFor more information, click here https://openreview.net/forum?id={note.id}\n'

        assert openreview_client.get_invitation('TestVenue.cc/Submission2/-/Withdrawal_Reversion')

        withdrawal_reversion_note = openreview_client.post_note_edit(invitation='TestVenue.cc/Submission2/-/Withdrawal_Reversion',
                                    signatures=['TestVenue.cc/Program_Chairs'],
                                    note=Note(
                                        content={
                                            'revert_withdrawal_confirmation': { 'value': 'We approve the reversion of withdrawn submission.' },
                                        }
                                    ))

        helpers.await_queue_edit(openreview_client, edit_id=withdrawal_reversion_note['id'])

        invitation = openreview_client.get_invitation('TestVenue.cc/Submission2/-/Meta_Review')
        assert invitation.expdate and invitation.expdate > openreview.tools.datetime_millis(datetime.datetime.utcnow())

        invitation =  openreview_client.get_invitation('TestVenue.cc/Submission2/-/Official_Review')
        assert invitation.expdate and invitation.expdate > openreview.tools.datetime_millis(datetime.datetime.utcnow())

        note = author_client.get_note(withdraw_note['note']['forum'])
        assert note
        assert note.invitations == ['TestVenue.cc/-/Submission', 'TestVenue.cc/-/Edit']
        assert note.content['venue']['value'] == 'TestVenue Submission'
        assert note.content['venueid']['value'] == 'TestVenue.cc/Submission'


        messages = openreview_client.get_messages(to='celeste@maileleven.com', subject='[TV 22]: Paper #2 restored by venue organizers')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == f'The TV 22 paper \"Paper 2 Title\" has been restored by the venue organizers.\n\nFor more information, click here https://openreview.net/forum?id={note.id}\n'

    def test_desk_reject_submission(self, venue, openreview_client, helpers):

        pc_client = OpenReviewClient(username='venue_pc@mail.com', password='1234')

        desk_reject_note = pc_client.post_note_edit(invitation='TestVenue.cc/Submission2/-/Desk_Rejection',
                                    signatures=['TestVenue.cc/Program_Chairs'],
                                    note=Note(
                                        content={
                                            'desk_reject_comments': { 'value': 'No PDF' },
                                        }
                                    ))

        helpers.await_queue_edit(openreview_client, edit_id=desk_reject_note['id'])

        note = pc_client.get_note(desk_reject_note['note']['forum'])
        assert note
        assert note.invitations == ['TestVenue.cc/-/Submission', 'TestVenue.cc/-/Edit', 'TestVenue.cc/-/Desk_Rejected_Submission']
        assert note.readers == ['everyone']
        assert note.writers == ['TestVenue.cc', 'TestVenue.cc/Submission2/Authors']
        assert note.signatures == ['TestVenue.cc/Submission2/Authors']
        assert note.content['venue']['value'] == 'TestVenue Desk Rejected Submission'
        assert note.content['venueid']['value'] == 'TestVenue.cc/Desk_Rejected_Submission'
        assert 'readers' in note.content['authors']
        assert 'readers' in note.content['authorids']
        assert note.content['authors']['readers'] == ["TestVenue.cc", "TestVenue.cc/Submission2/Authors"]
        assert note.content['authorids']['readers'] == ["TestVenue.cc", "TestVenue.cc/Submission2/Authors"]

        helpers.await_queue_edit(openreview_client, invitation='TestVenue.cc/-/Desk_Rejected_Submission')

        invitation = openreview_client.get_invitation('TestVenue.cc/Submission2/-/Meta_Review')
        assert invitation.expdate and invitation.expdate < openreview.tools.datetime_millis(datetime.datetime.utcnow())
        invitation =  openreview_client.get_invitation('TestVenue.cc/Submission2/-/Official_Review')
        assert invitation.expdate and invitation.expdate < openreview.tools.datetime_millis(datetime.datetime.utcnow())

        messages = openreview_client.get_messages(to='celeste@maileleven.com', subject='[TV 22]: Paper #2 desk-rejected by program chairs')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == f'The TV 22 paper \"Paper 2 Title\" has been desk-rejected by the program chairs.\n\nFor more information, click here https://openreview.net/forum?id={note.id}\n'

        messages = openreview_client.get_messages(to='venue_pc@mail.com', subject='[TV 22]: Paper #2 desk-rejected by program chairs')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == f'The TV 22 paper \"Paper 2 Title\" has been desk-rejected by the program chairs.\n\nFor more information, click here https://openreview.net/forum?id={note.id}\n'

        assert openreview_client.get_invitation('TestVenue.cc/Submission2/-/Desk_Rejection_Reversion')

        desk_rejection_reversion_note = openreview_client.post_note_edit(invitation='TestVenue.cc/Submission2/-/Desk_Rejection_Reversion',
                                    signatures=['TestVenue.cc/Program_Chairs'],
                                    note=Note(
                                        content={
                                            'revert_desk_rejection_confirmation': { 'value': 'We approve the reversion of desk-rejected submission.' },
                                        }
                                    ))

        helpers.await_queue_edit(openreview_client, edit_id=desk_rejection_reversion_note['id'])

        invitation = openreview_client.get_invitation('TestVenue.cc/Submission2/-/Meta_Review')
        assert invitation.expdate and invitation.expdate > openreview.tools.datetime_millis(datetime.datetime.utcnow())

        invitation =  openreview_client.get_invitation('TestVenue.cc/Submission2/-/Official_Review')
        assert invitation.expdate and invitation.expdate > openreview.tools.datetime_millis(datetime.datetime.utcnow())

        note = pc_client.get_note(desk_reject_note['note']['forum'])
        assert note
        assert note.invitations == ['TestVenue.cc/-/Submission', 'TestVenue.cc/-/Edit']
        assert note.content['venue']['value'] == 'TestVenue Submission'
        assert note.content['venueid']['value'] == 'TestVenue.cc/Submission'

        messages = openreview_client.get_messages(to='celeste@maileleven.com', subject='[TV 22]: Paper #2 restored by venue organizers')
        assert len(messages) == 2
        assert messages[0]['content']['text'] == f'The TV 22 paper \"Paper 2 Title\" has been restored by the venue organizers.\n\nFor more information, click here https://openreview.net/forum?id={note.id}\n'

        messages = openreview_client.get_messages(to='venue_pc@mail.com', subject='[TV 22]: Paper #2 restored by venue organizers')
        assert len(messages) == 2
        assert messages[1]['content']['text'] == f'The desk-rejected TV 22 paper \"Paper 2 Title\" has been restored by the venue organizers.\n\nFor more information, click here https://openreview.net/forum?id={note.id}\n'

    def test_comment_stage(self, venue, openreview_client, helpers):

        #release papers to the public
        venue.submission_stage = SubmissionStage(double_blind=True, readers=[openreview.builder.SubmissionStage.Readers.EVERYONE])
        venue.create_submission_stage()
        venue.setup_post_submission_stage()

        submissions = venue.get_submissions()
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
        venue.create_comment_stage()

        invitation = openreview_client.get_invitation(venue.id + '/Submission1/-/Public_Comment')
        assert not invitation.expdate
        invitation = openreview_client.get_invitation(venue.id + '/Submission1/-/Official_Comment')
        assert not invitation.expdate

    def test_decision_stage(self, venue, openreview_client, helpers):

        submissions = venue.get_submissions(sort='number:asc')
        assert submissions and len(submissions) == 2

        with open(os.path.join(os.path.dirname(__file__), 'data/venue_decision.csv'), 'w') as file_handle:
            writer = csv.writer(file_handle)
            writer.writerow([submissions[0].number, 'Accept (Oral)', 'Good Paper'])

        now = datetime.datetime.utcnow()
        venue.decision_stage = openreview.DecisionStage(
            due_date=now + datetime.timedelta(minutes = 40),
            decisions_file = os.path.join(os.path.dirname(__file__), 'data/venue_decision.csv'))
        venue.create_decision_stage()

        assert openreview_client.get_invitation(venue.id + '/Submission1/-/Decision')

        decision = openreview_client.get_notes(invitation=venue.id + '/Submission1/-/Decision')
        assert len(decision) == 1
        assert 'Accept (Oral)' == decision[0].content['decision']['value']

    def test_post_decision_stage(self, venue, openreview_client):

        venue.post_decision_stage()

    def test_submission_revision_stage(self, venue, openreview_client, helpers):

        assert openreview_client.get_invitation('TestVenue.cc/-/Camera_Ready_Revision')
        with pytest.raises(openreview.OpenReviewException, match=r'The Invitation TestVenue.cc/Submission1/-/Camera_Ready_Revision was not found'):
            assert openreview_client.get_invitation('TestVenue.cc/Submission1/-/Camera_Ready_Revision')

        openreview_client.post_invitation_edit(
            invitations='TestVenue.cc/-/Edit',
            readers=['TestVenue.cc'],
            writers=['TestVenue.cc'],
            signatures=['TestVenue.cc'],
            invitation=openreview.api.Invitation(id='TestVenue.cc/-/Camera_Ready_Revision',
                cdate=openreview.tools.datetime_millis(datetime.datetime.utcnow()) + 2000,
                signatures=['TestVenue.cc']
            )
        )

        helpers.await_queue_edit(openreview_client, 'TestVenue.cc/-/Camera_Ready_Revision-0-0')

        assert openreview_client.get_invitation('TestVenue.cc/-/Camera_Ready_Revision')
        assert openreview.tools.get_invitation(openreview_client, 'TestVenue.cc/Submission1/-/Camera_Ready_Revision')
        assert not openreview.tools.get_invitation(openreview_client, 'TestVenue.cc/Submission2/-/Camera_Ready_Revision')