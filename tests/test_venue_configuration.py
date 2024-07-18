import pytest
import datetime
import openreview
from openreview.api import Note
from openreview.api import OpenReviewClient
from openreview.venue.configuration import VenueConfiguration

class TestVenueConfiguration():

    def test_venue_configuration_setup(self, openreview_client, helpers):
        super_id = 'openreview.net'
        support_group_id = super_id + '/Support'

        helpers.create_user('sherry@iclr.cc', 'ProgramChair', 'ICLR')
        pc_client_v2=openreview.api.OpenReviewClient(username='sherry@iclr.cc', password=helpers.strong_password)

        assert openreview_client.get_invitation('openreview.net/-/Edit')
        assert openreview_client.get_invitation('openreview.net/-/Venue_Configuration_Request')
        assert openreview_client.get_invitation('openreview.net/-/Comment')
        assert openreview_client.get_invitation('openreview.net/-/Deploy')

        now = datetime.datetime.utcnow()
        start_date = now + datetime.timedelta(minutes=30)
        due_date = now + datetime.timedelta(days=1)

        # post a conference request form
        conference_request = openreview_client.post_note_edit(invitation='openreview.net/-/Venue_Configuration_Request',
            signatures=['~Super_User1'],
            note=openreview.api.Note(
                content={
                    'official_venue_name': { 'value': 'The Thirteenth International Conference on Learning Representations' },
                    'abbreviated_venue_name': { 'value': 'ICLR 2025' },
                    'venue_website_url': { 'value': 'https://iclr.cc/Conferences/2025' },
                    'location': { 'value': 'Vienna, Austria' },
                    'venue_start_date': { 'value': now.strftime('%Y/%m/%d') },
                    'program_chair_emails': { 'value': ['sherry@iclr.cc'] },
                    'contact_email': { 'value': 'iclr2024.programchairs@gmail.com' },
                    'publication_chairs': { 'value': 'No, our venue does not have Publication Chairs' },
                    'area_chairs_and_senior_area_chairs': { 'value': 'Yes, our venue has Area Chairs and Senior Area Chairs' },
                    'ethics_chairs_and_reviewers': { 'value': 'No, our venue does not have Ethics Chairs and Reviewers' },
                    'secondary_area_chairs': { 'value': 'No, our venue does not have Secondary Area Chairs' },
                    'submission_start_date': { 'value': start_date.strftime('%Y/%m/%d %H:%M') },
                    'submission_deadline': { 'value': due_date.strftime('%Y/%m/%d %H:%M') },
                    'author_and_reviewer_anonymity': { 'value': 'Double-blind' },
                    #'force_profiles_only': { 'value': 'No, allow submissions with email addresses' },
                    #'submission_readers': { 'value': 'All program committee (all reviewers, all area chairs, all senior area chairs if applicable)' },
                    'submission_license': { 'value': ['CC BY-NC 4.0'] },
                    #'email_pcs_for_new_submissions': { 'value': 'No, do not email PCs.' }
                }
            ))
        
        assert conference_request
        helpers.await_queue_edit(openreview_client, invitation='openreview.net/-/Venue_Configuration_Request')

        request = openreview_client.get_note(conference_request['note']['id'])
        assert openreview_client.get_invitation(f'openreview.net/Venue_Configuration_Request{request.number}/-/Comment')
        assert openreview_client.get_invitation(f'openreview.net/Venue_Configuration_Request{request.number}/-/Deploy')

        openreview_client.post_note_edit(invitation=f'openreview.net/Venue_Configuration_Request{request.number}/-/Deploy',
            signatures=[support_group_id],
            note=openreview.api.Note(
                id=request.id,
                content={
                    'venue_id': { 'value': 'ICLR.cc/2025/Conference' }
                }
            ))
        
        helpers.await_queue_edit(openreview_client, invitation='openreview.net/Venue_Configuration_Request1/-/Deploy')
        
        assert openreview.tools.get_group(openreview_client, 'ICLR.cc/2025/Conference')
        assert openreview.tools.get_group(openreview_client, 'ICLR.cc/2025')
        submission_inv = openreview.tools.get_invitation(openreview_client, 'ICLR.cc/2025/Conference/-/Submission')
        assert submission_inv and submission_inv.cdate == openreview.tools.datetime_millis(start_date.replace(second=0, microsecond=0))
        assert submission_inv.duedate == openreview.tools.datetime_millis(due_date.replace(second=0, microsecond=0))
        assert submission_inv.expdate == submission_inv.duedate + (30*60*1000)
        submission_deadline_inv =  openreview.tools.get_invitation(openreview_client, 'ICLR.cc/2025/Conference/-/Submission/Deadlines')
        assert submission_deadline_inv and submission_inv.id in submission_deadline_inv.edit['invitation']['id']
        post_submission_inv = openreview.tools.get_invitation(openreview_client, 'ICLR.cc/2025/Conference/-/Post_Submission')
        assert post_submission_inv and post_submission_inv.cdate == submission_inv.expdate

        assert openreview.tools.get_group(openreview_client, 'ICLR.cc/2025/Conference/Reviewers')
        assert openreview_client.get_invitation('ICLR.cc/2025/Conference/Reviewers/-/Expertise_Selection')
        assert openreview_client.get_invitation('ICLR.cc/2025/Conference/Reviewers/-/Matching_Setup')
        assert openreview.tools.get_group(openreview_client, 'ICLR.cc/2025/Conference/Area_Chairs')
        assert openreview_client.get_invitation('ICLR.cc/2025/Conference/Area_Chairs/-/Expertise_Selection')
        assert openreview_client.get_invitation('ICLR.cc/2025/Conference/Area_Chairs/-/Matching_Setup')
        assert openreview.tools.get_group(openreview_client, 'ICLR.cc/2025/Conference/Senior_Area_Chairs')
        assert openreview_client.get_invitation('ICLR.cc/2025/Conference/Senior_Area_Chairs/-/Expertise_Selection')
        assert openreview_client.get_invitation('ICLR.cc/2025/Conference/Senior_Area_Chairs/-/Matching_Setup')

        now = datetime.datetime.utcnow()
        new_cdate = openreview.tools.datetime_millis(now - datetime.timedelta(days=3))
        new_duedate = openreview.tools.datetime_millis(now + datetime.timedelta(days=3))

        withdrawal = openreview_client.get_invitation('ICLR.cc/2025/Conference/-/Withdrawal')
        assert withdrawal and 'expdate' not in withdrawal.edit['invitation']
        assert openreview_client.get_invitation('ICLR.cc/2025/Conference/-/Withdrawal/Deadlines')
        assert openreview_client.get_invitation('ICLR.cc/2025/Conference/-/Withdrawn_Submission/Readers')
        assert openreview_client.get_invitation('ICLR.cc/2025/Conference/-/Withdrawn_Submission/Notifications')
        assert openreview_client.get_invitation('ICLR.cc/2025/Conference/-/Desk_Rejected_Submission/Readers')
        assert openreview_client.get_invitation('ICLR.cc/2025/Conference/-/Desk_Rejected_Submission/Notifications')

        # set withdrawal expdate
        pc_client_v2.post_invitation_edit(
            invitations='ICLR.cc/2025/Conference/-/Withdrawal/Deadlines',
            content={
                'activation_date': { 'value': withdrawal.edit['invitation']['cdate'] },
                'expiration_date': { 'value': new_duedate }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id='ICLR.cc/2025/Conference/-/Withdrawal-0-1', count=2)

        withdrawal_inv = openreview.tools.get_invitation(openreview_client, 'ICLR.cc/2025/Conference/-/Withdrawal')
        assert withdrawal_inv.edit['invitation']['expdate'] == new_duedate

        # extend Submission duedate with Submission/Deadline invitation
        pc_client_v2.post_invitation_edit(
            invitations=submission_deadline_inv.id,
            content={
                'activation_date': { 'value': new_cdate },
                'deadline': { 'value': new_duedate }
            }
        )
        helpers.await_queue_edit(openreview_client, invitation='ICLR.cc/2025/Conference/-/Submission/Deadlines')
        helpers.await_queue_edit(openreview_client, edit_id='ICLR.cc/2025/Conference/-/Post_Submission-0-1', count=2)

        # assert submission deadline and expdate get updated
        submission_inv = openreview.tools.get_invitation(openreview_client, 'ICLR.cc/2025/Conference/-/Submission')
        assert submission_inv and submission_inv.cdate == new_cdate
        assert submission_inv.duedate == new_duedate
        assert submission_inv.expdate == new_duedate + 1800000
        post_submission_inv = openreview.tools.get_invitation(openreview_client, 'ICLR.cc/2025/Conference/-/Post_Submission')
        assert post_submission_inv and post_submission_inv.cdate == submission_inv.expdate

        matching_setup_inv = openreview.tools.get_invitation(openreview_client, 'ICLR.cc/2025/Conference/Reviewers/-/Matching_Setup')
        assert matching_setup_inv and matching_setup_inv.cdate == submission_inv.expdate

        matching_setup_inv = openreview.tools.get_invitation(openreview_client, 'ICLR.cc/2025/Conference/Area_Chairs/-/Matching_Setup')
        assert matching_setup_inv and matching_setup_inv.cdate == submission_inv.expdate

        matching_setup_inv = openreview.tools.get_invitation(openreview_client, 'ICLR.cc/2025/Conference/Senior_Area_Chairs/-/Matching_Setup')
        assert matching_setup_inv and matching_setup_inv.cdate == submission_inv.expdate

        content_inv = openreview.tools.get_invitation(openreview_client, 'ICLR.cc/2025/Conference/-/Submission/Form_Fields')
        assert content_inv
        assert 'subject_area' not in submission_inv.edit['note']['content']
        assert 'keywords' in submission_inv.edit['note']['content']
        assert submission_inv.edit['note']['license'] == 'CC BY 4.0'

        ## edit Submission content with Submission/Form_Fields invitation
        pc_client_v2.post_invitation_edit(
            invitations=content_inv.id,
            content = {
                'note_content': {
                    'value': {
                        'subject_area': {
                            'order': 10,
                            "description": "Select one subject area.",
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'enum': [
                                        "3D from multi-view and sensors",
                                        "3D from single images",
                                        "Adversarial attack and defense",
                                        "Autonomous driving",
                                        "Biometrics",
                                        "Computational imaging",
                                        "Computer vision for social good",
                                        "Computer vision theory",
                                        "Datasets and evaluation"
                                    ],
                                    "input": "select"
                                }
                            }
                        },
                        'keywords': {
                            'delete': True
                        }
                    }
                },
                'note_license': {
                    'value':  [
                        {'value': 'CC BY-NC-ND 4.0', 'optional': True, 'description': 'CC BY-NC-ND 4.0'},
                        {'value': 'CC BY-NC-SA 4.0', 'optional': True, 'description': 'CC BY-NC-SA 4.0'}
                    ]
                }
            }
        )

        submission_inv = openreview.tools.get_invitation(openreview_client, 'ICLR.cc/2025/Conference/-/Submission')
        assert submission_inv and 'subject_area' in submission_inv.edit['note']['content']
        assert 'keywords' not in submission_inv.edit['note']['content']
        content_keys = submission_inv.edit['note']['content'].keys()
        assert all(field in content_keys for field in ['title', 'authors', 'authorids', 'TLDR', 'abstract', 'pdf'])
        assert submission_inv.edit['note']['license']['param']['enum'] == [
            {
            "value": "CC BY-NC-ND 4.0",
            "optional": True,
            "description": "CC BY-NC-ND 4.0"
          },
          {
            "value": "CC BY-NC-SA 4.0",
            "optional": True,
            "description": "CC BY-NC-SA 4.0"
          }
        ]

        notifications_inv = openreview.tools.get_invitation(openreview_client, 'ICLR.cc/2025/Conference/-/Submission/Notifications')
        assert notifications_inv
        assert 'email_authors' in submission_inv.content and submission_inv.content['email_authors']['value']
        assert 'email_pcs' in submission_inv.content and not submission_inv.content['email_pcs']['value']

        ## edit Submission invitation content with Submission/Notifications invitation
        pc_client_v2.post_invitation_edit(
            invitations=notifications_inv.id,
            content = {
                'email_authors': { 'value': False },
                'email_pcs': { 'value': True }
            }
        )

        submission_inv = openreview.tools.get_invitation(openreview_client, 'ICLR.cc/2025/Conference/-/Submission')
        assert 'email_authors' in submission_inv.content and not submission_inv.content['email_authors']['value']
        assert 'email_pcs' in submission_inv.content and submission_inv.content['email_pcs']['value']

    def test_post_submissions(self, openreview_client, test_client, helpers):

        test_client = openreview.api.OpenReviewClient(token=test_client.token)

        domains = ['umass.edu', 'amazon.com', 'fb.com', 'cs.umass.edu', 'google.com', 'mit.edu', 'deepmind.com', 'co.ux', 'apple.com', 'nvidia.com']
        for i in range(1,11):
            note = openreview.api.Note(
                license = 'CC BY-NC-SA 4.0',
                content = {
                    'title': { 'value': 'Paper title ' + str(i) },
                    'abstract': { 'value': 'This is an abstract ' + str(i) },
                    'authorids': { 'value': ['~SomeFirstName_User1', 'peter@mail.com', 'andrew@' + domains[i % 10]] },
                    'authors': { 'value': ['SomeFirstName User', 'Peter SomeLastName', 'Andrew Mc'] },
                    'subject_area': { 'value': '3D from multi-view and sensors' },
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                }
            )

            test_client.post_note_edit(invitation='ICLR.cc/2025/Conference/-/Submission',
                signatures=['~SomeFirstName_User1'],
                note=note)

        helpers.await_queue_edit(openreview_client, invitation='ICLR.cc/2025/Conference/-/Submission', count=10)

        submissions = openreview_client.get_notes(invitation='ICLR.cc/2025/Conference/-/Submission')
        assert len(submissions) == 10
        assert submissions[0].readers == ['ICLR.cc/2025/Conference', '~SomeFirstName_User1', 'peter@mail.com', 'andrew@umass.edu']

        ## Setup submissions readers after the deadline
        pc_client = openreview.api.OpenReviewClient(username='sherry@iclr.cc', password=helpers.strong_password)

        submission_readers_inv = openreview.tools.get_invitation(openreview_client, 'ICLR.cc/2025/Conference/-/Post_Submission/Submission_Readers')
        assert submission_readers_inv

        pc_client.post_invitation_edit(
            invitations=submission_readers_inv.id,
            content = {
               'readers': { 'value': ['ICLR.cc/2025/Conference', 'ICLR.cc/2025/Conference/Submission${{2/id}/number}/Authors'] }
            }
        )

        submission_field_readers_inv = openreview.tools.get_invitation(openreview_client, 'ICLR.cc/2025/Conference/-/Post_Submission/Restrict_Field_Visibility')
        assert submission_field_readers_inv

        pc_client.post_invitation_edit(
            invitations=submission_field_readers_inv.id,
            content = {
                'author_readers': { 'value': ['ICLR.cc/2025/Conference', 'ICLR.cc/2025/Conference/Submission${{4/id}/number}/Authors'] },
                'pdf_readers': { 'value': ['ICLR.cc/2025/Conference', 'ICLR.cc/2025/Conference/Submission${{4/id}/number}/Authors', 'ICLR.cc/2025/Conference/Submission${{4/id}/number}/Reviewers'] },
            }
        )        

        now = datetime.datetime.utcnow()
        new_cdate = openreview.tools.datetime_millis(now - datetime.timedelta(days=1))
        new_duedate = openreview.tools.datetime_millis(now - datetime.timedelta(minutes=28))

        pc_client.post_invitation_edit(
            invitations='ICLR.cc/2025/Conference/-/Submission/Deadlines',
            content={
                'activation_date': { 'value': new_cdate },
                'deadline': { 'value': new_duedate },
                #'expiration_date': { 'value': new_duedate }
            }
        )
        helpers.await_queue_edit(openreview_client, invitation='ICLR.cc/2025/Conference/-/Submission/Deadlines')
        helpers.await_queue_edit(openreview_client, edit_id='ICLR.cc/2025/Conference/-/Post_Submission-0-0', count=1)

        submissions = openreview_client.get_notes(invitation='ICLR.cc/2025/Conference/-/Submission', sort='number:asc')
        assert len(submissions) == 10
        assert submissions[0].readers == ['ICLR.cc/2025/Conference', 'ICLR.cc/2025/Conference/Submission1/Authors']
        assert submissions[0].content['authors']['readers'] == ['ICLR.cc/2025/Conference', 'ICLR.cc/2025/Conference/Submission1/Authors']
        assert submissions[0].content['authorids']['readers'] == ['ICLR.cc/2025/Conference', 'ICLR.cc/2025/Conference/Submission1/Authors']
        assert submissions[0].content['pdf']['readers'] == ['ICLR.cc/2025/Conference', 'ICLR.cc/2025/Conference/Submission1/Authors', 'ICLR.cc/2025/Conference/Submission1/Reviewers']
        
    def test_matching_setup(self, openreview_client, test_client, helpers):

        pc_client = openreview.api.OpenReviewClient(username='sherry@iclr.cc', password=helpers.strong_password)

        pc_client.add_members_to_group('ICLR.cc/2025/Conference/Reviewers', ['reviewer1@iclr.cc', 'reviewer2@iclr.cc', 'reviewer3@iclr.cc'])     
    
        edit = pc_client.post_group_edit(
                invitation='ICLR.cc/2025/Conference/Reviewers/-/Matching_Setup',
                group=openreview.api.Group(
                    content={
                        'assignment_mode': { 'value':  'Automatic' },
                        'conflict_policy': { 'value':  'NeurIPS' }
                    },
                )
            )
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        assert openreview.tools.get_invitation(openreview_client, 'ICLR.cc/2025/Conference/Reviewers/-/Custom_Max_Papers')        
        assert openreview.tools.get_invitation(openreview_client, 'ICLR.cc/2025/Conference/Reviewers/-/Conflict')        
        assert openreview.tools.get_invitation(openreview_client, 'ICLR.cc/2025/Conference/Reviewers/-/Aggregate_Score')        
        assert not openreview.tools.get_invitation(openreview_client, 'ICLR.cc/2025/Conference/Reviewers/-/Affinity_Score')        
        assert openreview.tools.get_invitation(openreview_client, 'ICLR.cc/2025/Conference/Reviewers/-/Assignment_Configuration')        

    
    def test_review_stage(self, openreview_client, test_client, helpers):

        pc_client = openreview.api.OpenReviewClient(username='sherry@iclr.cc', password=helpers.strong_password)
        assert pc_client.get_invitation('ICLR.cc/2025/Conference/-/Official_Review')
        assert pc_client.get_invitation('ICLR.cc/2025/Conference/-/Official_Review/Deadlines')
        assert pc_client.get_invitation('ICLR.cc/2025/Conference/-/Official_Review/Form_Fields')
        assert pc_client.get_invitation('ICLR.cc/2025/Conference/-/Official_Review/Readers')
        assert pc_client.get_invitation('ICLR.cc/2025/Conference/-/Official_Review/Notifications')

        # edit review stage fields
        pc_client.post_invitation_edit(
            invitations='ICLR.cc/2025/Conference/-/Official_Review/Form_Fields',
            content = {
                'note_content': {
                    'value': {
                        "summary": {
                            "order": 1,
                            "description": "Briefly summarize the paper and its contributions. This is not the place to critique the paper; the authors should generally agree with a well-written summary.",
                            "value": {
                            "param": {
                                "maxLength": 200000,
                                "type": "string",
                                "input": "textarea",
                                "markdown": True
                            }
                            }
                        },
                        "review_rating": {
                            "order": 10,
                            "value": {
                            "param": {
                                "type": "string",
                                "enum": [
                                "1: strong reject",
                                "3: reject, not good enough",
                                "5: marginally below the acceptance threshold",
                                "6: marginally above the acceptance threshold",
                                "8: accept, good paper",
                                "10: strong accept, should be highlighted at the conference"
                                ],
                                "input": "radio"
                            }
                            },
                            "description": "Please provide an \"overall score\" for this submission."
                        },
                        'review_confidence': {
                            'order': 4,
                            'value': {
                                'param': {
                                    'type': 'integer',
                                    'enum': [
                                        { 'value': 5, 'description': '5: The reviewer is absolutely certain that the evaluation is correct and very familiar with the relevant literature' },
                                        { 'value': 4, 'description': '4: The reviewer is confident but not absolutely certain that the evaluation is correct' },
                                        { 'value': 3, 'description': '3: The reviewer is fairly confident that the evaluation is correct' },
                                        { 'value': 2, 'description': '2: The reviewer is willing to defend the evaluation, but it is quite likely that the reviewer did not understand central parts of the paper' },
                                        { 'value': 1, 'description': '1: The reviewer\'s evaluation is an educated guess' }
                                    ],
                                    'input': 'radio'
                                }
                            }
                        },
                        'title': {
                            'delete': True
                        },
                        'review': {
                            'delete': True
                        }
                    }
                },
                'rating_field_name': {
                    'value': 'review_rating'
                },
                'confidence_field_name': {
                    'value': 'review_confidence'
                }
            }
        )

        helpers.await_queue_edit(openreview_client, invitation=f'ICLR.cc/2025/Conference/-/Official_Review/Form_Fields')

        review_inv = openreview.tools.get_invitation(openreview_client, 'ICLR.cc/2025/Conference/-/Official_Review')
        assert 'title' not in review_inv.edit['invitation']['edit']['note']['content']
        assert 'review' not in review_inv.edit['invitation']['edit']['note']['content']
        assert 'summary' in review_inv.edit['invitation']['edit']['note']['content']
        assert 'review_rating' in review_inv.edit['invitation']['edit']['note']['content'] and review_inv.edit['invitation']['edit']['note']['content']['review_rating']['value']['param']['enum'][0] == "1: strong reject"
        assert 'review_confidence' in review_inv.edit['invitation']['edit']['note']['content']

        group = openreview_client.get_group('ICLR.cc/2025/Conference')
        assert 'review_rating' in group.content and group.content['review_rating']['value'] == 'review_rating'
        assert 'review_confidence' in group.content and group.content['review_confidence']['value'] == 'review_confidence'

        ## edit Official Review readers
        pc_client.post_invitation_edit(
            invitations='ICLR.cc/2025/Conference/-/Official_Review/Readers',
            content = {
                'reply_readers': {
                    'value':  [
                        'ICLR.cc/2025/Conference/Program_Chairs',
                        'ICLR.cc/2025/Conference/Submission${5/content/noteNumber/value}/Senior_Area_Chairs',
                        'ICLR.cc/2025/Conference/Submission${5/content/noteNumber/value}/Area_Chairs',
                        'ICLR.cc/2025/Conference/Submission${5/content/noteNumber/value}/Reviewers'
                    ]
                }
            }
        )

        review_inv = openreview.tools.get_invitation(openreview_client, 'ICLR.cc/2025/Conference/-/Official_Review')
        assert review_inv.edit['invitation']['edit']['note']['readers'] == [
            'ICLR.cc/2025/Conference/Program_Chairs',
            'ICLR.cc/2025/Conference/Submission${5/content/noteNumber/value}/Senior_Area_Chairs',
            'ICLR.cc/2025/Conference/Submission${5/content/noteNumber/value}/Area_Chairs',
            'ICLR.cc/2025/Conference/Submission${5/content/noteNumber/value}/Reviewers'
        ]

        # create child invitations
        now = datetime.datetime.utcnow()
        new_cdate = openreview.tools.datetime_millis(now - datetime.timedelta(minutes=30))
        new_duedate = openreview.tools.datetime_millis(now + datetime.timedelta(days=3))

        pc_client.post_invitation_edit(
            invitations='ICLR.cc/2025/Conference/-/Official_Review/Deadlines',
            content={
                'activation_date': { 'value': new_cdate },
                'deadline': { 'value': new_duedate },
                'expiration_date': { 'value': new_duedate }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id='ICLR.cc/2025/Conference/-/Official_Review-0-1', count=2)

        invitations = openreview_client.get_invitations(invitation='ICLR.cc/2025/Conference/-/Official_Review')
        assert len(invitations) == 10

        invitation  = openreview_client.get_invitation('ICLR.cc/2025/Conference/Submission1/-/Official_Review')
        assert invitation and invitation.edit['readers'] == [
            'ICLR.cc/2025/Conference/Program_Chairs',
            'ICLR.cc/2025/Conference/Submission1/Senior_Area_Chairs',
            'ICLR.cc/2025/Conference/Submission1/Area_Chairs',
            'ICLR.cc/2025/Conference/Submission1/Reviewers'
        ]

    def test_comment_stage(self, openreview_client, test_client, helpers):

        pc_client = openreview.api.OpenReviewClient(username='sherry@iclr.cc', password=helpers.strong_password)

        now = datetime.datetime.now()
        cdate = openreview.tools.datetime_millis(now - datetime.timedelta(minutes=1))
        expdate = openreview.tools.datetime_millis(now + datetime.timedelta(minutes=28))        

        edit = pc_client.post_invitation_edit(
            invitations='openreview.net/Support/-/Comment_Template',
            signatures=['~ProgramChair_ICLR1'],
            content={
                'venue_id': { 'value': 'ICLR.cc/2025/Conference' },
                'name': { 'value': 'Confidential_Comment' },
                'activation_date': { 'value': cdate },
                'expiration_date': { 'value': expdate },
                'participants': { 'value': ['Program Chairs', 'Assigned Senior Area Chairs', 'Assigned Area Chairs'] },
                'email_program_chairs_about_official_comments': { 'value': 'No, do not email PCs.' },
                'email_senior_area_chairs_about_official_comments' : { 'value': 'Yes, email SACs for every new comment.' },
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'], count=1)
        helpers.await_queue_edit(openreview_client, edit_id='ICLR.cc/2025/Conference/-/Confidential_Comment-0-1', count=1)

        super_invitation = pc_client.get_invitation('ICLR.cc/2025/Conference/-/Confidential_Comment')
        assert super_invitation
        assert pc_client.get_invitation('ICLR.cc/2025/Conference/-/Confidential_Comment/Deadlines')
        assert pc_client.get_invitation('ICLR.cc/2025/Conference/-/Confidential_Comment/Form_Fields')
        assert pc_client.get_invitation('ICLR.cc/2025/Conference/-/Confidential_Comment/Participants_and_Readers')

        invitation = pc_client.get_invitation('ICLR.cc/2025/Conference/Submission1/-/Confidential_Comment')
        assert invitation

        assert not super_invitation.content['email_pcs']['value']
        assert super_invitation.content['email_sacs']['value']

        assert invitation.invitees == ['ICLR.cc/2025/Conference', 'openreview.net/Support', 'ICLR.cc/2025/Conference/Submission1/Senior_Area_Chairs', 'ICLR.cc/2025/Conference/Submission1/Area_Chairs']

        assert invitation.edit['note']['readers']['param']['items'] == [
          {
            "value": "ICLR.cc/2025/Conference/Program_Chairs",
            "optional": False
            # "description": "Program Chairs."
          },
          {
            "value": "ICLR.cc/2025/Conference/Submission1/Senior_Area_Chairs",
            "optional": False
            # "description": "Assigned Senior Area Chairs"
          },
          {
            "value": "ICLR.cc/2025/Conference/Submission1/Area_Chairs",
            "optional": True
            # "description": "Assigned Area Chairs"
          }
        ]

        ## edit Confidential_Comment participants and readers
        with pytest.raises(openreview.OpenReviewException, match=r'The participant Area Chairs must also be readers of comments'):
            pc_client.post_invitation_edit(
                invitations='ICLR.cc/2025/Conference/-/Confidential_Comment/Participants_and_Readers',
                content = {
                    'participants': {
                        'value':  [
                            'ICLR.cc/2025/Conference',
                            'ICLR.cc/2025/Conference/Submission${3/content/noteNumber/value}/Senior_Area_Chairs',
                            'ICLR.cc/2025/Conference/Submission${3/content/noteNumber/value}/Area_Chairs',
                            'ICLR.cc/2025/Conference/Submission${3/content/noteNumber/value}/Authors'
                        ]
                    },
                    'reply_readers': {
                        'value':  [
                            {'value': 'ICLR.cc/2025/Conference', 'optional': False, 'description': 'Program Chairs'},
                            {'value': 'ICLR.cc/2025/Conference/Submission${8/content/noteNumber/value}/Senior_Area_Chairs', 'optional': False, 'description': 'Assigned Senior Area Chairs'},
                            {'value': 'ICLR.cc/2025/Conference/Submission${8/content/noteNumber/value}/Reviewers/Submitted', 'optional': True, 'description': 'Assigned Reviewers who already submitted their review'}
                        ]
                    }
                }
            )
        
        # edit participants and readers
        pc_client.post_invitation_edit(
            invitations='ICLR.cc/2025/Conference/-/Confidential_Comment/Participants_and_Readers',
            content = {
                'participants': {
                    'value':  [
                        'ICLR.cc/2025/Conference',
                        'ICLR.cc/2025/Conference/Submission${3/content/noteNumber/value}/Senior_Area_Chairs',
                        'ICLR.cc/2025/Conference/Submission${3/content/noteNumber/value}/Area_Chairs',
                        'ICLR.cc/2025/Conference/Submission${3/content/noteNumber/value}/Authors'
                    ]
                },
                'reply_readers': {
                    'value':  [
                        {'value': 'ICLR.cc/2025/Conference', 'optional': False, 'description': 'Program Chairs'},
                        {'value': 'ICLR.cc/2025/Conference/Submission${8/content/noteNumber/value}/Senior_Area_Chairs', 'optional': False, 'description': 'Assigned Senior Area Chairs'},
                        {'value': 'ICLR.cc/2025/Conference/Submission${8/content/noteNumber/value}/Area_Chairs', 'optional': True, 'description': 'Assigned Area Chairs'},
                        {'value': 'ICLR.cc/2025/Conference/Submission${8/content/noteNumber/value}/Reviewers/Submitted', 'optional': True, 'description': 'Assigned Reviewers who already submitted their review'},
                        {'value': 'ICLR.cc/2025/Conference/Submission${8/content/noteNumber/value}/Authors', 'optional': True, 'description': 'Paper authors'}
                    ]
                }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id='ICLR.cc/2025/Conference/-/Confidential_Comment-0-1', count=2)

        invitation = openreview_client.get_invitation('ICLR.cc/2025/Conference/Submission1/-/Confidential_Comment')

        assert invitation.invitees == ['ICLR.cc/2025/Conference', 'ICLR.cc/2025/Conference/Submission1/Senior_Area_Chairs', 'ICLR.cc/2025/Conference/Submission1/Area_Chairs', 'ICLR.cc/2025/Conference/Submission1/Authors']
        assert invitation.edit['note']['readers']['param']['items'] == [
          {
            "value": "ICLR.cc/2025/Conference",
            "optional": False,
            "description": "Program Chairs"
          },
          {
            "value": "ICLR.cc/2025/Conference/Submission1/Senior_Area_Chairs",
            "optional": False,
            "description": "Assigned Senior Area Chairs"
          },
          {
            "value": "ICLR.cc/2025/Conference/Submission1/Area_Chairs",
            "optional": True,
            "description": "Assigned Area Chairs"
          },
          {
            "value": "ICLR.cc/2025/Conference/Submission1/Reviewers/Submitted",
            "optional": True,
            "description": "Assigned Reviewers who already submitted their review"
          },
          {
            "value": "ICLR.cc/2025/Conference/Submission1/Authors",
            "optional": True,
            "description": "Paper authors"
          }
        ]

        # edit notification settings
        pc_client.post_invitation_edit(
            invitations='ICLR.cc/2025/Conference/-/Confidential_Comment/Notifications',
            content = {
                'email_pcs': {
                    'value': True
                },
                'email_sacs': {
                    'value': True
                }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id='ICLR.cc/2025/Conference/-/Confidential_Comment-0-1', count=3)

        invitation = pc_client.get_invitation('ICLR.cc/2025/Conference/-/Confidential_Comment')
        assert invitation

        assert invitation.content['email_pcs']['value']
        assert invitation.content['email_sacs']['value']

        submissions = openreview_client.get_notes(invitation='ICLR.cc/2025/Conference/-/Submission', sort='number:asc')
        pc_client.post_note_edit(invitation=f'ICLR.cc/2025/Conference/Submission1/-/Confidential_Comment',
            signatures=['ICLR.cc/2025/Conference/Program_Chairs'],
            note=openreview.api.Note(
                replyto=submissions[0].id,
                readers=['ICLR.cc/2025/Conference', 'ICLR.cc/2025/Conference/Submission1/Senior_Area_Chairs'],
                content={
                    'comment': { 'value': 'this is a comment between PCs and SACs' }
                }
            ))

    def test_metareview_stage(self, openreview_client, test_client, helpers):

        pc_client = openreview.api.OpenReviewClient(username='sherry@iclr.cc', password=helpers.strong_password)

        now = datetime.datetime.utcnow()
        cdate = openreview.tools.datetime_millis(now - datetime.timedelta(minutes=1))
        duedate = openreview.tools.datetime_millis(now + datetime.timedelta(days=10))
        expdate = openreview.tools.datetime_millis(now + datetime.timedelta(days=10))

        edit = pc_client.post_invitation_edit(
            invitations='openreview.net/Support/-/Meta_Review_Template',
            signatures=['~ProgramChair_ICLR1'],
            content={
                'venue_id': { 'value': 'ICLR.cc/2025/Conference' },
                'name': { 'value': 'MetaReview' },
                'activation_date': { 'value': cdate },
                'due_date': { 'value': duedate },
                'expiration_date': { 'value': expdate },
                'readers': { 'value': ['Program_Chairs', 'Senior_Area_Chairs', 'Area_Chairs', 'Reviewers/Submitted']},
                'content': {
                    'value': {
                        'title': {
                            'order': 1,
                            'description': 'Title',
                            'value': { 
                                'param': { 
                                    'type': 'string',
                                    'const': 'Meta Review'
                                }
                            }
                        },
                        'metareview': {
                            'order': 2,
                            'description': 'Please provide an evaluation of the quality, clarity, originality and significance of this work, including a list of its pros and cons. Your comment or reply (max 5000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'maxLength': 5000,
                                    'markdown': True,
                                    'input': 'textarea'
                                }
                            }
                        },
                        'recommendation': {
                            'order': 3,
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'enum': [
                                        'Accept',
                                        'Reject'
                                    ],
                                    'input': 'radio'
                                }
                            }
                        },
                        'confidence': {
                            'order': 4,
                            'value': {
                                'param': {
                                    'type': 'float',
                                    'enum': [
                                        { 'value': 3, 'description': '3: The area chair is absolutely certain' },
                                        { 'value': 2.5, 'description': '2.5: The area chair is confident but not absolutely certain' },
                                        { 'value': 2, 'description': '2: The area chair is somewhat confident' },
                                        { 'value': 1.5, 'description': '1.5: The area chair is not sure' },
                                        { 'value': 1.0, 'description': '1.0: The area chair\'s evaluation is an educated guess' }
                                    ],
                                    'input': 'radio'                
                                }
                            }
                        }
                    }
                },
                'recommendation_field_name': { 'value': 'recommendation' }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'], count=1)

        venue_group = openreview_client.get_group('ICLR.cc/2025/Conference')
        assert 'meta_review_name' in venue_group.content and venue_group.content['meta_review_name']['value'] == 'MetaReview'
        assert 'meta_review_recommendation' in venue_group.content and venue_group.content['meta_review_recommendation']['value'] == 'recommendation'

        assert pc_client.get_invitation('ICLR.cc/2025/Conference/-/MetaReview')
        assert pc_client.get_invitation('ICLR.cc/2025/Conference/-/MetaReview/Deadlines')
        assert pc_client.get_invitation('ICLR.cc/2025/Conference/-/MetaReview/Form_Fields')
        assert pc_client.get_invitation('ICLR.cc/2025/Conference/-/MetaReview/Readers')

        helpers.await_queue_edit(openreview_client, edit_id='ICLR.cc/2025/Conference/-/MetaReview-0-1', count=1)

        #update recommendation field name
        pc_client.post_invitation_edit(
            invitations='ICLR.cc/2025/Conference/-/MetaReview/Form_Fields',
            content = {
                'note_content': {
                    'value': {
                        'metareview': {
                            'order': 1,
                            'description': 'Please provide an evaluation of the quality, clarity, originality and significance of this work, including a list of its pros and cons. Your comment or reply (max 5000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'maxLength': 5000,
                                    'markdown': True,
                                    'input': 'textarea'
                                }
                            }
                        },
                        "recommendation_final": {
                            'order': 2,
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'enum': [
                                        'Accept (Oral)',
                                        'Accept (Poster)',
                                        'Reject'
                                    ],
                                    'input': 'radio'
                                }
                            }
                        },
                        'confidence': {
                            'order': 3,
                            'value': {
                                'param': {
                                    'type': 'integer',
                                    'enum': [
                                        { 'value': 5, 'description': '5: The area chair is absolutely certain' },
                                        { 'value': 4, 'description': '4: The area chair is confident but not absolutely certain' },
                                        { 'value': 3, 'description': '3: The area chair is somewhat confident' },
                                        { 'value': 2, 'description': '2: The area chair is not sure' },
                                        { 'value': 1, 'description': '1: The area chair\'s evaluation is an educated guess' }
                                    ],
                                    'input': 'radio'
                                }
                            }
                        },
                        'title': {
                            'delete': True
                        },
                        'recommendation': {
                            'delete': True
                        }
                    }
                },
                'recommendation_field_name': {
                    'value': 'recommendation_final'
                }
            }
        )

        helpers.await_queue_edit(openreview_client, edit_id='ICLR.cc/2025/Conference/-/MetaReview-0-1', count=2)

        venue_group = openreview_client.get_group('ICLR.cc/2025/Conference')
        assert 'meta_review_recommendation' in venue_group.content and venue_group.content['meta_review_recommendation']['value'] == 'recommendation_final'
        
        invitations = pc_client.get_invitations(invitation='ICLR.cc/2025/Conference/-/MetaReview')
        assert len(invitations) == 10

        invitation  = openreview_client.get_invitation('ICLR.cc/2025/Conference/Submission1/-/MetaReview')
        assert invitation.edit['readers'] == [
            "ICLR.cc/2025/Conference/Submission1/Senior_Area_Chairs",
            "ICLR.cc/2025/Conference/Submission1/Area_Chairs",
            "ICLR.cc/2025/Conference/Submission1/Reviewers/Submitted",
            "ICLR.cc/2025/Conference/Program_Chairs"
        ]
        assert 'title' not in invitation.edit['note']['content']
        assert 'recommendation_final' in invitation.edit['note']['content']
        assert invitation.edit['note']['content']['confidence']['value']['param']['type'] == 'integer'

    def test_decision_stage(self, openreview_client, test_client, helpers):

        pc_client = openreview.api.OpenReviewClient(username='sherry@iclr.cc', password=helpers.strong_password)

        now = datetime.datetime.utcnow()
        cdate = openreview.tools.datetime_millis(now - datetime.timedelta(minutes=1))
        duedate = openreview.tools.datetime_millis(now + datetime.timedelta(days=5))

        edit = pc_client.post_invitation_edit(
            invitations='openreview.net/Support/-/Decision_Template',
            signatures=['~ProgramChair_ICLR1'],
            content={
                'venue_id': { 'value': 'ICLR.cc/2025/Conference' },
                'name': { 'value': 'Final_Decision' },
                'activation_date': { 'value': cdate },
                'due_date': { 'value': duedate },
                'decision_options': { 'value': ['Accept', 'Revision Needed', 'Reject'] },
                'readers': { 'value': ['Program Chairs', 'Assigned Senior Area Chairs', 'Assigned Area Chairs', 'Assigned Reviewers', 'Paper Authors']}
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'], count=1)

        assert pc_client.get_invitation('ICLR.cc/2025/Conference/-/Final_Decision')
        assert pc_client.get_invitation('ICLR.cc/2025/Conference/-/Final_Decision/Deadlines')
        assert pc_client.get_invitation('ICLR.cc/2025/Conference/-/Final_Decision/Readers')

        helpers.await_queue_edit(openreview_client, edit_id='ICLR.cc/2025/Conference/-/Final_Decision-0-1', count=1)

        invitations = pc_client.get_invitations(invitation='ICLR.cc/2025/Conference/-/Final_Decision')
        assert len(invitations) == 10

        invitation  = openreview_client.get_invitation('ICLR.cc/2025/Conference/Submission1/-/Final_Decision')
        assert invitation.edit['readers'] == [
            "ICLR.cc/2025/Conference/Program_Chairs",
            "ICLR.cc/2025/Conference/Submission1/Senior_Area_Chairs",
            "ICLR.cc/2025/Conference/Submission1/Area_Chairs",
            "ICLR.cc/2025/Conference/Submission1/Reviewers",
            "ICLR.cc/2025/Conference/Submission1/Authors"
        ]
        assert 'decision' in invitation.edit['note']['content']
        assert invitation.edit['note']['content']['decision']['value']['param']['enum'] == ['Accept', 'Revision Needed', 'Reject']