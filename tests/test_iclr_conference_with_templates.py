import os
import re
import csv
import pytest
import random
import datetime
import re
import openreview
from openreview.api import Note
from selenium.webdriver.common.by import By
from openreview.api import OpenReviewClient

class TestSimpleDualAnonymous():

    def test_setup(self, openreview_client, helpers):
        super_id = 'openreview.net'
        support_group_id = super_id + '/Support'

        helpers.create_user('programchair@iclr.cc', 'ProgramChair', 'ICLROne')
        helpers.create_user('reviewer_one@iclr.cc', 'Reviewer', 'ICLROne')
        helpers.create_user('reviewer_two@iclr.cc', 'Reviewer', 'ICLRTwo')
        helpers.create_user('reviewer_three@iclr.cc', 'Reviewer', 'ICLRThree')
        helpers.create_user('areachair_one@iclr.cc', 'AC', 'ICLROne')
        helpers.create_user('areachair_two@iclr.cc', 'AC', 'ICLRTwo')
        helpers.create_user('senioractioneditor_one@iclr.cc', 'SAE', 'ICLROne')
        helpers.create_user('senioractioneditor_two@iclr.cc', 'SAE', 'ICLRTwo')
        pc_client=openreview.api.OpenReviewClient(username='programchair@iclr.cc', password=helpers.strong_password)

        assert openreview_client.get_invitation('openreview.net/-/Edit')
        assert openreview_client.get_group('openreview.net/Support/Venue_Request')
        assert openreview_client.get_invitation('openreview.net/Support/Venue_Request/-/Conference_Review_Workflow')
        assert openreview_client.get_invitation('openreview.net/Support/Venue_Request/Conference_Review_Workflow/-/Deployment')
        assert openreview_client.get_invitation('openreview.net/Support/Venue_Request/Conference_Review_Workflow/-/Comment')

        now = datetime.datetime.now()
        due_date = now + datetime.timedelta(days=2)

        request = pc_client.post_note_edit(invitation='openreview.net/Support/Venue_Request/-/Conference_Review_Workflow',
            signatures=['~ProgramChair_ICLROne1'],
            note=openreview.api.Note(
                content={
                    'official_venue_name': { 'value': 'International Conference on Learning Representations' },
                    'abbreviated_venue_name': { 'value': 'ICLR 2026' },
                    'venue_website_url': { 'value': 'https://iclr.cc/Conferences/2026' },
                    'location': { 'value': 'Minnetonka, Minnesota' },
                    'venue_start_date': { 'value': openreview.tools.datetime_millis(now + datetime.timedelta(weeks=52)) },
                    'program_chair_emails': { 'value': ['programchair@iclr.cc'] },
                    'contact_email': { 'value': 'iclr2026.programchairs@gmail.com' },
                    'submission_start_date': { 'value': openreview.tools.datetime_millis(now) },
                    'submission_deadline': { 'value': openreview.tools.datetime_millis(due_date) },
                    'full_submission_deadline': { 'value': openreview.tools.datetime_millis(now + datetime.timedelta(days=3)) },
                    'reviewers_name': { 'value': 'Reviewers' },
                    'area_chairs_support': { 'value': True },
                    'area_chairs_name': { 'value': 'Action_Editors' },
                    'senior_area_chairs_support': { 'value': True },
                    'senior_area_chairs_name': { 'value': 'Senior_Action_Editors' },
                    'expected_submissions': { 'value': 12000 },
                    'venue_organizer_agreement': { 
                        'value': [
                            'OpenReview natively supports a wide variety of reviewing workflow configurations. However, if we want significant reviewing process customizations or experiments, we will detail these requests to the OpenReview staff at least three months in advance.',
                            'We will ask authors and reviewers to create an OpenReview Profile at least two weeks in advance of the paper submission deadlines.',
                            'When assembling our group of reviewers, we will only include email addresses or OpenReview Profile IDs of people we know to have authored publications relevant to our venue.  (We will not solicit new reviewers using an open web form, because unfortunately some malicious actors sometimes try to create "fake ids" aiming to be assigned to review their own paper submissions.)',
                            'We acknowledge that, if our venue\'s reviewing workflow is non-standard, or if our venue is expecting more than a few hundred submissions for any one deadline, we should designate our own Workflow Chair, who will read the OpenReview documentation and manage our workflow configurations throughout the reviewing process.',
                            'We acknowledge that OpenReview staff work Monday-Friday during standard business hours US Eastern time, and we cannot expect support responses outside those times.  For this reason, we recommend setting submission and reviewing deadlines Monday through Thursday.',
                            'We will treat the OpenReview staff with kindness and consideration.',
                            'We acknowledge that authors and reviewers will be required to share their preferred email.',
                            'We acknowledge that review counts will be collected for all the reviewers and publicly available in OpenReview.',
                            'We acknowledge that metadata for accepted papers will be publicly released in OpenReview.'
                            ]
                    }
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=request['id'])

        # deploy the venue
        edit = openreview_client.post_note_edit(invitation=f'openreview.net/Support/Venue_Request/Conference_Review_Workflow/-/Deployment',
            signatures=[support_group_id],
            note=openreview.api.Note(
                id=request['note']['id'],
                content={
                    'venue_id': { 'value': 'ICLR.cc/2026/Conference' }
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        group = openreview.tools.get_group(openreview_client, 'ICLR.cc/2026/Conference')

        assert 'preferred_emails_groups' in group.content and group.content['preferred_emails_groups']['value'] == [
            'ICLR.cc/2026/Conference/Reviewers',
            'ICLR.cc/2026/Conference/Authors',
            'ICLR.cc/2026/Conference/Action_Editors',
            'ICLR.cc/2026/Conference/Senior_Action_Editors'
        ]
        assert 'preferred_emails_id' in group.content and group.content['preferred_emails_id']['value'] == 'ICLR.cc/2026/Conference/-/Preferred_Emails'
        invitation = openreview_client.get_invitation('ICLR.cc/2026/Conference/-/Preferred_Emails')
        assert invitation

        assert group.content['senior_area_chair_roles']['value'] == ['Senior_Action_Editors']
        assert group.content['senior_area_chairs_id']['value'] == 'ICLR.cc/2026/Conference/Senior_Action_Editors'
        assert group.content['senior_area_chairs_assignment_id']['value'] == 'ICLR.cc/2026/Conference/Senior_Action_Editors/-/Assignment'
        assert group.content['senior_area_chairs_affinity_score_id']['value'] == 'ICLR.cc/2026/Conference/Senior_Action_Editors/-/Affinity_Score'
        assert group.content['senior_area_chairs_name']['value'] == 'Senior_Action_Editors'
        assert group.content['sac_paper_assignments']['value'] == False
        assert group.content['senior_area_chairs_conflict_id']['value'] == 'ICLR.cc/2026/Conference/Senior_Action_Editors/-/Conflict'

        group = openreview.tools.get_group(openreview_client, 'ICLR.cc/2026/Conference/Senior_Action_Editors')
        assert group.readers == [
            'ICLR.cc/2026/Conference',
            'ICLR.cc/2026/Conference/Senior_Action_Editors'
        ]
        assert group.domain == 'ICLR.cc/2026/Conference'

        group = openreview.tools.get_group(openreview_client, 'ICLR.cc/2026/Conference/Senior_Action_Editors/Invited')
        assert group.readers == [
            'ICLR.cc/2026/Conference',
            'ICLR.cc/2026/Conference/Senior_Action_Editors/Invited'
        ]
        assert group.domain == 'ICLR.cc/2026/Conference'

        group = openreview.tools.get_group(openreview_client, 'ICLR.cc/2026/Conference/Senior_Action_Editors/Declined')
        assert group.readers == [
            'ICLR.cc/2026/Conference',
            'ICLR.cc/2026/Conference/Senior_Action_Editors/Declined'
        ]
        assert group.domain == 'ICLR.cc/2026/Conference'

        assert openreview.tools.get_invitation(openreview_client, 'ICLR.cc/2026/Conference/Senior_Action_Editors/-/Message')
        assert openreview.tools.get_invitation(openreview_client, 'ICLR.cc/2026/Conference/Senior_Action_Editors/-/Members')

        submission_invitation = openreview_client.get_invitation('ICLR.cc/2026/Conference/-/Submission')
        assert submission_invitation
        assert submission_invitation.duedate

        assert openreview_client.get_invitation('ICLR.cc/2026/Conference/Reviewers/-/Expertise_Selection')
        assert openreview_client.get_invitation('ICLR.cc/2026/Conference/Action_Editors/-/Expertise_Selection')
        assert openreview_client.get_invitation('ICLR.cc/2026/Conference/Senior_Action_Editors/-/Expertise_Selection')

    def test_sac_recruitment(self, client, openreview_client, helpers, request_page, selenium):

        # use invitation to recruit reviewers
        edit = openreview_client.post_group_edit(

                invitation='ICLR.cc/2026/Conference/Senior_Action_Editors/-/Recruitment_Request',
                content={
                    'invitee_details': { 'value':  'senioractioneditor_one@iclr.cc, SAE ICLROne\nsenioractioneditor_two@iclr.cc, SAE ICLRTwo\nSAC@mail.com\nceleste_martinez1\ninvalid_emäil@iclr.cc' },
                    'invite_message_subject_template': { 'value': '[ICLR 2026] Invitation to serve as Senior Action Editor' },
                    'invite_message_body_template': { 'value': 'Dear {{fullname}},\n\nWe are pleased to invite you to serve as a Senior Action Editor for the ICLR 2026 Conference.\n\nPlease accept or decline the invitation using the link below:\n\n{{invitation_url}}\n\nBest regards,\nICLR 2026 Program Chairs' },
                },
                group=openreview.api.Group()
            )
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'], process_index=1)

        invited_group = openreview_client.get_group('ICLR.cc/2026/Conference/Senior_Action_Editors/Invited')
        assert set(invited_group.members) == {'~SAE_ICLROne1', '~SAE_ICLRTwo1', 'sac@mail.com'}
        assert openreview_client.get_group('ICLR.cc/2026/Conference/Senior_Action_Editors/Declined').members == []
        assert openreview_client.get_group('ICLR.cc/2026/Conference/Senior_Action_Editors').members == []

        edits = openreview_client.get_group_edits(group_id='ICLR.cc/2026/Conference/Senior_Action_Editors/Invited', sort='tcdate:desc')

        messages = openreview_client.get_messages(to='programchair@iclr.cc', subject = 'Recruitment request status for ICLR 2026 Senior Action Editor Group')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == f'''The recruitment request process for the Senior Action Editor Group has been completed.

Invited: 3
Already invited: 0
Already member: 0
Errors: 2

For more details, please check the following links:

- [recruitment request details](https://openreview.net/group/revisions?id=ICLR.cc/2026/Conference/Senior_Action_Editors&editId={edit['id']})
- [invited list](https://openreview.net/group/revisions?id=ICLR.cc/2026/Conference/Senior_Action_Editors/Invited&editId={edits[0].id})
- [all invited list](https://openreview.net/group/edit?id=ICLR.cc/2026/Conference/Senior_Action_Editors/Invited)'''

    def test_submissions(self, client, openreview_client, helpers, test_client):

        test_client = openreview.api.OpenReviewClient(token=test_client.token)

        domains = ['umass.edu', 'amazon.com', 'fb.com', 'cs.umass.edu', 'google.com', 'mit.edu', 'deepmind.com', 'co.ux', 'apple.com', 'nvidia.com']
        for domain in domains:
            helpers.create_user(f'eddie@{domain}', 'Eddie', f'{domain.split(".")[0].capitalize()}')

        for i in range(1,11):
            note = openreview.api.Note(
                license = 'CC BY 4.0',
                content = {
                    'title': { 'value': 'Paper title ' + str(i) },
                    'abstract': { 'value': 'This is an abstract ' + str(i) },
                    'authorids': { 'value': ['~SomeFirstName_User1', '~Eddie_' + domains[i % 10].split('.')[0].capitalize() + '1'] },
                    'authors': { 'value': ['SomeFirstName User', 'Eddie ' + domains[i % 10].split('.')[0].capitalize()] },
                    'keywords': { 'value': ['machine learning', 'nlp'] },
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                    'email_sharing': { 'value': 'We authorize the sharing of all author emails with Program Chairs.' },
                    'data_release': { 'value': 'We authorize the release of our submission and author names to the public in the event of acceptance.' }
                }
            )
            if i == 1 or i == 10:
                note.content['authors']['value'].append('SAE ICLROne')
                note.content['authorids']['value'].append('~SAE_ICLROne1')

            test_client.post_note_edit(invitation='ICLR.cc/2026/Conference/-/Submission',
                signatures=['~SomeFirstName_User1'],
                note=note)

        helpers.await_queue_edit(openreview_client, invitation='ICLR.cc/2026/Conference/-/Submission', count=10)

        submissions = openreview_client.get_notes(invitation='ICLR.cc/2026/Conference/-/Submission', sort='number:asc')
        assert len(submissions) == 10
        assert submissions[-1].readers == ['ICLR.cc/2026/Conference', '~SomeFirstName_User1', '~Eddie_Umass1', '~SAE_ICLROne1']

    def test_post_submission(self, client, openreview_client, helpers, test_client):

        pc_client=openreview.api.OpenReviewClient(username='programchair@iclr.cc', password=helpers.strong_password)

        # close submission abstract
        now = datetime.datetime.now()

        edit = pc_client.post_invitation_edit(
            invitations='ICLR.cc/2026/Conference/-/Submission/Dates',
            content={
                'activation_date': { 'value': openreview.tools.datetime_millis(now - datetime.timedelta(days=1)) },
                'due_date': { 'value': openreview.tools.datetime_millis(now - datetime.timedelta(hours=2)) }
            }
        )

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])
        helpers.await_queue_edit(openreview_client, 'ICLR.cc/2026/Conference/-/Full_Submission-0-1', count=2)
        helpers.await_queue_edit(openreview_client, 'ICLR.cc/2026/Conference/Reviewers/-/Submission_Message-0-1', count=2)
        helpers.await_queue_edit(openreview_client, 'ICLR.cc/2026/Conference/Action_Editors/-/Submission_Message-0-1', count=2)

        full_submission_inv = openreview_client.get_invitations(invitation='ICLR.cc/2026/Conference/-/Full_Submission')
        assert len(full_submission_inv) == 10

        # release submissions to the public
        edit = pc_client.post_invitation_edit(
            invitations='ICLR.cc/2026/Conference/-/Submission_Change_Before_Bidding/Readers',
            content={
                'readers': { 'value': ['everyone'] }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id='ICLR.cc/2026/Conference/-/Submission_Change_Before_Bidding-0-1', count=2)

        edit = pc_client.post_invitation_edit(
            invitations='ICLR.cc/2026/Conference/-/Submission_Change_Before_Bidding/Dates',
            content={
                'activation_date': { 'value': openreview.tools.datetime_millis(now - datetime.timedelta(days=1)) }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id='ICLR.cc/2026/Conference/-/Submission_Change_Before_Bidding-0-1', count=3)

        submission_invitation = pc_client.get_invitation('ICLR.cc/2026/Conference/-/Submission')
        assert submission_invitation.expdate < openreview.tools.datetime_millis(now)

        submissions = pc_client.get_notes(invitation='ICLR.cc/2026/Conference/-/Submission', sort='number:asc')
        submission = submissions[0]
        assert len(submissions) == 10
        assert submission.license == 'CC BY 4.0'
        assert submission.readers == ['everyone']
        assert '_bibtex' in submission.content
        assert 'author={Anonymous}' in submission.content['_bibtex']['value']
        year = datetime.datetime.now().year
        valid_bibtex = '''@inproceedings{
anonymous'''+str(year)+'''paper,
title={Paper title 1},
author={Anonymous},
booktitle={Submitted to International Conference on Learning Representations},
year={'''+str(year)+'''},
url={https://openreview.net/forum?id='''

        valid_bibtex = valid_bibtex + submission.forum + '''},
note={under review}
}'''
        assert submission.content['_bibtex']['value'] == valid_bibtex

        full_submission_inv = openreview_client.get_invitation(id='ICLR.cc/2026/Conference/-/Full_Submission')

        # allow authors to edit license field
        pc_client.post_invitation_edit(
            invitations='ICLR.cc/2026/Conference/-/Full_Submission/Form_Fields',
            content={
                'content': {
                    'value': full_submission_inv.edit['invitation']['edit']['note']['content']
                },
                'license': {
                    'value':  [
                        {'value': 'CC BY 4.0', 'description': 'CC BY 4.0'},
                        {'value': 'CC BY-SA 4.0', 'description': 'CC BY-SA 4.0'},
                        {'value': 'CC0 1.0', 'description': 'CC0 1.0'}
                    ]
                }
            }
        )

        helpers.await_queue_edit(openreview_client, edit_id='ICLR.cc/2026/Conference/-/Full_Submission-0-1', count=3)

        test_client = openreview.api.OpenReviewClient(token=test_client.token)

        revision_note = test_client.post_note_edit(
            invitation = f'ICLR.cc/2026/Conference/Submission{submission.number}/-/Full_Submission',
            signatures = [f'ICLR.cc/2026/Conference/Submission{submission.number}/Authors'],
            note = openreview.api.Note(
                license = 'CC0 1.0',
                content = {
                    'title': { 'value': submission.content['title']['value'] + ' license revision' },
                    'abstract': { 'value': submission.content['abstract']['value'] },
                    'authorids': { 'value': submission.content['authorids']['value'] },
                    'authors': { 'value': submission.content['authors']['value'] },
                    'keywords': {'value': submission.content['keywords']['value']},
                    'pdf': { 'value': submission.content['pdf']['value'] },
                    'email_sharing': { 'value': submission.content['email_sharing']['value'] },
                    'data_release': { 'value': submission.content['data_release']['value'] }
                }
            ))
        helpers.await_queue_edit(openreview_client, edit_id=revision_note['id'])

        assert revision_note['readers'] == ['ICLR.cc/2026/Conference', f'ICLR.cc/2026/Conference/Submission{submission.number}/Authors']

        submission = pc_client.get_notes(invitation='ICLR.cc/2026/Conference/-/Submission', sort='number:asc')[0]
        assert submission.license == 'CC0 1.0'
        assert submission.readers == ['everyone']
        assert '_bibtex' in submission.content
        assert 'author={Anonymous}' in submission.content['_bibtex']['value']
        valid_bibtex = '''@inproceedings{
anonymous'''+str(year)+'''paper,
title={Paper title 1 license revision},
author={Anonymous},
booktitle={Submitted to International Conference on Learning Representations},
year={'''+str(year)+'''},
url={https://openreview.net/forum?id='''     

        valid_bibtex = valid_bibtex + submission.forum + '''},
note={under review}
}'''
        assert submission.content['_bibtex']['value'] == valid_bibtex

    def test_SAC_bidding(self, client, openreview_client, helpers, test_client, request_page, selenium):

        pc_client=openreview.api.OpenReviewClient(username='programchair@iclr.cc', password=helpers.strong_password)

        bid_invitation = openreview_client.get_invitation('ICLR.cc/2026/Conference/Senior_Action_Editors/-/Bid')
        assert bid_invitation
        assert bid_invitation.edit['label']['param']['enum'] == ['Very High', 'High', 'Neutral', 'Low', 'Very Low']
        assert bid_invitation.minReplies == 50
        assert bid_invitation.edit['head']['param']['options']['group'] == 'ICLR.cc/2026/Conference/Action_Editors'
        assert bid_invitation.edit['tail']['param']['options']['group'] == 'ICLR.cc/2026/Conference/Senior_Action_Editors'
        assert openreview_client.get_invitation('ICLR.cc/2026/Conference/Senior_Action_Editors/-/Bid/Dates')
        assert openreview_client.get_invitation('ICLR.cc/2026/Conference/Senior_Action_Editors/-/Bid/Settings')

        # before enabling bidding, run affinity score computation

        # enable bidding for SACs
        now = datetime.datetime.now()
        new_cdate = openreview.tools.datetime_millis(now)
        new_duedate = openreview.tools.datetime_millis(now + datetime.timedelta(days=5))
        edit = pc_client.post_invitation_edit(
            invitations='ICLR.cc/2026/Conference/Senior_Action_Editors/-/Bid/Dates',
            content={
                'activation_date': { 'value': new_cdate },
                'due_date': { 'value': new_duedate },
                'expiration_date': { 'value': new_duedate }
            }
        )

        openreview_client.add_members_to_group('ICLR.cc/2026/Conference/Senior_Action_Editors', ['~SAE_ICLROne1', '~SAE_ICLRTwo1'])
        openreview_client.add_members_to_group('ICLR.cc/2026/Conference/Action_Editors', ['~AC_ICLROne1', '~AC_ICLRTwo1'])

        sae_client = openreview.api.OpenReviewClient(username='senioractioneditor_one@iclr.cc', password=helpers.strong_password)

        # Check that reviewers bid console loads
        request_page(selenium, f'http://localhost:3030/invitation?id={bid_invitation.id}', sae_client, wait_for_element='header')
        header = selenium.find_element(By.ID, 'header')
        assert 'Senior Action Editor Bidding Console' in header.text