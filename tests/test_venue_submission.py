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

from openreview.venue import Venue

class TestVenueSubmission():

    def test_setup(self, openreview_client, selenium, request_page, helpers):
        conference_id = 'TestVenue.cc'

        # venue_group = Group(id = conference_id,
        #     readers = ['everyone'],
        #     writers = [conference_id],
        #     signatures = ['~Super_User1'],
        #     signatories = [conference_id],
        #     members = [],
        #     host = conference_id
        # )

        # with open(os.path.join(os.path.dirname(__file__), '../openreview/journal/webfield/homepage.js')) as f:
        #     content = f.read()
        #     content = content.replace("var VENUE_ID = '';", "var VENUE_ID = '" + conference_id + "';")
        #     content = content.replace("var SUBMISSION_ID = '';", "var SUBMISSION_ID = '" + conference_id + "/-/Submission';")
        #     content = content.replace("var SUBMITTED_ID = '';", "var SUBMITTED_ID = '" + conference_id + "/Submitted';")
        #     content = content.replace("var UNDER_REVIEW_ID = '';", "var UNDER_REVIEW_ID = '" + conference_id + "/Under_Review';")
        #     content = content.replace("var DESK_REJECTED_ID = '';", "var DESK_REJECTED_ID = '" + conference_id + "/Desk_Rejection';")
        #     content = content.replace("var WITHDRAWN_ID = '';", "var WITHDRAWN_ID = '" + conference_id + "/Withdrawn_Submission';")
        #     content = content.replace("var REJECTED_ID = '';", "var REJECTED_ID = '" + conference_id + "/Rejection';")
        #     venue_group.web = content
        #     openreview_client.post_group(venue_group)

        # assert venue_group

        # meta_inv = openreview_client.post_invitation_edit(invitations = None, 
        #     readers = [conference_id],
        #     writers = [conference_id],
        #     signatures = [conference_id],
        #     invitation = Invitation(id = f'{conference_id}/-/Edit',
        #         invitees = [conference_id],
        #         readers = [conference_id],
        #         signatures = [conference_id],
        #         edit = True
        #     ))

        # assert meta_inv

        venue = Venue(openreview_client, conference_id)
        venue.setup()

        assert openreview_client.get_group('TestVenue.cc')
        assert openreview_client.get_group('TestVenue.cc/Authors')

        venue.set_submission_stage(openreview.builder.SubmissionStage(double_blind=True, readers=[openreview.builder.SubmissionStage.Readers.REVIEWERS_ASSIGNED]))

        assert openreview_client.get_invitation('TestVenue.cc/-/Submission')

        # submission_invitation = Invitation(
        #     id=f'{conference_id}/-/Submission',
        #     invitees = ['~'],
        #     signatures = [conference_id],
        #     readers = ['everyone'],
        #     writers = [conference_id],
        #     edit = {
        #         'signatures': { 'param': { 'regex': '~.*' } },
        #         # 'readers': [conference_id, '${2/signatures}', conference_id + '/Paper${2/note/number}/Authors'],
        #         'readers': [conference_id, conference_id + '/Paper${2/note/number}/Action_Editors', conference_id + '/Paper${2/note/number}/Authors'],
        #         'writers': [conference_id],
        #         'note': {
        #             'signatures': [ conference_id + '/Paper${2/number}/Authors' ],
        #             # 'readers': [conference_id, '${3/signatures}', conference_id + '/Paper${2/number}/Authors'],
        #             # 'writers': [conference_id, '${3/signatures}', conference_id + '/Paper${2/number}/Authors'],
        #             'readers': [conference_id, conference_id + '/Paper${2/number}/Action_Editors', conference_id + '/Paper${2/number}/Authors'],
        #             # 'readers': {
        #             #     'param': {
        #             #         'enum': ['everyone', conference_id + '/Editors_In_Chief', conference_id + '/Paper${2/number}/Action_Editors', conference_id + '/Paper${2/number}/Authors']
        #             #     }
        #             # },
        #             'writers': [conference_id, conference_id + '/Paper${2/number}/Action_Editors', conference_id + '/Paper${2/number}/Authors'],
        #             'content': {
        #                 'title': {
        #                     'order': 1,
        #                     'type': 'string',
        #                     'description': 'Title of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$.',
        #                     'value': { 
        #                         'param': { 
        #                             'regex': '^.{1,250}$'
        #                         }
        #                     }
        #                 },
        #                 'authors': {
        #                     'order': 2,
        #                     'type': 'string[]',
        #                     'value': {
        #                         'param': {
        #                             'regex': '[^;,\\n]+(,[^,\\n]+)*',
        #                             'hidden': True
        #                         }
        #                     },
        #                     'readers': [conference_id, conference_id + '/Paper${4/number}/Action_Editors', conference_id + '/Paper${4/number}/Authors']
        #                 },
        #                 'authorids': {
        #                     'order': 3,
        #                     'type': 'group[]',
        #                     'description': 'Search author profile by first, middle and last name or email address. All authors must have an OpenReview profile.',
        #                     'value': {
        #                         'param': {
        #                             'regex': '~.*'
        #                         }
        #                     },
        #                     'readers': [conference_id, conference_id + '/Paper${4/number}/Action_Editors', conference_id + '/Paper${4/number}/Authors']
        #                 },
        #                 'abstract': {
        #                     'order': 4,
        #                     'type': 'string',
        #                     'description': 'Abstract of paper. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$.',
        #                     'value': {
        #                         'param': {
        #                             'regex': '^[\\S\\s]{1,5000}$',
        #                             'markdown': True
        #                         }
        #                     }
        #                 },
        #                 'pdf': {
        #                     'order': 5,
        #                     'type': 'file',
        #                     'description': 'Upload a PDF file that ends with .pdf.',
        #                     'value': {
        #                         'param': {
        #                             'maxSize': 50,
        #                             'extensions': ['pdf']
        #                         }
        #                     }
        #                 },
        #                 "previous_submission_url": {
        #                     'order': 6,
        #                     'type': 'string',
        #                     'description': 'If a version of this submission was previously rejected, give the OpenReview link to the original submission (which must still be anonymous) and describe the changes below.',
        #                     'value':{
        #                         'param': {
        #                             'regex': 'https:\\/\\/openreview\\.net\\/forum\\?id=.*',
        #                             'optional': True
        #                         }
        #                     }
        #                 },
        #                 'changes_since_last_submission': {
        #                     'order': 7,
        #                     'type': 'string',
        #                     'description': 'Describe changes since last submission. Add TeX formulas using the following formats: $In-line Formula$ or $$Block Formula$$.',
        #                     'value': {
        #                         'param': {
        #                             'regex': '^[\\S\\s]{1,5000}$',
        #                             'optional': True,
        #                             'markdown': True
        #                         }
        #                     }
        #                 },
        #                 "submission_length": {
        #                     'order': 8,
        #                     'type': 'string',
        #                     'description': 'Check if this is a regular length submission, i.e. the main content (all pages before references and appendices) is 12 pages or less. Note that the review process may take significantly longer for papers longer than 12 pages.',
        #                     'value': {
        #                         'param': {
        #                             'enum': [
        #                                 'Regular submission (no more than 12 pages of main content)',
        #                                 'Long submission (more than 12 pages of main content)'
        #                             ],
        #                             'input': 'radio'
        #                         }
        #                     }
        #                 }
        #             }
        #         }
        #     }
        # )

        # submission_invitation = openreview_client.post_invitation_edit(
        #     invitations = f'{conference_id}/-/Edit',
        #     readers = [conference_id],
        #     writers = [conference_id],
        #     signatures = [conference_id],
        #     invitation = submission_invitation)

        # assert submission_invitation

        helpers.create_user('celeste@mailnine.com', 'Celeste', 'Martinez')
        author_client = OpenReviewClient(username='celeste@mailnine.com', password='1234')

        submission_note_1 = author_client.post_note_edit(
            invitation=f'{conference_id}/-/Submission',
            signatures= ['~Celeste_Martinez1'],
            note=Note(
                #readers = [conference_id, 'TestVenue.cc/Paper1/Action_Editors', 'TestVenue.cc/Paper1/Authors'],
                content={
                    'title': { 'value': 'Paper 1 Title' },
                    'abstract': { 'value': 'Paper abstract' },
                    'authors': { 'value': ['Celeste Martinez']},
                    'authorids': { 'value': ['~Celeste_Martinez1']},
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                    'submission_length': {'value': 'Regular submission (no more than 12 pages of main content)' }
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=submission_note_1['id']) 

        submission = openreview_client.get_note(submission_note_1['note']['id'])
        assert len(submission.readers) == 2
        assert 'TestVenue.cc' in submission.readers
        assert 'TestVenue.cc/Paper1/Authors' in submission.readers
                
        venue.setup_post_submission_stage()
        assert openreview_client.get_group('TestVenue.cc/Paper1/Authors')
        assert openreview_client.get_group('TestVenue.cc/Paper1/Reviewers')
        assert openreview_client.get_group('TestVenue.cc/Paper1/Action_Editors')

        submission = openreview_client.get_note(submission.id)
        assert len(submission.readers) == 3
        assert 'TestVenue.cc' in submission.readers
        assert 'TestVenue.cc/Paper1/Authors' in submission.readers        
        assert 'TestVenue.cc/Paper1/Reviewers' in submission.readers        

        # editors_in_chief_id = f'{conference_id}/Editors_In_Chief'
        # action_editors_id = f'{conference_id}/Paper1/Action_Editors'
        # reviewers_id = f'{conference_id}/Paper1/Reviewers'
        # authors_id = f'{conference_id}/Paper1/Authors'

        # paper_group=openreview_client.post_group(Group(id=f'{conference_id}/Paper1',
        #         readers=[conference_id],
        #         writers=[conference_id],
        #         signatures=[conference_id],
        #         signatories=[conference_id]
        #     ))

        # authors_group=openreview_client.post_group(Group(id=authors_id,
        #     readers=[conference_id, authors_id],
        #     writers=[conference_id],
        #     signatures=[conference_id],
        #     signatories=[conference_id, authors_id],
        #     members=submission_note_1['note']['content']['authorids']['value'] ## always update authors
        # ))

        # action_editors_group=openreview_client.post_group(Group(id=action_editors_id,
        #         readers=['everyone'],
        #         nonreaders=[authors_id],
        #         writers=[conference_id],
        #         signatures=[conference_id],
        #         signatories=[conference_id, action_editors_id],
        #         members=[]
        #     ))

        # reviewers_group=openreview_client.post_group(Group(id=reviewers_id,
        #         readers=[conference_id, action_editors_id, reviewers_id],
        #         deanonymizers=[conference_id, action_editors_id],
        #         nonreaders=[authors_id],
        #         writers=[conference_id, action_editors_id],
        #         signatures=[conference_id],
        #         signatories=[conference_id],
        #         members=[],
        #         anonids=True
        #     ))

        # comment_invitation_id=f'{conference_id}/Paper1/-/Official_Comment'
        # comment_invitation = Invitation(id=comment_invitation_id,
        #     invitees=[conference_id, action_editors_id, reviewers_id, authors_id],
        #     readers=['everyone'],
        #     writers=[conference_id],
        #     signatures=[conference_id],
        #     edit = {
        #         'signatures': {'param': { 'regex': f'{editors_in_chief_id}|{action_editors_id}|{reviewers_id}.*|{authors_id}' }},
        #         'readers': {},
        #         'writers': {},
        #         'note': {
        #             'id': {
        #                 'withInvitation': comment_invitation_id,
        #                 'optional': True
        #             },
        #             'forum': {
        #                 'param':
        #             }
        #         }
        #     } )
        now = datetime.datetime.utcnow()
        venue.review_stage = openreview.ReviewStage(due_date=now + datetime.timedelta(minutes = 40))
        venue.create_review_stage()

        assert openreview_client.get_invitation('TestVenue.cc/-/Official_Review')

        ## Create Paper 1 review invitation
        openreview_client.post_invitation_edit(invitations='TestVenue.cc/-/Official_Review',
            readers=['TestVenue.cc'],
            writers=['TestVenue.cc'],
            signatures=['TestVenue.cc'],
            content={
                'noteId': {
                    'value': submission.id
                },
                'noteNumber': {
                    'value': submission.number
                },
                'duedate': {
                    'value': openreview.tools.datetime_millis(now)
                }
            },
            invitation=Invitation()
        )

        assert openreview_client.get_invitation('TestVenue.cc/Paper1/-/Official_Review')

        #recruit reviewers to create /Reviewers group
        message = 'Dear {{fullname}},\n\nYou have been nominated by the program chair committee of Test 2030 Venue V2 to serve as {{invitee_role}}.\n\nTo respond to the invitation, please click on the following link:\n\n{{invitation_url}}\n\nCheers!\n\nProgram Chairs'
        
        helpers.create_user('reviewer_venue_one@mail.com', 'Reviewer Venue', 'One')
        reviewer_client = OpenReviewClient(username='reviewer_venue_one@mail.com', password='1234')

        venue.recruit_reviewers(title='[TV 22] Invitation to serve as Reviewer',
            message=message,
            invitees = ['~Reviewer_Venue_One1'],
            contact_info='testvenue@contact.com')

        messages = openreview_client.get_messages(to='reviewer_venue_one@mail.com')
        invitation_url = re.search('href="https://.*">', messages[0]['content']['text']).group(0)[6:-1].replace('https://openreview.net', 'http://localhost:3030').replace('&amp;', '&')[:-1]
        print('invitation_url', invitation_url)
        helpers.respond_invitation(selenium, request_page, invitation_url, accept=True)

        reviewer_group = openreview_client.get_group('TestVenue.cc/Reviewers')
        assert reviewer_group
        assert '~Reviewer_Venue_One1' in reviewer_group.members
        
        #bid stage
        venue.area_chairs_name = 'Action_Editors'
        venue.has_area_chairs(True)
        bid_stage = openreview.BidStage(committee_id=venue.get_reviewers_id())
        venue.set_bid_stage(bid_stage)

        assert openreview_client.get_invitation('TestVenue.cc/Reviewers/-/Bid')