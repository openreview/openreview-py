import pytest
import datetime
import openreview
import os
import csv
import random
from selenium.webdriver.common.by import By

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
                    'area_chairs_support': { 'value': True },
                    'senior_area_chairs_support': { 'value': True },
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
            'ICLR.cc/2026/Conference/Area_Chairs',
            'ICLR.cc/2026/Conference/Senior_Area_Chairs'
        ]
        assert 'preferred_emails_id' in group.content and group.content['preferred_emails_id']['value'] == 'ICLR.cc/2026/Conference/-/Preferred_Emails'
        invitation = openreview_client.get_invitation('ICLR.cc/2026/Conference/-/Preferred_Emails')
        assert invitation

        assert group.content['senior_area_chair_roles']['value'] == ['Senior_Area_Chairs']
        assert group.content['senior_area_chairs_id']['value'] == 'ICLR.cc/2026/Conference/Senior_Area_Chairs'
        assert group.content['senior_area_chairs_assignment_id']['value'] == 'ICLR.cc/2026/Conference/Senior_Area_Chairs/-/Assignment'
        assert group.content['senior_area_chairs_affinity_score_id']['value'] == 'ICLR.cc/2026/Conference/Senior_Area_Chairs/-/Affinity_Score'
        assert group.content['senior_area_chairs_name']['value'] == 'Senior_Area_Chairs'
        assert group.content['sac_paper_assignments']['value'] == False
        assert group.content['senior_area_chairs_conflict_id']['value'] == 'ICLR.cc/2026/Conference/Senior_Area_Chairs/-/Conflict'

        group = openreview.tools.get_group(openreview_client, 'ICLR.cc/2026/Conference/Senior_Area_Chairs')
        assert group.readers == [
            'ICLR.cc/2026/Conference',
            'ICLR.cc/2026/Conference/Senior_Area_Chairs'
        ]
        assert group.domain == 'ICLR.cc/2026/Conference'

        group = openreview.tools.get_group(openreview_client, 'ICLR.cc/2026/Conference/Senior_Area_Chairs/Invited')
        assert group.readers == [
            'ICLR.cc/2026/Conference',
            'ICLR.cc/2026/Conference/Senior_Area_Chairs/Invited'
        ]
        assert group.domain == 'ICLR.cc/2026/Conference'

        group = openreview.tools.get_group(openreview_client, 'ICLR.cc/2026/Conference/Senior_Area_Chairs/Declined')
        assert group.readers == [
            'ICLR.cc/2026/Conference',
            'ICLR.cc/2026/Conference/Senior_Area_Chairs/Declined'
        ]
        assert group.domain == 'ICLR.cc/2026/Conference'

        assert openreview.tools.get_invitation(openreview_client, 'ICLR.cc/2026/Conference/Senior_Area_Chairs/-/Message')
        assert openreview.tools.get_invitation(openreview_client, 'ICLR.cc/2026/Conference/Senior_Area_Chairs/-/Members')

        submission_invitation = openreview_client.get_invitation('ICLR.cc/2026/Conference/-/Submission')
        assert submission_invitation
        assert submission_invitation.duedate

        assert openreview_client.get_invitation('ICLR.cc/2026/Conference/Reviewers/-/Expertise_Selection')
        assert openreview_client.get_invitation('ICLR.cc/2026/Conference/Area_Chairs/-/Expertise_Selection')
        assert openreview_client.get_invitation('ICLR.cc/2026/Conference/Senior_Area_Chairs/-/Expertise_Selection')

        group = openreview.tools.get_group(openreview_client, 'ICLR.cc/2026/Conference/Reviewers')
        assert group.domain == 'ICLR.cc/2026/Conference'
        assert group.readers == [
            'ICLR.cc/2026/Conference',
            'ICLR.cc/2026/Conference/Reviewers',
            'ICLR.cc/2026/Conference/Senior_Area_Chairs',
            'ICLR.cc/2026/Conference/Area_Chairs'
        ]

        group = openreview.tools.get_group(openreview_client, 'ICLR.cc/2026/Conference/Area_Chairs')
        assert group.readers == [
            'ICLR.cc/2026/Conference',
            'ICLR.cc/2026/Conference/Area_Chairs',
            'ICLR.cc/2026/Conference/Senior_Area_Chairs'
        ]

        group = openreview.tools.get_group(openreview_client, 'ICLR.cc/2026/Conference/Senior_Area_Chairs')
        assert group.readers == [
            'ICLR.cc/2026/Conference',
            'ICLR.cc/2026/Conference/Senior_Area_Chairs'
        ]

        group = openreview.tools.get_group(openreview_client, 'ICLR.cc/2026/Conference/Senior_Area_Chairs/Invited')
        assert group.readers == [
            'ICLR.cc/2026/Conference',
            'ICLR.cc/2026/Conference/Senior_Area_Chairs/Invited'
        ]

        group = openreview.tools.get_group(openreview_client, 'ICLR.cc/2026/Conference/Senior_Area_Chairs/Declined')
        assert group.readers == [
            'ICLR.cc/2026/Conference',
            'ICLR.cc/2026/Conference/Senior_Area_Chairs/Declined'
        ]

        domain_content = openreview.tools.get_group(openreview_client, 'ICLR.cc/2026/Conference').content
        assert domain_content['senior_area_chair_roles']['value'] == ['Senior_Area_Chairs']
        assert domain_content['senior_area_chairs_id']['value'] == 'ICLR.cc/2026/Conference/Senior_Area_Chairs'
        assert domain_content['senior_area_chairs_assignment_id']['value'] == 'ICLR.cc/2026/Conference/Senior_Area_Chairs/-/Assignment'
        assert domain_content['senior_area_chairs_affinity_score_id']['value'] == 'ICLR.cc/2026/Conference/Senior_Area_Chairs/-/Affinity_Score'
        assert domain_content['senior_area_chairs_name']['value'] == 'Senior_Area_Chairs'
        assert domain_content['sac_paper_assignments']['value'] == False
        assert domain_content['senior_area_chairs_conflict_id']['value'] == 'ICLR.cc/2026/Conference/Senior_Area_Chairs/-/Conflict'

        # add a reciprocal reviewing field to the submission form, the value must be a subset of the authors.
        # the authors, pdf and reciprocal_reviewing fields are visible only to the venue and the paper
        # authors starting from the first edit.
        field_readers = [
            'ICLR.cc/2026/Conference',
            'ICLR.cc/2026/Conference/Submission${{4/id}/number}/Authors'
        ]
        pc_client.post_invitation_edit(
            invitations='ICLR.cc/2026/Conference/-/Submission/Form_Fields',
            content={
                'content': {
                    'value': {
                        'authors': { 'readers': field_readers },
                        'pdf': { 'readers': field_readers },
                        'reciprocal_reviewing': {
                            'order': 10,
                            'description': 'Enter the profile ids of the authors of this submission who will serve as reviewers.',
                            'value': {
                                'param': {
                                    'type': 'string[]',
                                    'enum': ['${3/authors/value/*/username}'],
                                    'input': 'select'
                                }
                            },
                            'readers': field_readers
                        }
                    }
                },
                'license': {
                    'value': [
                        {'value': 'CC BY 4.0', 'description': 'CC BY 4.0'}
                    ]
                }
            }
        )

        submission_invitation = openreview_client.get_invitation('ICLR.cc/2026/Conference/-/Submission')
        assert 'reciprocal_reviewing' in submission_invitation.edit['note']['content']
        assert submission_invitation.edit['note']['content']['reciprocal_reviewing']['value']['param']['enum'] == ['${3/authors/value/*/username}']
        assert submission_invitation.edit['note']['content']['authors']['readers'] == field_readers
        assert submission_invitation.edit['note']['content']['pdf']['readers'] == field_readers
        assert submission_invitation.edit['note']['content']['reciprocal_reviewing']['readers'] == field_readers

    def test_sac_recruitment(self, client, openreview_client, helpers, request_page, selenium):

        # use invitation to recruit reviewers
        edit = openreview_client.post_group_edit(

                invitation='ICLR.cc/2026/Conference/Senior_Area_Chairs/-/Recruitment_Request',
                content={
                    'invitee_details': { 'value':  'senioractioneditor_one@iclr.cc, SAE ICLROne\nsenioractioneditor_two@iclr.cc, SAE ICLRTwo\nSAC@mail.com\nceleste_martinez1\ninvalid_emäil@iclr.cc' },
                    'invite_message_subject_template': { 'value': '[ICLR 2026] Invitation to serve as Senior Area Chair' },
                    'invite_message_body_template': { 'value': 'Dear {{fullname}},\n\nWe are pleased to invite you to serve as a Senior Area Chair for the ICLR 2026 Conference.\n\nPlease accept or decline the invitation using the link below:\n\n{{invitation_url}}\n\nBest regards,\nICLR 2026 Program Chairs' },
                },
                group=openreview.api.Group()
            )
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'], process_index=1)

        invited_group = openreview_client.get_group('ICLR.cc/2026/Conference/Senior_Area_Chairs/Invited')
        assert set(invited_group.members) == {'~SAE_ICLROne1', '~SAE_ICLRTwo1', 'sac@mail.com'}
        assert openreview_client.get_group('ICLR.cc/2026/Conference/Senior_Area_Chairs/Declined').members == []
        assert openreview_client.get_group('ICLR.cc/2026/Conference/Senior_Area_Chairs').members == []

        edits = openreview_client.get_group_edits(group_id='ICLR.cc/2026/Conference/Senior_Area_Chairs/Invited', sort='tcdate:desc')

        messages = openreview_client.get_messages(to='programchair@iclr.cc', subject = 'Recruitment request status for ICLR 2026 Senior Area Chair Group')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == f'''The recruitment request process for the Senior Area Chair Group has been completed.

Invited: 3
Already invited: 0
Already member: 0
Errors: 2

For more details, please check the following links:

- [recruitment request details](https://openreview.net/group/revisions?id=ICLR.cc/2026/Conference/Senior_Area_Chairs&editId={edit['id']})
- [invited list](https://openreview.net/group/revisions?id=ICLR.cc/2026/Conference/Senior_Area_Chairs/Invited&editId={edits[0].id})
- [all invited list](https://openreview.net/group/edit?id=ICLR.cc/2026/Conference/Senior_Area_Chairs/Invited)'''

    def test_submissions(self, client, openreview_client, helpers, test_client):

        test_client = openreview.api.OpenReviewClient(token=test_client.token)

        domains = ['umass.edu', 'amazon.com', 'fb.com', 'cs.umass.edu', 'google.com', 'mit.edu', 'deepmind.com', 'co.ux', 'apple.com', 'nvidia.com']
        for domain in domains:
            helpers.create_user(f'eddie@{domain}', 'Eddie', f'{domain.split(".")[0].capitalize()}')

        for i in range(1,11):
            eddie_domain = domains[i % 10]
            domain_name = eddie_domain.split('.')[0].capitalize()
            note = openreview.api.Note(
                license = 'CC BY 4.0',
                content = {
                    'title': { 'value': 'Paper title ' + str(i) },
                    'abstract': { 'value': 'This is an abstract ' + str(i) },
                    'authors': {
                        'value': [
                            {
                                'fullname': 'SomeFirstName User',
                                'username': '~SomeFirstName_User1',
                                'institutions': [{ 'domain': 'mail.com', 'country': 'US' }]
                            },
                            {
                                'fullname': f'Eddie {domain_name}',
                                'username': f'~Eddie_{domain_name}1',
                                'institutions': [{ 'domain': eddie_domain, 'country': 'US' }]
                            }
                        ]
                    },
                    'keywords': { 'value': ['machine learning', 'nlp'] },
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                    'email_sharing': { 'value': 'We authorize the sharing of all author emails with Program Chairs.' },
                    'data_release': { 'value': 'We authorize the release of our submission and author names to the public in the event of acceptance.' },
                    'reciprocal_reviewing': { 'value': ['~SomeFirstName_User1'] }
                }
            )
            if i == 1 or i == 10:
                note.content['authors']['value'].append({
                    'fullname': 'SAE ICLROne',
                    'username': '~SAE_ICLROne1',
                    'institutions': [{ 'domain': 'iclr.cc', 'country': 'US' }]
                })

            test_client.post_note_edit(invitation='ICLR.cc/2026/Conference/-/Submission',
                signatures=['~SomeFirstName_User1'],
                note=note)

        helpers.await_queue_edit(openreview_client, invitation='ICLR.cc/2026/Conference/-/Submission', count=10)

        submissions = openreview_client.get_notes(invitation='ICLR.cc/2026/Conference/-/Submission', sort='number:asc')
        assert len(submissions) == 10
        assert submissions[-1].readers == ['ICLR.cc/2026/Conference', '~SomeFirstName_User1', '~Eddie_Umass1', '~SAE_ICLROne1']

        # the authors, pdf and reciprocal_reviewing fields are hidden starting from the first edit
        for submission in submissions:
            assert submission.content['authors']['readers'] == ['ICLR.cc/2026/Conference', f'ICLR.cc/2026/Conference/Submission{submission.number}/Authors']
            assert submission.content['pdf']['readers'] == ['ICLR.cc/2026/Conference', f'ICLR.cc/2026/Conference/Submission{submission.number}/Authors']
            assert submission.content['reciprocal_reviewing']['readers'] == ['ICLR.cc/2026/Conference', f'ICLR.cc/2026/Conference/Submission{submission.number}/Authors']

        # the reciprocal reviewing value must be one of the authors of the submission
        with pytest.raises(openreview.OpenReviewException, match=r'.*must be equal to one of the allowed values.*'):
            test_client.post_note_edit(invitation='ICLR.cc/2026/Conference/-/Submission',
                signatures=['~SomeFirstName_User1'],
                note=openreview.api.Note(
                    license = 'CC BY 4.0',
                    content = {
                        'title': { 'value': 'Paper title with invalid reciprocal reviewer' },
                        'abstract': { 'value': 'This is an abstract' },
                        'authors': {
                            'value': [
                                {
                                    'fullname': 'SomeFirstName User',
                                    'username': '~SomeFirstName_User1',
                                    'institutions': [{ 'domain': 'mail.com', 'country': 'US' }]
                                }
                            ]
                        },
                        'keywords': { 'value': ['machine learning', 'nlp'] },
                        'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' },
                        'email_sharing': { 'value': 'We authorize the sharing of all author emails with Program Chairs.' },
                        'data_release': { 'value': 'We authorize the release of our submission and author names to the public in the event of acceptance.' },
                        'reciprocal_reviewing': { 'value': ['~ProgramChair_ICLROne1'] }
                    }
                ))

    def test_post_submission(self, client, openreview_client, helpers, test_client):

        pc_client=openreview.api.OpenReviewClient(username='programchair@iclr.cc', password=helpers.strong_password)

        # close submission abstract
        now = datetime.datetime.now()

        edit = pc_client.post_invitation_edit(
            invitations='ICLR.cc/2026/Conference/-/Submission/Dates',
            content={
                'activation_date': { 'value': openreview.tools.datetime_millis(now - datetime.timedelta(days=1)) },
                'due_date': { 'value': openreview.tools.datetime_millis(now - datetime.timedelta(hours=5)) }
            }
        )

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])
        helpers.await_queue_edit(openreview_client, 'ICLR.cc/2026/Conference/-/Full_Submission-0-1', count=2)
        helpers.await_queue_edit(openreview_client, 'ICLR.cc/2026/Conference/Reviewers/-/Submission_Message-0-1', count=2)
        helpers.await_queue_edit(openreview_client, 'ICLR.cc/2026/Conference/Area_Chairs/-/Submission_Message-0-1', count=2)

        full_submission_inv = openreview_client.get_invitations(invitation='ICLR.cc/2026/Conference/-/Full_Submission')
        assert len(full_submission_inv) == 10

        # release submissions to the committee for bidding, the papers are not public yet
        edit = pc_client.post_invitation_edit(
            invitations='ICLR.cc/2026/Conference/-/Submission_Change_Before_Bidding/Dates',
            content={
                'activation_date': { 'value': openreview.tools.datetime_millis(now - datetime.timedelta(days=1)) }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id='ICLR.cc/2026/Conference/-/Submission_Change_Before_Bidding-0-1', count=2)

        submission_invitation = pc_client.get_invitation('ICLR.cc/2026/Conference/-/Submission')
        assert submission_invitation.expdate < openreview.tools.datetime_millis(now)

        submissions = pc_client.get_notes(invitation='ICLR.cc/2026/Conference/-/Submission', sort='number:asc')
        submission = submissions[0]
        assert len(submissions) == 10
        assert submission.license == 'CC BY 4.0'
        assert submission.readers == [
            'ICLR.cc/2026/Conference',
            'ICLR.cc/2026/Conference/Senior_Area_Chairs',
            'ICLR.cc/2026/Conference/Area_Chairs',
            'ICLR.cc/2026/Conference/Reviewers',
            'ICLR.cc/2026/Conference/Submission1/Authors'
        ]
        assert not submissions[0].odate
        assert not submissions[0].pdate
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
        content = full_submission_inv.edit['invitation']['edit']['note']['content']

        # by default the authors field is locked so authors can only be re-ordered, not added or removed
        assert content['authors']['value'] == ['${{4/id}/content/authors/value}']

        # make sure pdfs remain hidden when authors post revisions
        content['pdf']['readers'] = [
            'ICLR.cc/2026/Conference',
            'ICLR.cc/2026/Conference/Submission${{4/id}/number}/Authors'
        ]

        # allow authors to edit license field
        pc_client.post_invitation_edit(
            invitations='ICLR.cc/2026/Conference/-/Full_Submission/Form_Fields',
            content={
                'content': {
                    'value': content
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
        assert submission.readers == [
            'ICLR.cc/2026/Conference',
            'ICLR.cc/2026/Conference/Senior_Area_Chairs',
            'ICLR.cc/2026/Conference/Area_Chairs',
            'ICLR.cc/2026/Conference/Reviewers',
            'ICLR.cc/2026/Conference/Submission1/Authors'
        ]
        assert 'readers' in submission.content['pdf'] and submission.content['pdf']['readers'] == ['ICLR.cc/2026/Conference', f'ICLR.cc/2026/Conference/Submission{submission.number}/Authors']
        assert 'readers' in submission.content['authors'] and submission.content['authors']['readers'] == ['ICLR.cc/2026/Conference', f'ICLR.cc/2026/Conference/Submission{submission.number}/Authors']
        assert 'authorids' not in submission.content
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

        # the reciprocal reviewing field is visible only to the venue and the authors
        assert 'readers' in submission.content['reciprocal_reviewing'] and submission.content['reciprocal_reviewing']['readers'] == ['ICLR.cc/2026/Conference', f'ICLR.cc/2026/Conference/Submission{submission.number}/Authors']

        # reviewers can see the submissions during bidding but not the hidden fields
        openreview_client.add_members_to_group('ICLR.cc/2026/Conference/Reviewers', ['~Reviewer_ICLROne1', '~Reviewer_ICLRTwo1', '~Reviewer_ICLRThree1'])

        reviewer_client = openreview.api.OpenReviewClient(username='reviewer_one@iclr.cc', password=helpers.strong_password)
        reviewer_submission = reviewer_client.get_note(submission.id)
        assert 'authors' not in reviewer_submission.content
        assert 'pdf' not in reviewer_submission.content
        assert 'reciprocal_reviewing' not in reviewer_submission.content

        # authors can be re-ordered but not added or removed during the full submission stage
        submission2 = pc_client.get_notes(invitation='ICLR.cc/2026/Conference/-/Submission', sort='number:asc')[1]
        authors = submission2.content['authors']['value']

        full_submission_content = {
            'title': { 'value': submission2.content['title']['value'] },
            'abstract': { 'value': submission2.content['abstract']['value'] },
            'authors': { 'value': [authors[1], authors[0]] },
            'keywords': { 'value': submission2.content['keywords']['value'] },
            'pdf': { 'value': submission2.content['pdf']['value'] },
            'email_sharing': { 'value': submission2.content['email_sharing']['value'] },
            'data_release': { 'value': submission2.content['data_release']['value'] }
        }

        revision_edit = test_client.post_note_edit(
            invitation='ICLR.cc/2026/Conference/Submission2/-/Full_Submission',
            signatures=['ICLR.cc/2026/Conference/Submission2/Authors'],
            note=openreview.api.Note(
                license='CC BY 4.0',
                content=full_submission_content
            ))
        helpers.await_queue_edit(openreview_client, edit_id=revision_edit['id'])

        submission2 = pc_client.get_notes(invitation='ICLR.cc/2026/Conference/-/Submission', sort='number:asc')[1]
        assert [author['username'] for author in submission2.content['authors']['value']] == ['~Eddie_Fb1', '~SomeFirstName_User1']

        # removing an author is not allowed
        with pytest.raises(openreview.OpenReviewException):
            test_client.post_note_edit(
                invitation='ICLR.cc/2026/Conference/Submission2/-/Full_Submission',
                signatures=['ICLR.cc/2026/Conference/Submission2/Authors'],
                note=openreview.api.Note(
                    license='CC BY 4.0',
                    content={ **full_submission_content, 'authors': { 'value': [authors[0]] } }
                ))

        # adding an author is not allowed
        with pytest.raises(openreview.OpenReviewException):
            test_client.post_note_edit(
                invitation='ICLR.cc/2026/Conference/Submission2/-/Full_Submission',
                signatures=['ICLR.cc/2026/Conference/Submission2/Authors'],
                note=openreview.api.Note(
                    license='CC BY 4.0',
                    content={ **full_submission_content, 'authors': { 'value': [authors[1], authors[0], {'fullname': 'SAE ICLRTwo', 'username': '~SAE_ICLRTwo1', 'institutions': [{ 'domain': 'iclr.cc', 'country': 'US' }]}] } }
                ))

    def test_SAC_bidding(self, client, openreview_client, helpers, test_client, request_page, selenium):

        pc_client=openreview.api.OpenReviewClient(username='programchair@iclr.cc', password=helpers.strong_password)

        bid_invitation = openreview_client.get_invitation('ICLR.cc/2026/Conference/Senior_Area_Chairs/-/Bid')
        assert bid_invitation
        assert bid_invitation.edit['label']['param']['enum'] == ['Very High', 'High', 'Neutral', 'Low', 'Very Low']
        assert bid_invitation.minReplies == 50
        assert bid_invitation.edit['head']['param']['options']['group'] == 'ICLR.cc/2026/Conference/Area_Chairs'
        assert bid_invitation.edit['tail']['param']['options']['group'] == 'ICLR.cc/2026/Conference/Senior_Area_Chairs'
        assert openreview_client.get_invitation('ICLR.cc/2026/Conference/Senior_Area_Chairs/-/Bid/Dates')
        assert openreview_client.get_invitation('ICLR.cc/2026/Conference/Senior_Area_Chairs/-/Bid/Settings')
        assert openreview_client.get_invitation('ICLR.cc/2026/Conference/Senior_Area_Chairs/-/Affinity_Score')
        assert openreview_client.get_invitation('ICLR.cc/2026/Conference/Senior_Area_Chairs/-/Affinity_Score/Model')
        assert openreview_client.get_invitation('ICLR.cc/2026/Conference/Senior_Area_Chairs/-/Affinity_Score/Dates')
        assert not openreview.tools.get_invitation(openreview_client, 'ICLR.cc/2026/Conference/Senior_Area_Chairs/-/Conflict')
        inv = openreview_client.get_invitation('ICLR.cc/2026/Conference/Senior_Area_Chairs/-/Assignment_Configuration')
        assert inv and inv.content['committee_name']['value'] == 'Senior_Area_Chairs'
        assert inv.edit['note']['content']['paper_invitation']['value']['param']['default'] == 'ICLR.cc/2026/Conference/Area_Chairs'
        assert inv.edit['note']['content']['match_group']['value']['param']['default'] == 'ICLR.cc/2026/Conference/Senior_Area_Chairs'

        # enable bidding for SACs
        now = datetime.datetime.now()
        new_cdate = openreview.tools.datetime_millis(now)
        new_duedate = openreview.tools.datetime_millis(now + datetime.timedelta(days=5))
        edit = pc_client.post_invitation_edit(
            invitations='ICLR.cc/2026/Conference/Senior_Area_Chairs/-/Bid/Dates',
            content={
                'activation_date': { 'value': new_cdate },
                'due_date': { 'value': new_duedate },
                'expiration_date': { 'value': new_duedate }
            }
        )

        openreview_client.add_members_to_group('ICLR.cc/2026/Conference/Senior_Area_Chairs', ['~SAE_ICLROne1', '~SAE_ICLRTwo1'])
        openreview_client.add_members_to_group('ICLR.cc/2026/Conference/Area_Chairs', ['~AC_ICLROne1', '~AC_ICLRTwo1'])

        sae_client = openreview.api.OpenReviewClient(username='senioractioneditor_one@iclr.cc', password=helpers.strong_password)

        # Check that reviewers bid console loads
        request_page(selenium, f'http://localhost:3030/invitation?id={bid_invitation.id}', sae_client, wait_for_element='header')
        header = selenium.find_element(By.ID, 'header')
        assert 'Senior Area Chair Bidding Console' in header.text

def test_AC_conflicts(client, openreview_client, helpers):

    pc_client=openreview.api.OpenReviewClient(username='programchair@iclr.cc', password=helpers.strong_password)

    now = datetime.datetime.now()
    now = openreview.tools.datetime_millis(now)

    pc_client.post_invitation_edit(
        invitations='ICLR.cc/2026/Conference/Area_Chairs/-/Conflict/Policy',
        content={
            'conflict_policy': { 'value': 'NeurIPS' },
            'conflict_n_years': { 'value': 3 }
        }
    )

    helpers.await_queue_edit(openreview_client,  edit_id=f'ICLR.cc/2026/Conference/Area_Chairs/-/Conflict-0-1', count=2)

    # trigger conflicts date process 
    pc_client.post_invitation_edit(
            invitations='ICLR.cc/2026/Conference/Area_Chairs/-/Conflict/Dates',
            content={
                'activation_date': { 'value': now }
            }
        )

    helpers.await_queue_edit(openreview_client,  edit_id=f'ICLR.cc/2026/Conference/Area_Chairs/-/Conflict-0-1', count=3)

    venue = openreview_client.get_group('ICLR.cc/2026/Conference')
    # assert status comment posted to request form
    notes = openreview_client.get_notes(invitation='openreview.net/Support/Venue_Request/Conference_Review_Workflow/-/Status', forum=venue.content['request_form_id']['value'], sort='number:asc')
    assert len(notes) == 1
    assert notes[0].content['title']['value'] == 'Area Chairs Conflicts Reminder'
    assert notes[0].content['comment']['value'] == 'Area Chairs conflicts have been successfully computed. Please note that you will need to recompute Area Chairs conflicts once you deploy SAC-AC assignments to account for SAC conflicts.'

    assert len(openreview_client.get_grouped_edges(
        invitation='ICLR.cc/2026/Conference/Area_Chairs/-/Conflict',
        groupby='id'
    )) == 4

def test_sac_deployment(client, openreview_client, helpers):

    pc_client=openreview.api.OpenReviewClient(username='programchair@iclr.cc', password=helpers.strong_password)

    inv = openreview_client.get_invitation('ICLR.cc/2026/Conference/Senior_Area_Chairs/-/Assignment')
    assert inv and inv.content['committee_role']['value'] == 'senior_area_chairs'
    assert inv.edit['head']['param']['inGroup'] == 'ICLR.cc/2026/Conference/Area_Chairs'
    assert inv.edit['tail']['param']['options']['group'] == 'ICLR.cc/2026/Conference/Senior_Area_Chairs'
    assert openreview_client.get_invitation('ICLR.cc/2026/Conference/Senior_Area_Chairs/-/Assignment/Dates')
    assert openreview_client.get_invitation('ICLR.cc/2026/Conference/Senior_Area_Chairs/-/Proposed_Assignment')
    assert openreview_client.get_invitation('ICLR.cc/2026/Conference/Senior_Area_Chairs/-/Aggregate_Score')
    assert openreview_client.get_invitation('ICLR.cc/2026/Conference/Senior_Area_Chairs/-/Custom_Max_Papers')
    assert openreview_client.get_invitation('ICLR.cc/2026/Conference/Senior_Area_Chairs/-/Custom_User_Demands')
    assert openreview_client.get_invitation('ICLR.cc/2026/Conference/Senior_Area_Chairs/-/Assignment_Configuration')
    assert openreview_client.get_invitation('ICLR.cc/2026/Conference/-/Senior_Area_Chairs_Assignment_Deployment')
    assert openreview_client.get_invitation('ICLR.cc/2026/Conference/-/Senior_Area_Chairs_Assignment_Deployment/Dates')
    assert openreview_client.get_invitation('ICLR.cc/2026/Conference/-/Senior_Area_Chairs_Assignment_Deployment/Match')

    #submit Assignment_Configuration
    config_note = openreview_client.post_note_edit(
        invitation='ICLR.cc/2026/Conference/Senior_Area_Chairs/-/Assignment_Configuration',
        readers=['ICLR.cc/2026/Conference'],
        writers=['ICLR.cc/2026/Conference'],
        signatures=['ICLR.cc/2026/Conference'],
        note=openreview.api.Note(
            content={
                'title': { 'value': 'sac-matching-1'},
                'user_demand': { 'value': '1'},
                'max_papers': { 'value': '5'},
                'min_papers': { 'value': '1'},
                'alternates': { 'value': '1'},
                'paper_invitation': { 'value': 'ICLR.cc/2026/Conference/Area_Chairs' },
                'match_group': { 'value': 'ICLR.cc/2026/Conference/Senior_Area_Chairs' },
                'scores_specification': {
                    'value': {
                        'ICLR.cc/2026/Conference/Senior_Area_Chairs/-/Affinity_Score': {
                            'weight': 1,
                            'default': 0
                        },
                        'ICLR.cc/2026/Conference/Senior_Area_Chairs/-/Bid': {
                            'weight': 1,
                            'default': 0,
                            'translate_map': {
                                'Very High': 1.0,
                                'High': 0.5,
                                'Neutral': 0.0,
                                'Low': -0.5,
                                'Very Low': -1.0
                            }
                        }
                    }
                },
                'aggregate_score_invitation': { 'value': 'ICLR.cc/2026/Conference/Senior_Area_Chairs/-/Aggregate_Score'},
                'conflicts_invitation': { 'value': 'ICLR.cc/2026/Conference/Senior_Area_Chairs/-/Conflict'},
                'solver': { 'value': 'FairFlow'},
                'status': { 'value': 'Initialized'},
            }
        )
    )
    helpers.await_queue_edit(openreview_client, invitation=f'ICLR.cc/2026/Conference/Senior_Area_Chairs/-/Assignment_Configuration')

    match_invitation = openreview_client.get_invitation('ICLR.cc/2026/Conference/-/Senior_Area_Chairs_Assignment_Deployment/Match')
    assert match_invitation.edit['content']['match_name']['value']['param']['enum'] == ['sac-matching-1']

    now = datetime.datetime.now()
    now = openreview.tools.datetime_millis(now)

    # trigger deployment date process without selecting match name
    openreview_client.post_invitation_edit(
        invitations='ICLR.cc/2026/Conference/-/Senior_Area_Chairs_Assignment_Deployment/Dates',
        content={
            'activation_date': { 'value': now }
        }
    )

    helpers.await_queue_edit(openreview_client,  edit_id=f'ICLR.cc/2026/Conference/-/Senior_Area_Chairs_Assignment_Deployment-0-1', count=2)

    # assert status comment posted to request form
    venue = openreview_client.get_group('ICLR.cc/2026/Conference')
    notes = openreview_client.get_notes(invitation='openreview.net/Support/Venue_Request/Conference_Review_Workflow/-/Status', forum=venue.content['request_form_id']['value'], sort='number:asc')
    assert len(notes) == 2
    assert notes[-1].content['title']['value'] == 'Senior Area Chairs Assignment Deployment Failed'

    # try to deploy initialized configuration and get an error
    with pytest.raises(openreview.OpenReviewException, match=r'The matching configuration with title "sac-matching-1" does not have status "Complete".'):
        pc_client.post_invitation_edit(
            invitations='ICLR.cc/2026/Conference/-/Senior_Area_Chairs_Assignment_Deployment/Match',
            content = {
                'match_name': { 'value': 'sac-matching-1' }
            }
        )

    # post proposed assignments to test deployment process
    openreview_client.post_edge(openreview.api.Edge(
            invitation = 'ICLR.cc/2026/Conference/Senior_Area_Chairs/-/Proposed_Assignment',
            head = '~AC_ICLROne1',
            tail = '~SAE_ICLROne1',
            signatures = ['ICLR.cc/2026/Conference/Program_Chairs'],
            weight = 1,
            label = 'sac-matching-1'
        ))

    openreview_client.post_edge(openreview.api.Edge(
                invitation = 'ICLR.cc/2026/Conference/Senior_Area_Chairs/-/Proposed_Assignment',
                head = '~AC_ICLRTwo1',
                tail = '~SAE_ICLRTwo1',
                signatures = ['ICLR.cc/2026/Conference/Program_Chairs'],
                weight = 1,
                label = 'sac-matching-1'
            ))

    assert len(openreview_client.get_grouped_edges(
        invitation='ICLR.cc/2026/Conference/Senior_Area_Chairs/-/Proposed_Assignment',
        groupby='id'
    )) == 2

    assert len(openreview_client.get_grouped_edges(
        invitation='ICLR.cc/2026/Conference/Senior_Area_Chairs/-/Assignment',
        groupby='id'
    )) == 0

    #change status of configuration to complete
    openreview_client.post_note_edit(
        invitation='ICLR.cc/2026/Conference/-/Edit',
        signatures=['ICLR.cc/2026/Conference'],
        note=openreview.api.Note(
            id=config_note['note']['id'],
            content = {
                'status': {
                    'value': 'Complete'
                }
            }
        )
    )

    # deploy assignments
    openreview_client.post_invitation_edit(
        invitations='ICLR.cc/2026/Conference/-/Senior_Area_Chairs_Assignment_Deployment/Match',
        content = {
            'match_name': { 'value': 'sac-matching-1' }
        }
    )
    helpers.await_queue_edit(openreview_client,  edit_id=f'ICLR.cc/2026/Conference/-/Senior_Area_Chairs_Assignment_Deployment-0-1', count=3)

    grouped_edges = openreview_client.get_grouped_edges(invitation='ICLR.cc/2026/Conference/Senior_Area_Chairs/-/Assignment', groupby='id')
    assert len(grouped_edges) == 2

    # retrigger AC conflicts after SAC-AC deployment
    now = datetime.datetime.now()
    now = openreview.tools.datetime_millis(now)

    # trigger conflicts date process 
    pc_client.post_invitation_edit(
            invitations='ICLR.cc/2026/Conference/Area_Chairs/-/Conflict/Dates',
            content={
                'activation_date': { 'value': now }
            }
        )

    helpers.await_queue_edit(openreview_client,  edit_id=f'ICLR.cc/2026/Conference/Area_Chairs/-/Conflict-0-1', count=4)

    venue = openreview_client.get_group('ICLR.cc/2026/Conference')
    # assert status comment was not posted to the request form since SAC-AC assignemnts were already deployed
    notes = openreview_client.get_notes(invitation='openreview.net/Support/Venue_Request/Conference_Review_Workflow/-/Status', forum=venue.content['request_form_id']['value'], sort='number:asc')
    assert len(notes) == 2
    assert notes[-1].content['title']['value'] == 'Senior Area Chairs Assignment Deployment Failed'

    assert len(openreview_client.get_grouped_edges(
        invitation='ICLR.cc/2026/Conference/Area_Chairs/-/Conflict',
        groupby='id'
    )) == 12

def test_review_stage(client, openreview_client, helpers):

    pc_client=openreview.api.OpenReviewClient(username='programchair@iclr.cc', password=helpers.strong_password)

    # close submission deadline
    now = datetime.datetime.now()

    edit = pc_client.post_invitation_edit(
        invitations='ICLR.cc/2026/Conference/-/Full_Submission/Dates',
        content={
            'due_date': { 'value': openreview.tools.datetime_millis(now - datetime.timedelta(hours=2)) },
            'expiration_date': { 'value': openreview.tools.datetime_millis(now - datetime.timedelta(hours=1.5)) }
        }
    )

    helpers.await_queue_edit(openreview_client, edit_id=edit['id'])
    helpers.await_queue_edit(openreview_client, 'ICLR.cc/2026/Conference/-/Full_Submission-0-1', count=4)

    edit = pc_client.post_invitation_edit(
            invitations='ICLR.cc/2026/Conference/-/Withdrawal/Dates',
            content={
                'activation_date': { 'value': openreview.tools.datetime_millis(now - datetime.timedelta(minutes=30)) },
                'expiration_date': { 'value': openreview.tools.datetime_millis(now + datetime.timedelta(days=31)) }
            }
        )

    # manually trigger post submission invitations
    helpers.await_queue_edit(openreview_client, edit_id=edit['id'])
    helpers.await_queue_edit(openreview_client, edit_id='ICLR.cc/2026/Conference/-/Withdrawal-0-1', count=2)

    edit = pc_client.post_invitation_edit(
        invitations='ICLR.cc/2026/Conference/-/Desk_Rejection/Dates',
        content={
            'activation_date': { 'value': openreview.tools.datetime_millis(now - datetime.timedelta(minutes=30)) },
            'expiration_date': { 'value': openreview.tools.datetime_millis(now + datetime.timedelta(days=31)) }
        }
    )

    helpers.await_queue_edit(openreview_client, edit_id=edit['id'])
    helpers.await_queue_edit(openreview_client, edit_id='ICLR.cc/2026/Conference/-/Desk_Rejection-0-1', count=2)

    pc_client.post_invitation_edit(
        invitations='ICLR.cc/2026/Conference/Reviewers/-/Submission_Group/Dates',
        content={
            'activation_date': { 'value': openreview.tools.datetime_millis(now - datetime.timedelta(minutes=30)) }
        }
    )

    helpers.await_queue_edit(openreview_client, edit_id='ICLR.cc/2026/Conference/Reviewers/-/Submission_Group-0-1', count=2)

    pc_client.post_invitation_edit(
        invitations='ICLR.cc/2026/Conference/Area_Chairs/-/Submission_Group/Dates',
        content={
            'activation_date': { 'value': openreview.tools.datetime_millis(now - datetime.timedelta(minutes=30)) }
        }
    )

    helpers.await_queue_edit(openreview_client, edit_id='ICLR.cc/2026/Conference/Area_Chairs/-/Submission_Group-0-1', count=2)

    pc_client.post_invitation_edit(
        invitations='ICLR.cc/2026/Conference/Senior_Area_Chairs/-/Submission_Group/Dates',
        content={
            'activation_date': { 'value': openreview.tools.datetime_millis(now - datetime.timedelta(minutes=30)) }
        }
    )

    helpers.await_queue_edit(openreview_client, edit_id='ICLR.cc/2026/Conference/Senior_Area_Chairs/-/Submission_Group-0-1', count=2)

    submission_groups = openreview_client.get_all_groups(prefix='ICLR.cc/2026/Conference/Submission')
    reviewer_groups = [group for group in submission_groups if group.id.endswith('/Reviewers')]
    assert len(reviewer_groups) == 10
    action_editor_groups = [group for group in submission_groups if group.id.endswith('/Area_Chairs')]
    assert len(action_editor_groups) == 10
    senior_action_editor_groups = [group for group in submission_groups if group.id.endswith('/Senior_Area_Chairs')]
    assert len(senior_action_editor_groups) == 10

    withdrawal_invitations = openreview_client.get_all_invitations(invitation='ICLR.cc/2026/Conference/-/Withdrawal')
    assert len(withdrawal_invitations) == 10

    desk_rejection_invitations = openreview_client.get_all_invitations(invitation='ICLR.cc/2026/Conference/-/Desk_Rejection')
    assert len(desk_rejection_invitations) == 10

    submissions = openreview_client.get_notes(invitation='ICLR.cc/2026/Conference/-/Submission', sort='number:asc')
    assert len(submissions) == 10
    assert submissions[0].readers == [
        'ICLR.cc/2026/Conference',
        'ICLR.cc/2026/Conference/Senior_Area_Chairs',
        'ICLR.cc/2026/Conference/Area_Chairs',
        'ICLR.cc/2026/Conference/Reviewers',
        'ICLR.cc/2026/Conference/Submission1/Authors'
    ]
    assert submissions[0].content['pdf']['readers'] == ['ICLR.cc/2026/Conference', 'ICLR.cc/2026/Conference/Submission1/Authors']

    # trigger Submission_Change_Before_Reviewing invitation
    pc_client.post_invitation_edit(
            invitations='ICLR.cc/2026/Conference/-/Submission_Change_Before_Reviewing/Readers',
            content={
                'readers': { 'value': ['everyone'] }
            }
        )

    helpers.await_queue_edit(openreview_client, 'ICLR.cc/2026/Conference/-/Submission_Change_Before_Reviewing-0-1', count=3)

    now = datetime.datetime.now()
    pc_client.post_invitation_edit(
            invitations='ICLR.cc/2026/Conference/-/Submission_Change_Before_Reviewing/Dates',
            content={
                'activation_date': { 'value': openreview.tools.datetime_millis(now) }
            }
        )

    helpers.await_queue_edit(openreview_client, 'ICLR.cc/2026/Conference/-/Submission_Change_Before_Reviewing-0-1', count=4)

    submissions = pc_client.get_notes(invitation='ICLR.cc/2026/Conference/-/Submission', sort='number:asc')
    submission = submissions[0]
    assert len(submissions) == 10
    assert submission.readers == ['everyone']
    assert submission.odate
    assert not submission.pdate
    assert 'readers' not in submission.content['pdf']
    assert 'readers' in submission.content['authors'] and submission.content['authors']['readers'] == ['ICLR.cc/2026/Conference', f'ICLR.cc/2026/Conference/Submission{submission.number}/Authors']
    assert 'readers' in submission.content['reciprocal_reviewing'] and submission.content['reciprocal_reviewing']['readers'] == ['ICLR.cc/2026/Conference', f'ICLR.cc/2026/Conference/Submission{submission.number}/Authors']
    assert 'authorids' not in submission.content

    # create child invitations
    now = datetime.datetime.now()
    new_cdate = openreview.tools.datetime_millis(now)
    new_duedate = openreview.tools.datetime_millis(now + datetime.timedelta(days=3))

    pc_client.post_invitation_edit(
        invitations='ICLR.cc/2026/Conference/-/Official_Review/Dates',
        content={
            'activation_date': { 'value': new_cdate },
            'due_date': { 'value': new_duedate },
            'expiration_date': { 'value': new_duedate }
        }
    )
    helpers.await_queue_edit(openreview_client, edit_id='ICLR.cc/2026/Conference/-/Official_Review-0-1', count=2)

    invitations = openreview_client.get_invitations(invitation='ICLR.cc/2026/Conference/-/Official_Review')
    assert len(invitations) == 10

    invitation  = openreview_client.get_invitation('ICLR.cc/2026/Conference/Submission1/-/Official_Review')
    assert invitation and invitation.edit['note']['readers'] == [
        'ICLR.cc/2026/Conference/Program_Chairs',
        'ICLR.cc/2026/Conference/Submission1/Senior_Area_Chairs', ## SACs are added by default as readers of reviews
        'ICLR.cc/2026/Conference/Submission1/Area_Chairs', ## ACs are added by default as readers of reviews
        '${3/signatures}'
    ]

    assert pc_client.get_invitation('ICLR.cc/2026/Conference/-/Official_Review_Release')
    assert pc_client.get_invitation('ICLR.cc/2026/Conference/-/Official_Review_Release/Dates')
    assert pc_client.get_invitation('ICLR.cc/2026/Conference/-/Official_Review_Release/Readers')

    review_release_inv = openreview.tools.get_invitation(openreview_client, 'ICLR.cc/2026/Conference/-/Official_Review_Release')
    assert review_release_inv.edit['invitation']['edit']['invitation']['edit']['note']['readers'] == [
        'ICLR.cc/2026/Conference/Program_Chairs',
        'ICLR.cc/2026/Conference/Submission${5/content/noteNumber/value}/Senior_Area_Chairs',
        'ICLR.cc/2026/Conference/Submission${5/content/noteNumber/value}/Area_Chairs',
        'ICLR.cc/2026/Conference/Submission${5/content/noteNumber/value}/Reviewers',
        'ICLR.cc/2026/Conference/Submission${5/content/noteNumber/value}/Authors'
    ]

    # assign reviewers to Submission1 and post an official review
    openreview_client.add_members_to_group('ICLR.cc/2026/Conference/Submission1/Reviewers', ['~Reviewer_ICLROne1', '~Reviewer_ICLRTwo1', '~Reviewer_ICLRThree1'])

    reviewer_client = openreview.api.OpenReviewClient(username='reviewer_one@iclr.cc', password=helpers.strong_password)

    anon_groups = reviewer_client.get_groups(prefix='ICLR.cc/2026/Conference/Submission1/Reviewer_', signatory='~Reviewer_ICLROne1')
    anon_group_id = anon_groups[0].id

    review_edit = reviewer_client.post_note_edit(
        invitation='ICLR.cc/2026/Conference/Submission1/-/Official_Review',
        signatures=[anon_group_id],
        note=openreview.api.Note(
            content={
                'title': { 'value': 'Good paper, accept'},
                'review': { 'value': 'Excellent paper, accept'},
                'rating': { 'value': 10},
                'confidence': { 'value': 5},
            }
        )
    )

    helpers.await_queue_edit(openreview_client, edit_id=review_edit['id'])

    reviews = openreview_client.get_notes(invitation='ICLR.cc/2026/Conference/Submission1/-/Official_Review')
    assert len(reviews) == 1
    assert reviews[0].readers == [
        'ICLR.cc/2026/Conference/Program_Chairs',
        'ICLR.cc/2026/Conference/Submission1/Senior_Area_Chairs',
        'ICLR.cc/2026/Conference/Submission1/Area_Chairs',
        anon_group_id
    ]

def test_comment_stage(client, openreview_client, helpers):

    pc_client=openreview.api.OpenReviewClient(username='programchair@iclr.cc', password=helpers.strong_password)

    assert pc_client.get_invitation('ICLR.cc/2026/Conference/-/Official_Comment')
    assert pc_client.get_invitation('ICLR.cc/2026/Conference/-/Official_Comment/Dates')
    assert pc_client.get_invitation('ICLR.cc/2026/Conference/-/Official_Comment/Form_Fields')
    assert pc_client.get_invitation('ICLR.cc/2026/Conference/-/Official_Comment/Writers_and_Readers')
    assert pc_client.get_invitation('ICLR.cc/2026/Conference/-/Official_Comment/Notifications')

    # create child invitations
    now = datetime.datetime.now()
    new_cdate = openreview.tools.datetime_millis(now)
    new_duedate = openreview.tools.datetime_millis(now + datetime.timedelta(days=4))

    pc_client.post_invitation_edit(
        invitations='ICLR.cc/2026/Conference/-/Official_Comment/Dates',
        content={
            'activation_date': { 'value': new_cdate },
            'expiration_date': { 'value': new_duedate }
        }
    )
    helpers.await_queue_edit(openreview_client, edit_id='ICLR.cc/2026/Conference/-/Official_Comment-0-1', count=2)

    invitations = openreview_client.get_invitations(invitation='ICLR.cc/2026/Conference/-/Official_Comment')
    assert len(invitations) == 10

    invitation  = openreview_client.get_invitation('ICLR.cc/2026/Conference/Submission1/-/Official_Comment')
    assert invitation.invitees == [
        'ICLR.cc/2026/Conference',
        'openreview.net/Support',
        'ICLR.cc/2026/Conference/Submission1/Senior_Area_Chairs',
        'ICLR.cc/2026/Conference/Submission1/Area_Chairs',
        'ICLR.cc/2026/Conference/Submission1/Reviewers',
        'ICLR.cc/2026/Conference/Submission1/Authors'
    ]
    assert invitation and invitation.edit['note']['readers']['param']['items'] == [
      {
        "value": "ICLR.cc/2026/Conference/Program_Chairs",
        "optional": False
      },
      {
        "value": "ICLR.cc/2026/Conference/Submission1/Senior_Area_Chairs",
        "optional": False
      },
      {
        "value": "ICLR.cc/2026/Conference/Submission1/Area_Chairs",
        "optional": True
      },
      {
        "value": "ICLR.cc/2026/Conference/Submission1/Reviewers",
        "optional": True
      },
      {
        "inGroup": "ICLR.cc/2026/Conference/Submission1/Reviewers",
        "optional": True
      },
      {
        "value": "ICLR.cc/2026/Conference/Submission1/Authors",
        "optional": True
      }
    ]
    assert invitation and invitation.edit['signatures']['param']['items'] == [
        {
            "value": "ICLR.cc/2026/Conference/Program_Chairs",
            "optional": True
        },
        {
            "value": "ICLR.cc/2026/Conference/Submission1/Senior_Area_Chairs",
            "optional": True
        },
        {
            "prefix": "ICLR.cc/2026/Conference/Submission1/Area_Chair_.*",
            "optional": True
        },
        {
            "prefix": "ICLR.cc/2026/Conference/Submission1/Reviewer_.*",
            "optional": True
        },
        {
            "value": "ICLR.cc/2026/Conference/Submission1/Authors",
            "optional": True
        }
    ]

    # PC posts an official comment visible to the paper's senior action editors and action editors
    submissions = openreview_client.get_notes(invitation='ICLR.cc/2026/Conference/-/Submission', sort='number:asc')
    comment_edit = pc_client.post_note_edit(
        invitation='ICLR.cc/2026/Conference/Submission1/-/Official_Comment',
        signatures=['ICLR.cc/2026/Conference/Program_Chairs'],
        note=openreview.api.Note(
            replyto=submissions[0].id,
            content={
                'title': {'value': 'test comment title'},
                'comment': {'value': 'test comment'}
            },
            readers=[
                'ICLR.cc/2026/Conference/Program_Chairs',
                'ICLR.cc/2026/Conference/Submission1/Senior_Area_Chairs',
                'ICLR.cc/2026/Conference/Submission1/Area_Chairs'
            ]
        )
    )

    helpers.await_queue_edit(openreview_client, edit_id=comment_edit['id'])

    comments = openreview_client.get_notes(invitation='ICLR.cc/2026/Conference/Submission1/-/Official_Comment')
    assert len(comments) == 1
    assert comments[0].readers == [
        'ICLR.cc/2026/Conference/Program_Chairs',
        'ICLR.cc/2026/Conference/Submission1/Senior_Area_Chairs',
        'ICLR.cc/2026/Conference/Submission1/Area_Chairs'
    ]

def test_withdrawal_stage(client, openreview_client, helpers, test_client):

    test_client = openreview.api.OpenReviewClient(token=test_client.token)
    pc_client = openreview.api.OpenReviewClient(username='programchair@iclr.cc', password=helpers.strong_password)

    # make withdrawn submissions public and reveal the author identities
    pc_client.post_invitation_edit(
        invitations='ICLR.cc/2026/Conference/-/Withdrawn_Submission/Readers',
        content={
            'readers': { 'value': ['everyone'] }
        }
    )

    reveal_edit = pc_client.post_invitation_edit(
        invitations='ICLR.cc/2026/Conference/-/Withdrawn_Submission/Reveal_Authors',
        content={
            'reveal_author_identities': { 'value': True }
        }
    )
    helpers.await_queue_edit(openreview_client, edit_id=reveal_edit['id'])

    withdrawn_invitation = openreview_client.get_invitation('ICLR.cc/2026/Conference/-/Withdrawn_Submission')
    assert withdrawn_invitation.edit['note']['readers'] == ['everyone']
    assert withdrawn_invitation.edit['note']['content']['authors']['readers'] == { 'param': { 'const': { 'delete': True } } }

    withdraw_note = test_client.post_note_edit(invitation='ICLR.cc/2026/Conference/Submission10/-/Withdrawal',
                                signatures=['ICLR.cc/2026/Conference/Submission10/Authors'],
                                note=openreview.api.Note(
                                    content={
                                        'withdrawal_confirmation': { 'value': 'I have read and agree with the venue\'s withdrawal policy on behalf of myself and my co-authors.' },
                                    }
                                ))

    helpers.await_queue_edit(openreview_client, edit_id=withdraw_note['id'])
    helpers.await_queue_edit(openreview_client, invitation='ICLR.cc/2026/Conference/-/Withdrawn_Submission')

    note = test_client.get_note(withdraw_note['note']['forum'])
    assert note
    assert 'ICLR.cc/2026/Conference/-/Withdrawn_Submission' in note.invitations
    assert note.content['venueid']['value'] == 'ICLR.cc/2026/Conference/Withdrawn_Submission'
    assert note.content['venue']['value'] == 'ICLR 2026 Conference Withdrawn Submission'
    assert note.readers == ['everyone']
    assert 'readers' not in note.content['authors']

    # reverse the withdrawal
    withdrawal_reversion_note = pc_client.post_note_edit(invitation='ICLR.cc/2026/Conference/Submission10/-/Withdrawal_Reversion',
                                signatures=['ICLR.cc/2026/Conference/Program_Chairs'],
                                note=openreview.api.Note(
                                    content={
                                        'revert_withdrawal_confirmation': { 'value': 'We approve the reversion of withdrawn submission.' },
                                    }
                                ))

    helpers.await_queue_edit(openreview_client, edit_id=withdrawal_reversion_note['id'])
    helpers.await_queue_edit(openreview_client, invitation='ICLR.cc/2026/Conference/Submission10/-/Withdrawal_Reversion')

    note = test_client.get_note(withdraw_note['note']['forum'])
    assert note.content['venueid']['value'] == 'ICLR.cc/2026/Conference/Submission'
    assert note.content['venue']['value'] == 'ICLR 2026 Conference Submission'
    assert note.readers == ['everyone']
    # author identities are hidden again after the reversion
    assert 'readers' in note.content['authors'] and note.content['authors']['readers'] == ['ICLR.cc/2026/Conference', 'ICLR.cc/2026/Conference/Submission10/Authors']

def test_desk_rejection_and_custom_stage(client, openreview_client, helpers, test_client):

    test_client = openreview.api.OpenReviewClient(token=test_client.token)
    pc_client = openreview.api.OpenReviewClient(username='programchair@iclr.cc', password=helpers.strong_password)

    # make desk-rejected submissions public and reveal the author identities
    pc_client.post_invitation_edit(
        invitations='ICLR.cc/2026/Conference/-/Desk_Rejected_Submission/Readers',
        content={
            'readers': { 'value': ['everyone'] }
        }
    )

    reveal_edit = pc_client.post_invitation_edit(
        invitations='ICLR.cc/2026/Conference/-/Desk_Rejected_Submission/Reveal_Authors',
        content={
            'reveal_author_identities': { 'value': True }
        }
    )
    helpers.await_queue_edit(openreview_client, edit_id=reveal_edit['id'])

    desk_rejected_invitation = openreview_client.get_invitation('ICLR.cc/2026/Conference/-/Desk_Rejected_Submission')
    assert desk_rejected_invitation.edit['note']['readers'] == ['everyone']
    assert desk_rejected_invitation.edit['note']['content']['authors']['readers'] == { 'param': { 'const': { 'delete': True } } }

    # desk-reject a paper
    desk_reject_note = pc_client.post_note_edit(invitation='ICLR.cc/2026/Conference/Submission10/-/Desk_Rejection',
                                signatures=['ICLR.cc/2026/Conference/Program_Chairs'],
                                note=openreview.api.Note(
                                    content={
                                        'desk_reject_comments': { 'value': 'Wrong format.' },
                                    }
                                ))

    helpers.await_queue_edit(openreview_client, edit_id=desk_reject_note['id'])
    helpers.await_queue_edit(openreview_client, invitation='ICLR.cc/2026/Conference/-/Desk_Rejected_Submission')

    note = pc_client.get_note(desk_reject_note['note']['forum'])
    assert note
    assert 'ICLR.cc/2026/Conference/-/Desk_Rejected_Submission' in note.invitations
    assert note.content['venueid']['value'] == 'ICLR.cc/2026/Conference/Desk_Rejected_Submission'
    assert note.content['venue']['value'] == 'ICLR 2026 Conference Desk Rejected Submission'
    assert note.readers == ['everyone']
    assert 'readers' not in note.content['authors']

    # add a custom stage for desk-rejected submissions
    venue = openreview.venue.helpers.get_venue(pc_client, 'ICLR.cc/2026/Conference', support_user='openreview.net/Support')

    now = datetime.datetime.now()
    due_date = now + datetime.timedelta(days=3)
    venue.custom_stage = openreview.stages.CustomStage(name='Desk_Rejection_Challenge',
        reply_to=openreview.stages.CustomStage.ReplyTo.FORUM,
        source={ 'venueid': 'ICLR.cc/2026/Conference/Desk_Rejected_Submission' },
        due_date=due_date,
        exp_date=due_date + datetime.timedelta(days=1),
        invitees=[openreview.stages.CustomStage.Participants.AUTHORS],
        readers=[openreview.stages.CustomStage.Participants.PROGRAM_CHAIRS, openreview.stages.CustomStage.Participants.SIGNATURES],
        content={
            'desk_reject_challenge': {
                'order': 1,
                'description': 'Explain why you think the desk-rejection was not appropriate.',
                'value': {
                    'param': {
                        'type': 'string',
                        'input': 'textarea',
                        'maxLength': 5000
                    }
                }
            }
        },
        notify_readers=True,
        email_sacs=False)

    venue.create_custom_stage()

    helpers.await_queue_edit(openreview_client, 'ICLR.cc/2026/Conference/-/Desk_Rejection_Challenge-0-1', count=1)

    invitations = openreview_client.get_invitations(invitation='ICLR.cc/2026/Conference/-/Desk_Rejection_Challenge')
    assert len(invitations) == 1
    assert invitations[0].id == 'ICLR.cc/2026/Conference/Submission10/-/Desk_Rejection_Challenge'

    edit = test_client.post_note_edit(invitation='ICLR.cc/2026/Conference/Submission10/-/Desk_Rejection_Challenge',
                                signatures=['ICLR.cc/2026/Conference/Submission10/Authors'],
                                note=openreview.api.Note(
                                    content={
                                        'desk_reject_challenge': { 'value': 'We missed our checklist, please let us upload it during the rebuttal stage.' },
                                    }
                                ))
    helpers.await_queue_edit(openreview_client, edit_id=edit['id'], count=1)

    # reverse the desk-rejection
    desk_rejection_reversion_note = pc_client.post_note_edit(invitation='ICLR.cc/2026/Conference/Submission10/-/Desk_Rejection_Reversion',
                                signatures=['ICLR.cc/2026/Conference/Program_Chairs'],
                                note=openreview.api.Note(
                                    content={
                                        'revert_desk_rejection_confirmation': { 'value': 'We approve the reversion of desk-rejected submission.' },
                                    }
                                ))

    helpers.await_queue_edit(openreview_client, edit_id=desk_rejection_reversion_note['id'])
    helpers.await_queue_edit(openreview_client, invitation='ICLR.cc/2026/Conference/Submission10/-/Desk_Rejection_Reversion')

    note = pc_client.get_note(desk_reject_note['note']['forum'])
    assert note.content['venueid']['value'] == 'ICLR.cc/2026/Conference/Submission'
    assert note.content['venue']['value'] == 'ICLR 2026 Conference Submission'
    assert note.readers == ['everyone']
    # author identities are hidden again after the reversion
    assert 'readers' in note.content['authors'] and note.content['authors']['readers'] == ['ICLR.cc/2026/Conference', 'ICLR.cc/2026/Conference/Submission10/Authors']

    # the custom stage invitation is expired after the reversion
    invitation = openreview_client.get_invitation('ICLR.cc/2026/Conference/Submission10/-/Desk_Rejection_Challenge')
    assert invitation.ddate <= openreview.tools.datetime_millis(datetime.datetime.now())

def test_review_release_stage(client, openreview_client, helpers):

    pc_client = openreview.api.OpenReviewClient(username='programchair@iclr.cc', password=helpers.strong_password)

    # release the reviews to the public
    pc_client.post_invitation_edit(
        invitations='ICLR.cc/2026/Conference/-/Official_Review_Release/Readers',
        content = {
            'readers': {
                'value': ['everyone']
            }
        }
    )
    helpers.await_queue_edit(openreview_client, edit_id='ICLR.cc/2026/Conference/-/Official_Review_Release-0-1', count=2)

    review_release_inv = openreview.tools.get_invitation(openreview_client, 'ICLR.cc/2026/Conference/-/Official_Review_Release')
    assert review_release_inv.edit['invitation']['edit']['invitation']['edit']['note']['readers'] == ['everyone']

    now = datetime.datetime.now()
    pc_client.post_invitation_edit(
        invitations='ICLR.cc/2026/Conference/-/Official_Review_Release/Dates',
        content={
            'activation_date': { 'value': openreview.tools.datetime_millis(now) }
        }
    )
    helpers.await_queue_edit(openreview_client, edit_id='ICLR.cc/2026/Conference/-/Official_Review_Release-0-1', count=3)
    helpers.await_queue_edit(openreview_client, edit_id='ICLR.cc/2026/Conference/-/Official_Review-0-1', count=3)

    reviews = openreview_client.get_notes(invitation='ICLR.cc/2026/Conference/Submission1/-/Official_Review')
    assert len(reviews) == 1
    assert reviews[0].readers == ['everyone']

def test_author_reviews_notification(client, openreview_client, helpers):

    pc_client = openreview.api.OpenReviewClient(username='programchair@iclr.cc', password=helpers.strong_password)

    assert pc_client.get_invitation('ICLR.cc/2026/Conference/-/Author_Reviews_Notification')
    assert pc_client.get_invitation('ICLR.cc/2026/Conference/-/Author_Reviews_Notification/Dates')
    assert pc_client.get_invitation('ICLR.cc/2026/Conference/-/Author_Reviews_Notification/Fields_to_Include')
    assert pc_client.get_invitation('ICLR.cc/2026/Conference/-/Author_Reviews_Notification/Message')

    # select the review fields to include in the email
    pc_client.post_invitation_edit(
        invitations='ICLR.cc/2026/Conference/-/Author_Reviews_Notification/Fields_to_Include',
        content={
            'fields_to_include': { 'value': ['title', 'review', 'rating', 'confidence'] }
        }
    )
    helpers.await_queue_edit(openreview_client, edit_id='ICLR.cc/2026/Conference/-/Author_Reviews_Notification-0-1', count=2)

    # trigger the notification process
    now = datetime.datetime.now()
    pc_client.post_invitation_edit(
        invitations='ICLR.cc/2026/Conference/-/Author_Reviews_Notification/Dates',
        content={
            'activation_date': { 'value': openreview.tools.datetime_millis(now) }
        }
    )
    helpers.await_queue_edit(openreview_client, edit_id='ICLR.cc/2026/Conference/-/Author_Reviews_Notification-0-1', count=3)

    # only Submission1 has a review, so only its authors are notified
    messages = openreview_client.get_messages(subject='[ICLR 2026] The reviews for your submission.*')
    assert messages
    assert all('Paper title 1 license revision' in message['content']['subject'] for message in messages)
    recipients = [message['content']['to'] for message in messages]
    assert 'test@mail.com' in recipients

def test_rebuttal_revision_stage(client, openreview_client, helpers, test_client):

    pc_client = openreview.api.OpenReviewClient(username='programchair@iclr.cc', password=helpers.strong_password)
    test_client = openreview.api.OpenReviewClient(token=test_client.token)

    # allow authors to upload a new PDF as part of the rebuttal, keeping the revision history
    # visible to the readers of the submission so reviewers can compare versions
    venue = openreview.venue.helpers.get_venue(pc_client, 'ICLR.cc/2026/Conference', support_user='openreview.net/Support')

    now = datetime.datetime.now()
    venue.submission_revision_stage = openreview.stages.SubmissionRevisionStage(
        name='Rebuttal_Revision',
        start_date=now,
        due_date=now + datetime.timedelta(days=3),
        remove_fields=['title', 'abstract', 'keywords', 'email_sharing', 'data_release', 'reciprocal_reviewing'],
        allow_author_reorder=openreview.stages.AuthorReorder.DISALLOW_EDIT,
        source={ 'venueid': 'ICLR.cc/2026/Conference/Submission' },
        revision_history_readers=['${{2/note/id}/readers}']
    )
    venue.create_submission_revision_stage()

    helpers.await_queue_edit(openreview_client, 'ICLR.cc/2026/Conference/-/Rebuttal_Revision-0-1', count=1)

    invitations = openreview_client.get_invitations(invitation='ICLR.cc/2026/Conference/-/Rebuttal_Revision')
    assert len(invitations) == 10

    invitation = openreview_client.get_invitation('ICLR.cc/2026/Conference/Submission1/-/Rebuttal_Revision')
    assert 'pdf' in invitation.edit['note']['content']
    assert 'title' not in invitation.edit['note']['content']
    assert 'authors' not in invitation.edit['note']['content']
    # the revision history is visible to the readers of the submission
    assert invitation.edit['readers'] == ['${{2/note/id}/readers}']

    # author uploads a new PDF
    revision_edit = test_client.post_note_edit(
        invitation='ICLR.cc/2026/Conference/Submission1/-/Rebuttal_Revision',
        signatures=['ICLR.cc/2026/Conference/Submission1/Authors'],
        note=openreview.api.Note(
            content={
                'pdf': { 'value': '/pdf/' + 'q' * 40 +'.pdf' }
            }
        ))
    helpers.await_queue_edit(openreview_client, edit_id=revision_edit['id'])

    submission = openreview_client.get_notes(invitation='ICLR.cc/2026/Conference/-/Submission', sort='number:asc')[0]
    assert submission.content['pdf']['value'] == '/pdf/' + 'q' * 40 +'.pdf'

    # a reviewer can see the revision to compare the different versions
    reviewer_client = openreview.api.OpenReviewClient(username='reviewer_one@iclr.cc', password=helpers.strong_password)
    revision_edits = reviewer_client.get_note_edits(note_id=submission.id, invitation='ICLR.cc/2026/Conference/Submission1/-/Rebuttal_Revision')
    assert len(revision_edits) == 1

def test_rebuttal_stage(client, openreview_client, helpers):

    pc_client=openreview.api.OpenReviewClient(username='programchair@iclr.cc', password=helpers.strong_password)
    assert pc_client.get_invitation('ICLR.cc/2026/Conference/-/Author_Rebuttal')
    assert pc_client.get_invitation('ICLR.cc/2026/Conference/-/Author_Rebuttal/Dates')
    assert pc_client.get_invitation('ICLR.cc/2026/Conference/-/Author_Rebuttal/Form_Fields')
    assert pc_client.get_invitation('ICLR.cc/2026/Conference/-/Author_Rebuttal/Readers')

    # create child invitations
    now = datetime.datetime.now()
    new_cdate = openreview.tools.datetime_millis(now)
    new_duedate = openreview.tools.datetime_millis(now + datetime.timedelta(days=4))

    pc_client.post_invitation_edit(
        invitations='ICLR.cc/2026/Conference/-/Author_Rebuttal/Dates',
        content={
            'activation_date': { 'value': new_cdate },
            'due_date': { 'value': new_duedate },
            'expiration_date': { 'value': new_duedate }
        }
    )
    helpers.await_queue_edit(openreview_client, edit_id='ICLR.cc/2026/Conference/-/Author_Rebuttal-0-1', count=2)

    invitations = openreview_client.get_invitations(invitation='ICLR.cc/2026/Conference/-/Author_Rebuttal')
    assert len(invitations) == 10

    invitation  = openreview_client.get_invitation('ICLR.cc/2026/Conference/Submission1/-/Author_Rebuttal')
    assert invitation.invitees == [
        'ICLR.cc/2026/Conference',
        'ICLR.cc/2026/Conference/Submission1/Authors'
    ]

    assert invitation and invitation.edit['readers'] == [
        'ICLR.cc/2026/Conference/Program_Chairs',
        'ICLR.cc/2026/Conference/Submission1/Senior_Area_Chairs',
        'ICLR.cc/2026/Conference/Submission1/Area_Chairs',
        'ICLR.cc/2026/Conference/Submission1/Reviewers',
        'ICLR.cc/2026/Conference/Submission1/Authors'
    ]

def test_metareview_stage(client, openreview_client, helpers):

    pc_client=openreview.api.OpenReviewClient(username='programchair@iclr.cc', password=helpers.strong_password)
    metareview_inv = pc_client.get_invitation('ICLR.cc/2026/Conference/-/Meta_Review')
    assert metareview_inv
    assert pc_client.get_invitation('ICLR.cc/2026/Conference/-/Meta_Review/Dates')
    assert pc_client.get_invitation('ICLR.cc/2026/Conference/-/Meta_Review/Form_Fields')
    assert pc_client.get_invitation('ICLR.cc/2026/Conference/-/Meta_Review/Readers')
    content = metareview_inv.edit['invitation']['edit']['note']['content']
    assert all(field in content for field in ['metareview', 'recommendation', 'confidence'])

    assert pc_client.get_invitation('ICLR.cc/2026/Conference/-/Meta_Review_SAC_Revision/Dates')
    assert pc_client.get_invitation('ICLR.cc/2026/Conference/-/Meta_Review_SAC_Revision/Form_Fields')

    metareview_sac_revision_inv = pc_client.get_invitation('ICLR.cc/2026/Conference/-/Meta_Review_SAC_Revision')
    assert metareview_sac_revision_inv
    assert pc_client.get_invitation('ICLR.cc/2026/Conference/-/Meta_Review_SAC_Revision/Dates')
    content = metareview_sac_revision_inv.edit['invitation']['edit']['note']['content']
    assert all(field in content for field in ['metareview', 'recommendation', 'confidence'])

    metareview_content = {
        "final_metareview": {
            "order": 1,
            "description": "Please provide an evaluation of the quality, clarity, originality and significance of this work, including a list of its pros and cons. Your comment or reply (max 5000 characters). Add formatting using Markdown and formulas using LaTeX. For more information see https://openreview.net/faq",
            "value": {
              "param": {
                "type": "string",
                "maxLength": 5000,
                "markdown": True,
                "input": "textarea"
              }
            }
        },
        "final_recommendation": {
            "order": 2,
            "value": {
                "param": {
                "type": "string",
                "enum": [
                    "Accept (Oral)",
                    "Accept (Poster)",
                    "Reject"
                ],
                "input": "radio"
                }
            }
        },
        "final_confidence": {
            "order": 3,
            "value": {
                "param": {
                "type": "integer",
                "enum": [
                    {
                    "value": 5,
                    "description": "5: The area chair is absolutely certain"
                    },
                    {
                    "value": 4,
                    "description": "4: The area chair is confident but not absolutely certain"
                    },
                    {
                    "value": 3,
                    "description": "3: The area chair is somewhat confident"
                    },
                    {
                    "value": 2,
                    "description": "2: The area chair is not sure"
                    },
                    {
                    "value": 1,
                    "description": "1: The area chair's evaluation is an educated guess"
                    }
                ],
                "input": "radio"
                }
            }
        },
        'metareview': {
            'delete': True
        },
        'recommendation': {
            'delete': True
        },
        'confidence': {
            'delete': True
        }
    }

    # edit the metareview form
    pc_client.post_invitation_edit(
        invitations='ICLR.cc/2026/Conference/-/Meta_Review/Form_Fields',
        content = {
            'content': {
                'value': metareview_content
            },
            'recommendation_field_name': {
                'value': 'final_recommendation'
            }
        }
    )
    helpers.await_queue_edit(openreview_client, edit_id='ICLR.cc/2026/Conference/-/Meta_Review-0-1', count=2)

    # create child invitations
    now = datetime.datetime.now()
    new_cdate = openreview.tools.datetime_millis(now)
    new_duedate = openreview.tools.datetime_millis(now + datetime.timedelta(days=4))

    pc_client.post_invitation_edit(
        invitations='ICLR.cc/2026/Conference/-/Meta_Review/Dates',
        content={
            'activation_date': { 'value': new_cdate },
            'due_date': { 'value': new_duedate },
            'expiration_date': { 'value': new_duedate }
        }
    )
    helpers.await_queue_edit(openreview_client, edit_id='ICLR.cc/2026/Conference/-/Meta_Review-0-1', count=3)

    invitations = openreview_client.get_invitations(invitation='ICLR.cc/2026/Conference/-/Meta_Review')
    assert len(invitations) == 10

    invitation  = openreview_client.get_invitation('ICLR.cc/2026/Conference/Submission1/-/Meta_Review')
    assert invitation.invitees == [
        'ICLR.cc/2026/Conference',
        'ICLR.cc/2026/Conference/Submission1/Area_Chairs'
    ]

    assert invitation and invitation.edit['readers'] == [
        'ICLR.cc/2026/Conference/Submission1/Senior_Area_Chairs',
        'ICLR.cc/2026/Conference/Submission1/Area_Chairs',
        'ICLR.cc/2026/Conference/Program_Chairs'
    ]
    assert all(field in invitation.edit['note']['content'] for field in ['final_metareview', 'final_recommendation', 'final_confidence'])
    assert not all (field in invitation.edit['note']['content'] for field in ['metareview', 'recommendation', 'confidence'])

    # assert meta review revision invitation is edited with metareview fields
    meta_review_revision_inv = openreview_client.get_invitation('ICLR.cc/2026/Conference/-/Meta_Review_SAC_Revision')
    content = meta_review_revision_inv.edit['invitation']['edit']['note']['content']
    assert all(field in content for field in ['final_metareview', 'final_recommendation', 'final_confidence'])
    assert not all (field in content for field in ['metareview', 'recommendation', 'confidence'])

    assert pc_client.get_invitation('ICLR.cc/2026/Conference/-/Meta_Review_Release')
    assert pc_client.get_invitation('ICLR.cc/2026/Conference/-/Meta_Review_Release/Dates')
    assert pc_client.get_invitation('ICLR.cc/2026/Conference/-/Meta_Review_Release/Readers')

    # allow PC to directly edit metareview revision invitation content
    pc_client.post_invitation_edit(
        invitations='ICLR.cc/2026/Conference/-/Meta_Review_SAC_Revision/Form_Fields',
        content = {
            'content': {
                'value': {
                    "private_comment_to_PCs": {
                        "order": 10,
                        "value": {
                            "param": {
                                "type": "string",
                                "maxLength": 5000,
                                "markdown": True,
                                "input": "textarea"
                            }
                        },
                        "readers": [
                            "ICLR.cc/2026/Conference/Program_Chairs",
                            "ICLR.cc/2026/Conference/Submission${7/content/noteNumber/value}/Senior_Area_Chairs"
                        ]
                    }
                }
            }
        }
    )
    helpers.await_queue_edit(openreview_client, edit_id='ICLR.cc/2026/Conference/-/Meta_Review_SAC_Revision-0-1', count=3)

    # assert metareview revision invitation has metareview fields plus the new private comment field
    meta_review_revision_inv = openreview_client.get_invitation('ICLR.cc/2026/Conference/-/Meta_Review_SAC_Revision')
    content = meta_review_revision_inv.edit['invitation']['edit']['note']['content']
    assert all(field in content for field in ['final_metareview', 'final_recommendation', 'final_confidence', 'private_comment_to_PCs'])
    assert not all (field in content for field in ['metareview', 'recommendation', 'confidence'])

    meta_review_release_inv = openreview.tools.get_invitation(openreview_client, 'ICLR.cc/2026/Conference/-/Meta_Review_Release')
    assert meta_review_release_inv.edit['invitation']['edit']['invitation']['edit']['note']['readers'] == [
        'ICLR.cc/2026/Conference/Program_Chairs',
        'ICLR.cc/2026/Conference/Submission${5/content/noteNumber/value}/Senior_Area_Chairs',
        'ICLR.cc/2026/Conference/Submission${5/content/noteNumber/value}/Area_Chairs',
        'ICLR.cc/2026/Conference/Submission${5/content/noteNumber/value}/Reviewers',
        'ICLR.cc/2026/Conference/Submission${5/content/noteNumber/value}/Authors'
    ]

def test_decision_stage(client, openreview_client, helpers):

    pc_client = openreview.api.OpenReviewClient(username='programchair@iclr.cc', password=helpers.strong_password)

    invitation = pc_client.get_invitation('ICLR.cc/2026/Conference/-/Decision')
    assert invitation
    assert pc_client.get_invitation('ICLR.cc/2026/Conference/-/Decision/Dates')
    assert pc_client.get_invitation('ICLR.cc/2026/Conference/-/Decision/Readers')
    assert pc_client.get_invitation('ICLR.cc/2026/Conference/-/Decision/Decision_Options')
    assert pc_client.get_invitation('ICLR.cc/2026/Conference/-/Decision_Upload')
    assert pc_client.get_invitation('ICLR.cc/2026/Conference/-/Decision_Upload/Decision_CSV')

    # create child invitations
    now = datetime.datetime.now()
    new_cdate = openreview.tools.datetime_millis(now)
    new_duedate = openreview.tools.datetime_millis(now + datetime.timedelta(days=4))

    pc_client.post_invitation_edit(
        invitations='ICLR.cc/2026/Conference/-/Decision/Dates',
        content={
            'activation_date': { 'value': new_cdate },
            'due_date': { 'value': new_duedate },
            'expiration_date': { 'value': new_duedate }
        }
    )
    helpers.await_queue_edit(openreview_client, edit_id='ICLR.cc/2026/Conference/-/Decision-0-1', count=2)

    invitations = openreview_client.get_invitations(invitation='ICLR.cc/2026/Conference/-/Decision')
    assert len(invitations) == 10

    invitation = openreview_client.get_invitation('ICLR.cc/2026/Conference/Submission1/-/Decision')

    assert invitation and invitation.edit['readers'] == [
        'ICLR.cc/2026/Conference/Program_Chairs'
    ]

    invitation = openreview_client.get_invitation('ICLR.cc/2026/Conference/-/Decision/Readers')
    reader_values = [item['value'] for item in invitation.edit['content']['readers']['value']['param']['items']]
    assert 'ICLR.cc/2026/Conference/Senior_Area_Chairs' in reader_values
    assert 'ICLR.cc/2026/Conference/Submission${5/content/noteNumber/value}/Senior_Area_Chairs' in reader_values

    # upload decisions using a CSV file
    submissions = openreview_client.get_notes(invitation='ICLR.cc/2026/Conference/-/Submission', sort='number:asc')

    decisions = ['Accept (Oral)', 'Accept (Poster)', 'Reject']
    comment = {
        'Accept (Oral)': 'Congratulations on your oral acceptance.',
        'Accept (Poster)': 'Congratulations on your poster acceptance.',
        'Reject': 'We regret to inform you...'
    }

    with open(os.path.join(os.path.dirname(__file__), 'data/ICLR_2026_decisions.csv'), 'w') as file_handle:
        writer = csv.writer(file_handle)
        writer.writerow([submissions[0].number, 'Accept (Oral)', comment['Accept (Oral)']])
        writer.writerow([submissions[1].number, 'Accept (Poster)', comment['Accept (Poster)']])
        writer.writerow([submissions[2].number, 'Reject', comment['Reject']])
        for submission in submissions[3:]:
            decision = random.choice(decisions)
            writer.writerow([submission.number, decision, comment[decision]])

    url = pc_client.put_attachment(os.path.join(os.path.dirname(__file__), 'data/ICLR_2026_decisions.csv'),
                                     'ICLR.cc/2026/Conference/-/Decision_Upload/Decision_CSV', 'decision_CSV')

    pc_client.post_invitation_edit(
        invitations='ICLR.cc/2026/Conference/-/Decision_Upload/Decision_CSV',
        content={
            'decision_CSV': { 'value': url }
        }
    )
    helpers.await_queue_edit(openreview_client, edit_id='ICLR.cc/2026/Conference/-/Decision_Upload-0-1', count=2)

    # trigger decision upload process
    now = datetime.datetime.now()
    pc_client.post_invitation_edit(
        invitations='ICLR.cc/2026/Conference/-/Decision_Upload/Dates',
        content={
            'activation_date': { 'value': openreview.tools.datetime_millis(now) }
        }
    )
    helpers.await_queue_edit(openreview_client, edit_id='ICLR.cc/2026/Conference/-/Decision_Upload-0-1', count=3)

    helpers.await_queue_edit(openreview_client, invitation='ICLR.cc/2026/Conference/Submission1/-/Decision')

    decision_note = openreview_client.get_notes(invitation='ICLR.cc/2026/Conference/Submission1/-/Decision')[0]
    assert decision_note and decision_note.content['decision']['value'] == 'Accept (Oral)'
    assert decision_note.readers == ['ICLR.cc/2026/Conference/Program_Chairs']
    assert decision_note.nonreaders == ['ICLR.cc/2026/Conference/Submission1/Authors']

def test_decision_release_stage(client, openreview_client, helpers):

    pc_client = openreview.api.OpenReviewClient(username='programchair@iclr.cc', password=helpers.strong_password)
    assert pc_client.get_invitation('ICLR.cc/2026/Conference/-/Decision_Release')
    assert pc_client.get_invitation('ICLR.cc/2026/Conference/-/Decision_Release/Dates')
    assert pc_client.get_invitation('ICLR.cc/2026/Conference/-/Decision_Release/Readers')

    decision_release_inv = openreview.tools.get_invitation(openreview_client, 'ICLR.cc/2026/Conference/-/Decision_Release')
    assert decision_release_inv.edit['invitation']['edit']['invitation']['edit']['note']['readers'] == [
        'ICLR.cc/2026/Conference/Program_Chairs',
        'ICLR.cc/2026/Conference/Submission${5/content/noteNumber/value}/Senior_Area_Chairs',
        'ICLR.cc/2026/Conference/Submission${5/content/noteNumber/value}/Area_Chairs',
        'ICLR.cc/2026/Conference/Submission${5/content/noteNumber/value}/Reviewers',
        'ICLR.cc/2026/Conference/Submission${5/content/noteNumber/value}/Authors'
    ]
    assert decision_release_inv.edit['invitation']['edit']['invitation']['edit']['note']['nonreaders'] == []

    # release decisions to the paper committees and authors
    now = datetime.datetime.now()
    pc_client.post_invitation_edit(
        invitations='ICLR.cc/2026/Conference/-/Decision_Release/Dates',
        content={
            'activation_date': { 'value': openreview.tools.datetime_millis(now) }
        }
    )
    helpers.await_queue_edit(openreview_client, edit_id='ICLR.cc/2026/Conference/-/Decision_Release-0-1', count=2)
    helpers.await_queue_edit(openreview_client, edit_id='ICLR.cc/2026/Conference/-/Decision-0-1', count=3)

    decisions = openreview_client.get_notes(invitation='ICLR.cc/2026/Conference/Submission1/-/Decision')
    assert len(decisions) == 1
    assert decisions[0].readers == [
        'ICLR.cc/2026/Conference/Program_Chairs',
        'ICLR.cc/2026/Conference/Submission1/Senior_Area_Chairs',
        'ICLR.cc/2026/Conference/Submission1/Area_Chairs',
        'ICLR.cc/2026/Conference/Submission1/Reviewers',
        'ICLR.cc/2026/Conference/Submission1/Authors'
    ]
    assert decisions[0].nonreaders == []

def test_author_decision_notification(client, openreview_client, helpers):

    pc_client = openreview.api.OpenReviewClient(username='programchair@iclr.cc', password=helpers.strong_password)

    assert pc_client.get_invitation('ICLR.cc/2026/Conference/-/Author_Decision_Notification')
    assert pc_client.get_invitation('ICLR.cc/2026/Conference/-/Author_Decision_Notification/Dates')
    assert pc_client.get_invitation('ICLR.cc/2026/Conference/-/Author_Decision_Notification/Fields_to_Include')
    assert pc_client.get_invitation('ICLR.cc/2026/Conference/-/Author_Decision_Notification/Message')

    # select the decision fields to include in the email
    pc_client.post_invitation_edit(
        invitations='ICLR.cc/2026/Conference/-/Author_Decision_Notification/Fields_to_Include',
        content={
            'fields_to_include': { 'value': ['decision', 'comment'] }
        }
    )
    helpers.await_queue_edit(openreview_client, edit_id='ICLR.cc/2026/Conference/-/Author_Decision_Notification-0-1', count=2)

    # trigger the notification process
    now = datetime.datetime.now()
    pc_client.post_invitation_edit(
        invitations='ICLR.cc/2026/Conference/-/Author_Decision_Notification/Dates',
        content={
            'activation_date': { 'value': openreview.tools.datetime_millis(now) }
        }
    )
    helpers.await_queue_edit(openreview_client, edit_id='ICLR.cc/2026/Conference/-/Author_Decision_Notification-0-1', count=3)

    # all the submissions have a decision, the authors of each submission are notified
    messages = openreview_client.get_messages(to='test@mail.com', subject='[ICLR 2026] The decision for your submission.*')
    assert len(messages) == 10

def test_camera_ready_revision_stage(client, openreview_client, helpers, test_client):

    pc_client = openreview.api.OpenReviewClient(username='programchair@iclr.cc', password=helpers.strong_password)
    test_client = openreview.api.OpenReviewClient(token=test_client.token)

    assert pc_client.get_invitation('ICLR.cc/2026/Conference/-/Camera_Ready_Revision')
    assert pc_client.get_invitation('ICLR.cc/2026/Conference/-/Camera_Ready_Revision/Dates')
    assert pc_client.get_invitation('ICLR.cc/2026/Conference/-/Camera_Ready_Revision/Form_Fields')

    # create child invitations for accepted submissions only
    now = datetime.datetime.now()
    new_cdate = openreview.tools.datetime_millis(now)
    new_duedate = openreview.tools.datetime_millis(now + datetime.timedelta(days=5))

    pc_client.post_invitation_edit(
        invitations='ICLR.cc/2026/Conference/-/Camera_Ready_Revision/Dates',
        content={
            'activation_date': { 'value': new_cdate },
            'due_date': { 'value': new_duedate },
            'expiration_date': { 'value': new_duedate }
        }
    )
    helpers.await_queue_edit(openreview_client, edit_id='ICLR.cc/2026/Conference/-/Camera_Ready_Revision-0-1', count=2)

    submissions = openreview_client.get_notes(invitation='ICLR.cc/2026/Conference/-/Submission', sort='number:asc')
    accepted_numbers = []
    for submission in submissions:
        decision = openreview_client.get_notes(invitation=f'ICLR.cc/2026/Conference/Submission{submission.number}/-/Decision')[0]
        if 'Accept' in decision.content['decision']['value']:
            accepted_numbers.append(submission.number)

    invitations = openreview_client.get_invitations(invitation='ICLR.cc/2026/Conference/-/Camera_Ready_Revision')
    assert len(invitations) == len(accepted_numbers)
    assert openreview.tools.get_invitation(openreview_client, 'ICLR.cc/2026/Conference/Submission3/-/Camera_Ready_Revision') is None

    invitation = openreview_client.get_invitation('ICLR.cc/2026/Conference/Submission1/-/Camera_Ready_Revision')
    assert invitation.invitees == [
        'ICLR.cc/2026/Conference',
        'ICLR.cc/2026/Conference/Submission1/Authors'
    ]

    # author posts a camera-ready revision
    submission = submissions[0]
    revision_edit = test_client.post_note_edit(
        invitation='ICLR.cc/2026/Conference/Submission1/-/Camera_Ready_Revision',
        signatures=['ICLR.cc/2026/Conference/Submission1/Authors'],
        note=openreview.api.Note(
            content={
                'title': { 'value': submission.content['title']['value'] },
                'abstract': { 'value': submission.content['abstract']['value'] + ' camera ready' },
                'authors': { 'value': submission.content['authors']['value'] },
                'keywords': { 'value': submission.content['keywords']['value'] },
                'pdf': { 'value': submission.content['pdf']['value'] },
            }
        ))
    helpers.await_queue_edit(openreview_client, edit_id=revision_edit['id'])

    submission = openreview_client.get_notes(invitation='ICLR.cc/2026/Conference/-/Submission', sort='number:asc')[0]
    assert submission.content['abstract']['value'].endswith('camera ready')

def test_release_submissions(client, openreview_client, helpers):

    pc_client = openreview.api.OpenReviewClient(username='programchair@iclr.cc', password=helpers.strong_password)

    submissions = openreview_client.get_notes(invitation='ICLR.cc/2026/Conference/-/Submission', sort='number:asc')
    assert submissions[0].readers == ['everyone']
    assert not submissions[0].pdate
    assert submissions[0].content['authors']['readers'] == [
        'ICLR.cc/2026/Conference',
        'ICLR.cc/2026/Conference/Submission1/Authors'
    ]
    assert submissions[0].content['venueid']['value'] == 'ICLR.cc/2026/Conference/Submission'

    assert pc_client.get_invitation('ICLR.cc/2026/Conference/-/Accepted_Submission_Release')
    assert pc_client.get_invitation('ICLR.cc/2026/Conference/-/Rejected_Submission_Release')
    assert pc_client.get_invitation('ICLR.cc/2026/Conference/-/Accepted_Submission_Release/Dates')
    assert pc_client.get_invitation('ICLR.cc/2026/Conference/-/Rejected_Submission_Release/Dates')

    # release accepted submissions to the public revealing the author identities
    pc_client.post_invitation_edit(
        invitations='ICLR.cc/2026/Conference/-/Accepted_Submission_Release/Readers',
        content={
            'readers': {
                'value': ['everyone']
            },
            'reveal_author_identities': {
                'value': True
            }
        }
    )
    helpers.await_queue_edit(openreview_client, edit_id='ICLR.cc/2026/Conference/-/Accepted_Submission_Release-0-1', count=2)

    # release rejected submissions to the public keeping the authors anonymous
    pc_client.post_invitation_edit(
        invitations='ICLR.cc/2026/Conference/-/Rejected_Submission_Release/Readers',
        content={
            'readers': {
                'value': ['everyone']
            },
            'reveal_author_identities': {
                'value': False
            }
        }
    )
    helpers.await_queue_edit(openreview_client, edit_id='ICLR.cc/2026/Conference/-/Rejected_Submission_Release-0-1', count=2)

    now = datetime.datetime.now()
    new_cdate = openreview.tools.datetime_millis(now)

    # trigger the submission release processes
    pc_client.post_invitation_edit(
        invitations='ICLR.cc/2026/Conference/-/Accepted_Submission_Release/Dates',
        content={
            'activation_date': { 'value': new_cdate }
        }
    )
    helpers.await_queue_edit(openreview_client, edit_id='ICLR.cc/2026/Conference/-/Accepted_Submission_Release-0-1', count=3)

    pc_client.post_invitation_edit(
        invitations='ICLR.cc/2026/Conference/-/Rejected_Submission_Release/Dates',
        content={
            'activation_date': { 'value': new_cdate }
        }
    )
    helpers.await_queue_edit(openreview_client, edit_id='ICLR.cc/2026/Conference/-/Rejected_Submission_Release-0-1', count=3)

    submissions = openreview_client.get_notes(invitation='ICLR.cc/2026/Conference/-/Submission', sort='number:asc')

    # accepted submission: authors are revealed and the paper is published
    assert submissions[0].readers == ['everyone']
    assert submissions[0].pdate
    assert 'readers' not in submissions[0].content['authors']
    assert submissions[0].content['venueid']['value'] == 'ICLR.cc/2026/Conference'
    assert submissions[0].content['venue']['value'] == 'ICLR 2026 Oral'
    year = datetime.datetime.now().year
    valid_bibtex = '''@inproceedings{
user'''+str(year)+'''paper,
title={Paper title 1 license revision},
author={SomeFirstName User and Eddie Amazon and SAE ICLROne},
booktitle={International Conference on Learning Representations},
year={'''+str(year)+'''},
url={https://openreview.net/forum?id='''

    valid_bibtex = valid_bibtex + submissions[0].forum + '''}
}'''
    assert submissions[0].content['_bibtex']['value'] == valid_bibtex

    assert submissions[1].readers == ['everyone']
    assert submissions[1].pdate
    assert 'readers' not in submissions[1].content['authors']
    assert submissions[1].content['venueid']['value'] == 'ICLR.cc/2026/Conference'
    assert submissions[1].content['venue']['value'] == 'ICLR 2026 Poster'

    # rejected submission: authors stay anonymous
    assert submissions[2].readers == ['everyone']
    assert submissions[2].odate
    assert not submissions[2].pdate
    assert submissions[2].content['authors']['readers'] == [
        'ICLR.cc/2026/Conference',
        'ICLR.cc/2026/Conference/Submission3/Authors'
    ]
    assert submissions[2].content['venueid']['value'] == 'ICLR.cc/2026/Conference/Rejected_Submission'
    assert submissions[2].content['venue']['value'] == 'Submitted to ICLR 2026'
    valid_bibtex = '''@misc{
anonymous'''+str(year)+'''paper,
title={Paper title 3},
author={Anonymous},
year={'''+str(year)+'''},
url={https://openreview.net/forum?id='''

    valid_bibtex = valid_bibtex + submissions[2].forum + '''}
}'''
    assert submissions[2].content['_bibtex']['value'] == valid_bibtex