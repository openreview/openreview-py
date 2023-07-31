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
        venue.invitation_builder.update_wait_time = 2000
        venue.invitation_builder.update_date_string = "#{4/mdate} + 2000"
        venue.automatic_reviewer_assignment = True 
        venue.use_area_chairs = True
        venue.name = 'Test Venue V2'
        venue.short_name = 'TV 22'
        venue.website = 'testvenue.org'
        venue.contact = 'testvenue@contact.com'
        venue.reviewer_identity_readers = [openreview.stages.IdentityReaders.PROGRAM_CHAIRS, openreview.stages.IdentityReaders.AREA_CHAIRS_ASSIGNED]

        now = datetime.datetime.utcnow()
        venue.submission_stage = SubmissionStage(
            double_blind=True,
            due_date=now + datetime.timedelta(minutes = 30),
            readers=[SubmissionStage.Readers.EVERYONE], 
            withdrawn_submission_public=True, 
            withdrawn_submission_reveal_authors=True, 
            desk_rejected_submission_public=True,
            force_profiles=True,
            remove_fields=['abstract']
        )

        venue.bid_stages = [
            BidStage(due_date=now + datetime.timedelta(minutes = 30), committee_id=venue.get_reviewers_id()),
            BidStage(due_date=now + datetime.timedelta(minutes = 30), committee_id=venue.get_area_chairs_id())
        ]        
        venue.review_stage = openreview.stages.ReviewStage(start_date=now + datetime.timedelta(minutes = 4), due_date=now + datetime.timedelta(minutes = 40))
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
        venue.meta_review_stage = openreview.stages.MetaReviewStage(start_date=now + datetime.timedelta(minutes = 10), due_date=now + datetime.timedelta(minutes = 40))
        venue.submission_revision_stage = openreview.SubmissionRevisionStage(
            name='Camera_Ready_Revision',
            due_date=now + datetime.timedelta(minutes = 40),
            only_accepted=True
        )

        venue.custom_stage = openreview.stages.CustomStage(
            name='Camera_Ready_Verification',
            source=openreview.stages.CustomStage.Source.ACCEPTED_SUBMISSIONS,
            reply_to=openreview.stages.CustomStage.ReplyTo.FORUM,
            start_date=now + datetime.timedelta(minutes = 10),
            due_date=now + datetime.timedelta(minutes = 40),
            readers=[openreview.stages.CustomStage.Participants.AREA_CHAIRS_ASSIGNED, openreview.stages.CustomStage.Participants.AUTHORS],
            content={
                "verification": {
                    "order": 1,
                    "value": {
                    "param": {
                        "type": "string",
                        "enum": [
                        "I confirm that camera ready manuscript complies with the TV 22 stylefile and, if appropriate, includes the minor revisions that were requested."
                        ],
                        "input": "checkbox"
                    }
                    }
                }
            },
            notify_readers=True,
            email_pcs=True,
            email_template='''The camera ready verification for submission number {submission_number} has been posted.
Please follow this link: https://openreview.net/forum?id={submission_id}&noteId={note_id}'''
        )

        return venue

    def test_setup(self, venue, openreview_client, helpers):

        venue.setup(program_chair_ids=['venue_pc@mail.com'])
        venue.create_submission_stage()
        venue.create_review_stage()
        venue.create_review_rebuttal_stage()
        venue.create_meta_review_stage()
        venue.create_submission_revision_stage()
        venue.create_custom_stage()
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

        #make sure there's no error if recruitment invitation does not have to be updated
        venue.recruit_reviewers(title='[TV 22] Invitation to serve as Reviewer',
            message=message,
            invitees = ['ana@mail.com'],
            contact_info='testvenue@contact.com',
            reduced_load_on_decline = ['1','2','3'])

        venue.recruit_reviewers(title='[TV 22] Invitation to serve as Area Chair',
            message=message,
            invitees = ['~Reviewer_Venue_One1'],
            reviewers_name = 'Area_Chairs',
            contact_info='testvenue@contact.com',
            allow_overlap_official_committee = True)

        recruitment_inv = openreview_client.get_invitation('TestVenue.cc/Area_Chairs/-/Recruitment')
        assert 'overlap_committee_name' not in recruitment_inv.content
        assert 'reduced_load' not in recruitment_inv.edit['note']['content']

        messages = openreview_client.get_messages(to='reviewer_venue_one@mail.com')
        assert messages
        invitation_url = re.search('https://.*\n', messages[1]['content']['text']).group(0).replace('https://openreview.net', 'http://localhost:3030')[:-1]
        helpers.respond_invitation(selenium, request_page, invitation_url, accept=True, quota=1)

        reviewer_group = openreview_client.get_group('TestVenue.cc/Reviewers')
        assert reviewer_group
        assert '~Reviewer_Venue_One1' in reviewer_group.members

        venue.recruit_reviewers(title='[TV 22] Invitation to serve as Area Chair',
            message=message,
            invitees = ['celeste@email.com'],
            reviewers_name = 'Area_Chairs',
            contact_info='testvenue@contact.com',
            allow_overlap_official_committee = False,
            reduced_load_on_decline = ['1', '2'])

        recruitment_inv = openreview_client.get_invitation('TestVenue.cc/Area_Chairs/-/Recruitment')
        assert 'overlap_committee_name' in recruitment_inv.content and recruitment_inv.content['overlap_committee_name']['value'] == 'Reviewers'
        assert 'reduced_load' in recruitment_inv.edit['note']['content'] and recruitment_inv.edit['note']['content']['reduced_load']['value']['param']['enum'] == ['1', '2']
    
    def test_submission_stage(self, venue, openreview_client, helpers):

        assert openreview_client.get_invitation('TestVenue.cc/-/Submission')

        helpers.create_user('celeste@maileleven.com', 'Celeste', 'MartinezEleven')
        author_client = OpenReviewClient(username='celeste@maileleven.com', password=helpers.strong_password)

        submission_note_1 = author_client.post_note_edit(
            invitation='TestVenue.cc/-/Submission',
            signatures= ['~Celeste_MartinezEleven1'],
            note=Note(
                content={
                    'title': { 'value': 'Paper 1 Title' },
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

        messages = openreview_client.get_messages(subject = 'TV 22 has received your submission titled Paper 1 Title')
        assert len(messages) == 1
        assert 'Your submission to TV 22 has been posted.' in messages[0]['content']['text']

        #update submission 1
        updated_submission_note_1 = author_client.post_note_edit(invitation='TestVenue.cc/-/Submission',
            signatures=['~Celeste_MartinezEleven1'],
            note=Note(id=submission.id,
                content={
                    'title': { 'value': 'Paper 1 Title UPDATED' },
                    'authors': { 'value': ['Celeste MartinezEleven', 'Celeste MartinezTwelve']},
                    'authorids': { 'value': ['~Celeste_MartinezEleven1', '~Celeste_MartinezEleven1']},
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                    'keywords': {'value': ['aa'] }
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=updated_submission_note_1['id'])

        messages = openreview_client.get_messages(subject = 'TV 22 has received your submission titled Paper 1 Title UPDATED')
        assert len(messages) == 1
        assert 'Your submission to TV 22 has been updated.' in messages[0]['content']['text']

        authors_group = openreview_client.get_group('TestVenue.cc/Submission1/Authors')
        assert len(authors_group.members) == 1 and ['~Celeste_MartinezEleven1'] == authors_group.members

        with pytest.raises(openreview.OpenReviewException, match=r'authorids value/1 must match pattern "~.*"'):
            submission_note_2 = author_client.post_note_edit(
                invitation='TestVenue.cc/-/Submission',
                signatures= ['~Celeste_MartinezEleven1'],
                note=Note(
                    content={
                        'title': { 'value': 'Paper 2 Title' },
                        'authors': { 'value': ['Celeste MartinezEleven', 'Melisa BokEleven']},
                        'authorids': { 'value': ['~Celeste_MartinezEleven1', 'melisa@maileleven.com']},
                        'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                        'keywords': {'value': ['aa'] }
                    }
                ))
            
        helpers.create_user('melisa@maileleven.com', 'Melisa', 'BokEleven')

        submission_note_2 = author_client.post_note_edit(
                invitation='TestVenue.cc/-/Submission',
                signatures= ['~Celeste_MartinezEleven1'],
                note=Note(
                    content={
                        'title': { 'value': 'Paper 2 Title' },
                        'authors': { 'value': ['Celeste MartinezEleven', 'Melisa BokEleven']},
                        'authorids': { 'value': ['~Celeste_MartinezEleven1', '~Melisa_BokEleven1']},
                        'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                        'keywords': {'value': ['aa'] }
                    }
                ))

        helpers.await_queue_edit(openreview_client, edit_id=submission_note_2['id']) 

    def test_post_submission_stage(self, venue, openreview_client, helpers):
                
        venue.submission_stage.readers = [SubmissionStage.Readers.REVIEWERS, SubmissionStage.Readers.AREA_CHAIRS]
        venue.submission_stage.exp_date = datetime.datetime.utcnow() + datetime.timedelta(seconds = 60)
        venue.create_submission_stage()

        helpers.await_queue_edit(openreview_client, 'TestVenue.cc/-/Post_Submission-0-0')
        helpers.await_queue_edit(openreview_client, 'TestVenue.cc/Reviewers/-/Submission_Group-0-0')
        helpers.await_queue_edit(openreview_client, 'TestVenue.cc/Area_Chairs/-/Submission_Group-0-0')

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

        helpers.await_queue_edit(openreview_client, 'TestVenue.cc/-/Withdrawal-0-0')
        
        assert openreview_client.get_invitation('TestVenue.cc/Submission1/-/Withdrawal')
        assert openreview_client.get_invitation('TestVenue.cc/Submission2/-/Withdrawal')

        helpers.await_queue_edit(openreview_client, 'TestVenue.cc/-/Desk_Rejection-0-0')

        assert openreview_client.get_invitation('TestVenue.cc/Submission1/-/Desk_Rejection')
        assert openreview_client.get_invitation('TestVenue.cc/Submission2/-/Desk_Rejection')

        ## post a submission after the deadline
        pc_client = OpenReviewClient(username='venue_pc@mail.com', password=helpers.strong_password)
        submission_note_3 = pc_client.post_note_edit(
            invitation='TestVenue.cc/-/Submission',
            signatures= ['~PC_Venue_One1'],
            note=Note(
                content={
                    'title': { 'value': 'Paper 3 Title' },
                    'authors': { 'value': ['Celeste MartinezEleven']},
                    'authorids': { 'value': ['~Celeste_MartinezEleven1']},
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                    'keywords': {'value': ['aa'] }
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=submission_note_3['id'])

        assert openreview_client.get_group('TestVenue.cc/Submission3/Authors')
        assert openreview_client.get_group('TestVenue.cc/Submission3/Reviewers')
        assert openreview_client.get_group('TestVenue.cc/Submission3/Area_Chairs')
        assert openreview_client.get_invitation('TestVenue.cc/Submission3/-/Withdrawal')
        assert openreview_client.get_invitation('TestVenue.cc/Submission3/-/Desk_Rejection')

    def test_bid_stage(self, venue, openreview_client, helpers):
        
        reviewer_client = OpenReviewClient(username='reviewer_venue_one@mail.com', password=helpers.strong_password)
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
        venue.create_post_submission_stage()

        helpers.await_queue_edit(openreview_client, 'TestVenue.cc/-/Post_Submission-0-1', count=3)

        submissions = venue.get_submissions(sort='number:asc')
        assert len(submissions) == 3
        submission = submissions[0]
        assert len(submission.readers) == 1
        assert 'everyone' in submission.readers
    
    def test_setup_matching(self, venue, openreview_client, helpers):

        submissions = venue.get_submissions(sort='number:asc')

        helpers.create_user('reviewer_venue_two@mail.com', 'Reviewer Venue', 'Two')
        helpers.create_user('reviewer_venue_three@mail.com', 'Reviewer Venue', 'Three')

        with open(os.path.join(os.path.dirname(__file__), 'data/venue_affinity_scores.csv'), 'w') as file_handle:
            writer = csv.writer(file_handle)
            for submission in submissions:
                writer.writerow([submission.id, '~Reviewer_Venue_One1', round(random.random(), 2)])
                writer.writerow([submission.id, '~Reviewer_Venue_Two1', round(random.random(), 2)])
                writer.writerow([submission.id, '~Reviewer_Venue_Three1', round(random.random(), 2)])

        venue.setup_committee_matching(
            committee_id='TestVenue.cc/Reviewers',
            compute_affinity_scores=os.path.join(os.path.dirname(__file__), 'data/venue_affinity_scores.csv'),
            compute_conflicts=True)

        scores_invitation = openreview.tools.get_invitation(openreview_client, 'TestVenue.cc/Reviewers/-/Affinity_Score')
        assert scores_invitation

        affinity_edges = openreview_client.get_edges_count(invitation='TestVenue.cc/Reviewers/-/Affinity_Score')
        assert affinity_edges == 9

        conflict_invitation = openreview.tools.get_invitation(openreview_client, 'TestVenue.cc/Reviewers/-/Conflict')
        assert conflict_invitation

        # #test posting proposed assignment edge
        proposed_assignment_edge = openreview_client.post_edge(Edge(
            invitation = venue.id + '/Reviewers/-/Proposed_Assignment',
            signatures = ['TestVenue.cc'],
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

        new_cdate = openreview.tools.datetime_millis(datetime.datetime.utcnow()) + 2000
        openreview_client.post_invitation_edit(
            invitations='TestVenue.cc/-/Edit',
            readers=['TestVenue.cc'],
            writers=['TestVenue.cc'],
            signatures=['TestVenue.cc'],
            invitation=openreview.api.Invitation(id='TestVenue.cc/-/Official_Review',
                signatures=['TestVenue.cc'],
                edit = {
                    'invitation': {
                        'cdate': new_cdate
                    }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, 'TestVenue.cc/-/Official_Review-0-0')
        helpers.await_queue_edit(openreview_client, 'TestVenue.cc/-/Official_Review-0-1', count=2)

        invitations = openreview_client.get_invitations(invitation='TestVenue.cc/-/Official_Review')
        assert len(invitations) == 3
        #assert invitation.cdate == new_cdate
        invitation = openreview_client.get_invitation('TestVenue.cc/Submission1/-/Official_Review')
        assert invitation.cdate == new_cdate
        assert invitation.edit['note']['readers'] == ["TestVenue.cc/Program_Chairs", "TestVenue.cc/Submission1/Area_Chairs", "${3/signatures}"]

        now = datetime.datetime.utcnow()
        venue.review_stage = openreview.stages.ReviewStage(start_date=now - datetime.timedelta(minutes = 4), due_date=now + datetime.timedelta(minutes = 40), release_to_authors=True)
        venue.create_review_stage()

        invitation = openreview_client.get_invitation('TestVenue.cc/-/Official_Review')
        assert invitation.edit['invitation']['edit']['note']['readers'] == ["TestVenue.cc/Program_Chairs", "TestVenue.cc/Submission${5/content/noteNumber/value}/Area_Chairs", "${3/signatures}", "TestVenue.cc/Submission${5/content/noteNumber/value}/Authors"]

        invitation = openreview_client.get_invitation('TestVenue.cc/Submission1/-/Official_Review')
        assert invitation.edit['note']['readers'] == ["TestVenue.cc/Program_Chairs", "TestVenue.cc/Submission1/Area_Chairs", "${3/signatures}", "TestVenue.cc/Submission1/Authors"]

        ## If I change the super invitation, let's propagate the changes to the children
        openreview_client.post_invitation_edit(
            invitations='TestVenue.cc/-/Edit',
            readers=['TestVenue.cc'],
            writers=['TestVenue.cc'],
            signatures=['TestVenue.cc'],
            invitation=openreview.api.Invitation(id='TestVenue.cc/-/Official_Review',
                signatures=['TestVenue.cc'],
                edit={
                    'invitation': {
                        'edit': {
                            'note': {
                                'content': {
                                    "private_comment_to_acs": {
                                        "order": 11,
                                        "description": "Leave a comment to the ACs.",
                                        "value": {
                                            "param": {
                                                "type": "string",
                                                "regex": ".{0,500}"
                                            }
                                        },
                                        "readers": ['TestVenue.cc', "TestVenue.cc/Submission${4/number}/Area_Chairs"]
                                    },
                                }
                            }
                        }
                    }
                }
            )
        )        

        helpers.await_queue_edit(openreview_client, 'TestVenue.cc/-/Official_Review-0-1', count=4)

        invitation = openreview_client.get_invitation('TestVenue.cc/Submission1/-/Official_Review')
        assert invitation.edit['note']['readers'] == ["TestVenue.cc/Program_Chairs", "TestVenue.cc/Submission1/Area_Chairs", "${3/signatures}", "TestVenue.cc/Submission1/Authors"]
        assert 'private_comment_to_acs' in invitation.edit['note']['content']

    def test_review_rebuttal_stage(self, venue, openreview_client, helpers):

        assert openreview_client.get_invitation('TestVenue.cc/-/Rebuttal')
        with pytest.raises(openreview.OpenReviewException, match=r'The Invitation TestVenue.cc/Submission1/-/Rebuttal was not found'):
            assert openreview_client.get_invitation('TestVenue.cc/Submission1/-/Rebuttal')

        openreview_client.post_invitation_edit(
            invitations='TestVenue.cc/-/Edit',
            readers=['TestVenue.cc'],
            writers=['TestVenue.cc'],
            signatures=['TestVenue.cc'],
            invitation=openreview.api.Invitation(id='TestVenue.cc/-/Rebuttal',
                signatures=['TestVenue.cc'],
                edit = {
                    'invitation': {
                        'cdate': openreview.tools.datetime_millis(datetime.datetime.utcnow()) + 2000
                    }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, 'TestVenue.cc/-/Rebuttal-0-0')

        assert openreview_client.get_invitation('TestVenue.cc/-/Rebuttal')
        assert openreview_client.get_invitation('TestVenue.cc/Submission1/-/Rebuttal')

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
                signatures=['TestVenue.cc'],
                edit = {
                    'invitation': {
                        'cdate': openreview.tools.datetime_millis(datetime.datetime.utcnow()) + 2000
                    }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, 'TestVenue.cc/-/Meta_Review-0-0')
        
        assert openreview_client.get_invitation('TestVenue.cc/-/Meta_Review')
        assert openreview_client.get_invitation('TestVenue.cc/Submission1/-/Meta_Review')

    def test_comment_stage(self, venue, openreview_client, helpers):

        #release papers to the public
        venue.submission_stage.readers = [SubmissionStage.Readers.EVERYONE]
        venue.create_submission_stage()

        submissions = venue.get_submissions()
        assert submissions and len(submissions) == 3
        assert submissions[0].readers == ['everyone']
        assert submissions[1].readers == ['everyone']
        assert submissions[2].readers == ['everyone']

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

    def test_withdraw_submission(self, venue, openreview_client, helpers):

        author_client = OpenReviewClient(username='celeste@maileleven.com', password=helpers.strong_password)

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
        assert note.invitations == ['TestVenue.cc/-/Submission', 'TestVenue.cc/-/Post_Submission', 'TestVenue.cc/-/Withdrawn_Submission']
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
        invitation =  openreview_client.get_invitation('TestVenue.cc/Submission2/-/Official_Comment')
        assert invitation.expdate and invitation.expdate < openreview.tools.datetime_millis(datetime.datetime.utcnow())        
        invitation =  openreview_client.get_invitation('TestVenue.cc/Submission2/-/Public_Comment')
        assert invitation.expdate and invitation.expdate < openreview.tools.datetime_millis(datetime.datetime.utcnow())        

        messages = openreview_client.get_messages(to='celeste@maileleven.com', subject='[TV 22]: Paper #2 withdrawn by paper authors')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == f'The TV 22 paper \"Paper 2 Title\" has been withdrawn by the paper authors.\n\nFor more information, click here https://openreview.net/forum?id={note.id}&noteId={withdraw_note["note"]["id"]}\n'

        assert openreview_client.get_invitation('TestVenue.cc/Submission2/-/Withdrawal_Reversion')

        authors_group = openreview_client.get_group('TestVenue.cc/Authors')
        assert 'TestVenue.cc/Submission2/Authors' not in authors_group.members

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

        invitation =  openreview_client.get_invitation('TestVenue.cc/Submission2/-/Official_Comment')
        assert invitation.expdate is None       

        invitation =  openreview_client.get_invitation('TestVenue.cc/Submission2/-/Public_Comment')
        assert invitation.expdate is None 

        note = author_client.get_note(withdraw_note['note']['forum'])
        assert note
        assert note.invitations == ['TestVenue.cc/-/Submission', 'TestVenue.cc/-/Post_Submission']
        assert note.content['venue']['value'] == 'TestVenue Submission'
        assert note.content['venueid']['value'] == 'TestVenue.cc/Submission'


        messages = openreview_client.get_messages(to='celeste@maileleven.com', subject='[TV 22]: Paper #2 restored by venue organizers')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == f'The TV 22 paper \"Paper 2 Title\" has been restored by the venue organizers.\n\nFor more information, click here https://openreview.net/forum?id={note.id}\n'

        authors_group = openreview_client.get_group('TestVenue.cc/Authors')
        assert 'TestVenue.cc/Submission2/Authors' in authors_group.members

    def test_desk_reject_submission(self, venue, openreview_client, helpers):

        pc_client = OpenReviewClient(username='venue_pc@mail.com', password=helpers.strong_password)

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
        assert note.invitations == ['TestVenue.cc/-/Submission', 'TestVenue.cc/-/Post_Submission', 'TestVenue.cc/-/Desk_Rejected_Submission']
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
        invitation =  openreview_client.get_invitation('TestVenue.cc/Submission2/-/Official_Comment')
        assert invitation.expdate and invitation.expdate < openreview.tools.datetime_millis(datetime.datetime.utcnow())
        invitation =  openreview_client.get_invitation('TestVenue.cc/Submission2/-/Public_Comment')
        assert invitation.expdate and invitation.expdate < openreview.tools.datetime_millis(datetime.datetime.utcnow())

        messages = openreview_client.get_messages(to='celeste@maileleven.com', subject='[TV 22]: Paper #2 desk-rejected by Program Chairs')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == f'The TV 22 paper \"Paper 2 Title\" has been desk-rejected by Program Chairs.\n\nFor more information, click here https://openreview.net/forum?id={note.id}\n'

        messages = openreview_client.get_messages(to='venue_pc@mail.com', subject='[TV 22]: Paper #2 desk-rejected by Program Chairs')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == f'The TV 22 paper \"Paper 2 Title\" has been desk-rejected by Program Chairs.\n\nFor more information, click here https://openreview.net/forum?id={note.id}\n'

        assert openreview_client.get_invitation('TestVenue.cc/Submission2/-/Desk_Rejection_Reversion')

        authors_group = openreview_client.get_group('TestVenue.cc/Authors')
        assert 'TestVenue.cc/Submission2/Authors' not in authors_group.members

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

        invitation =  openreview_client.get_invitation('TestVenue.cc/Submission2/-/Official_Comment')
        assert invitation.expdate is None 

        invitation =  openreview_client.get_invitation('TestVenue.cc/Submission2/-/Public_Comment')
        assert invitation.expdate is None 

        note = pc_client.get_note(desk_reject_note['note']['forum'])
        assert note
        assert note.invitations == ['TestVenue.cc/-/Submission', 'TestVenue.cc/-/Post_Submission']
        assert note.content['venue']['value'] == 'TestVenue Submission'
        assert note.content['venueid']['value'] == 'TestVenue.cc/Submission'

        messages = openreview_client.get_messages(to='celeste@maileleven.com', subject='[TV 22]: Paper #2 restored by venue organizers')
        assert len(messages) == 2
        assert messages[0]['content']['text'] == f'The TV 22 paper \"Paper 2 Title\" has been restored by the venue organizers.\n\nFor more information, click here https://openreview.net/forum?id={note.id}\n'

        messages = openreview_client.get_messages(to='venue_pc@mail.com', subject='[TV 22]: Paper #2 restored by venue organizers')
        assert len(messages) == 2
        assert messages[1]['content']['text'] == f'The desk-rejected TV 22 paper \"Paper 2 Title\" has been restored by the venue organizers.\n\nFor more information, click here https://openreview.net/forum?id={note.id}\n'

        authors_group = openreview_client.get_group('TestVenue.cc/Authors')
        assert 'TestVenue.cc/Submission2/Authors' in authors_group.members

    def test_decision_stage(self, venue, openreview_client, helpers):

        submissions = venue.get_submissions(sort='number:asc')
        assert submissions and len(submissions) == 3

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

    def test_submission_revision_stage(self, venue, client, openreview_client, helpers):

        submissions = openreview_client.get_notes(invitation='TestVenue.cc/-/Submission', sort='number:asc')

        assert openreview_client.get_invitation('TestVenue.cc/-/Camera_Ready_Revision')
        with pytest.raises(openreview.OpenReviewException, match=r'The Invitation TestVenue.cc/Submission1/-/Camera_Ready_Revision was not found'):
            assert openreview_client.get_invitation('TestVenue.cc/Submission1/-/Camera_Ready_Revision')

        openreview_client.post_invitation_edit(
            invitations='TestVenue.cc/-/Edit',
            readers=['TestVenue.cc'],
            writers=['TestVenue.cc'],
            signatures=['TestVenue.cc'],
            invitation=openreview.api.Invitation(id='TestVenue.cc/-/Camera_Ready_Revision',
                signatures=['TestVenue.cc'],
                edit = {
                    'invitation': {
                        'cdate': openreview.tools.datetime_millis(datetime.datetime.utcnow()) + 2000
                    }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, 'TestVenue.cc/-/Camera_Ready_Revision-0-0')

        assert openreview_client.get_invitation('TestVenue.cc/-/Camera_Ready_Revision')
        assert openreview.tools.get_invitation(openreview_client, 'TestVenue.cc/Submission1/-/Camera_Ready_Revision')
        assert not openreview.tools.get_invitation(openreview_client, 'TestVenue.cc/Submission2/-/Camera_Ready_Revision')

        author_client = OpenReviewClient(username='celeste@maileleven.com', password=helpers.strong_password)
        # post revision for a submission without abstract
        updated_submission = author_client.post_note_edit(invitation='TestVenue.cc/Submission1/-/Camera_Ready_Revision',
            signatures=['TestVenue.cc/Submission1/Authors'],
            note=Note(
                content={
                    'title': { 'value': 'Paper 1 Title REVISED AGAIN' },
                    'authors': { 'value': ['Celeste MartinezEleven']},
                    'authorids': { 'value': ['~Celeste_MartinezEleven1']},
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                    'keywords': {'value': ['aa'] }
                }
            ))
        helpers.await_queue_edit(openreview_client, edit_id=updated_submission['id'])

        updated_note = author_client.get_note(id=submissions[0].forum)

        messages = client.get_messages(to = 'celeste@maileleven.com', subject='TV 22 has received a new revision of your submission titled Paper 1 Title REVISED AGAIN')
        assert messages and len(messages) == 1

        message_text = f'''Your new revision of the submission to TV 22 has been posted.

Title: Paper 1 Title REVISED AGAIN

To view your submission, click here: https://openreview.net/forum?id={updated_note.id}'''
        assert message_text in messages[0]['content']['text']

    def test_custom_stage(self, venue, openreview_client, helpers):

        submissions = venue.get_submissions(sort='number:asc')
        assert submissions and len(submissions) == 3

        assert openreview_client.get_invitation('TestVenue.cc/-/Camera_Ready_Verification')
        with pytest.raises(openreview.OpenReviewException, match=r'The Invitation TestVenue.cc/Submission1/-/Camera_Ready_Verification was not found'):
            assert openreview_client.get_invitation('TestVenue.cc/Submission1/-/Camera_Ready_Verification')

        openreview_client.post_invitation_edit(
            invitations='TestVenue.cc/-/Edit',
            readers=['TestVenue.cc'],
            writers=['TestVenue.cc'],
            signatures=['TestVenue.cc'],
            invitation=openreview.api.Invitation(id='TestVenue.cc/-/Camera_Ready_Verification',
                signatures=['TestVenue.cc'],
                edit = {
                    'invitation': {
                        'cdate': openreview.tools.datetime_millis(datetime.datetime.utcnow()) + 2000
                    }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, 'TestVenue.cc/-/Camera_Ready_Verification-0-0')

        assert openreview_client.get_invitation('TestVenue.cc/-/Camera_Ready_Verification')
        invitation = openreview.tools.get_invitation(openreview_client, 'TestVenue.cc/Submission1/-/Camera_Ready_Verification')
        assert invitation
        assert invitation.invitees == ['TestVenue.cc/Program_Chairs']
        assert invitation.edit['note']['readers'] == [
            'TestVenue.cc/Program_Chairs',
            'TestVenue.cc/Submission1/Area_Chairs',
            'TestVenue.cc/Submission1/Authors'
        ]
        assert 'verification' in invitation.edit['note']['content']
        assert invitation.edit['note']['forum'] == submissions[0].id
        assert invitation.edit['note']['replyto'] == submissions[0].id
        assert not openreview.tools.get_invitation(openreview_client, 'TestVenue.cc/Submission2/-/Camera_Ready_Verification')

        pc_client = OpenReviewClient(username='venue_pc@mail.com', password=helpers.strong_password)

        verification = pc_client.post_note_edit(invitation='TestVenue.cc/Submission1/-/Camera_Ready_Verification',
            signatures=['TestVenue.cc/Program_Chairs'],
            note=Note(
                content={
                    'verification': { 'value': 'I confirm that camera ready manuscript complies with the TV 22 stylefile and, if appropriate, includes the minor revisions that were requested.' },
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=verification['id'])

        verification_note = openreview_client.get_notes(invitation='TestVenue.cc/Submission1/-/Camera_Ready_Verification')[0]

        messages = openreview_client.get_messages(subject='[TV 22] A camera ready verification has been received on your Paper Number: 1, Paper Title: "Paper 1 Title REVISED AGAIN"')
        assert len(messages) == 1
        assert 'celeste@maileleven.com' in messages[0]['content']['to']
        assert messages[0]['content']['text'] == f'''The camera ready verification for submission number {str(submissions[0].number)} has been posted.
Please follow this link: https://openreview.net/forum?id={submissions[0].id}&noteId={verification_note.id}'''

        messages = openreview_client.get_messages(subject='[TV 22] Your camera ready verification has been received on Paper Number: 1, Paper Title: "Paper 1 Title REVISED AGAIN"')
        assert len(messages) == 1
        assert 'venue_pc@mail.com' in messages[0]['content']['to']
        assert messages[0]['content']['text'] == f'''The camera ready verification for submission number {str(submissions[0].number)} has been posted.
Please follow this link: https://openreview.net/forum?id={submissions[0].id}&noteId={verification_note.id}'''