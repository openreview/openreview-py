import pytest
import datetime
import openreview
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

        group = openreview.tools.get_group(openreview_client, 'ICLR.cc/2026/Conference/Reviewers')
        assert group.domain == 'ICLR.cc/2026/Conference'
        assert group.readers == [
            'ICLR.cc/2026/Conference',
            'ICLR.cc/2026/Conference/Reviewers',
            'ICLR.cc/2026/Conference/Senior_Action_Editors',
            'ICLR.cc/2026/Conference/Action_Editors'
        ]

        group = openreview.tools.get_group(openreview_client, 'ICLR.cc/2026/Conference/Action_Editors')
        assert group.readers == [
            'ICLR.cc/2026/Conference',
            'ICLR.cc/2026/Conference/Action_Editors',
            'ICLR.cc/2026/Conference/Senior_Action_Editors'
        ]

        group = openreview.tools.get_group(openreview_client, 'ICLR.cc/2026/Conference/Senior_Action_Editors')
        assert group.readers == [
            'ICLR.cc/2026/Conference',
            'ICLR.cc/2026/Conference/Senior_Action_Editors'
        ]

        group = openreview.tools.get_group(openreview_client, 'ICLR.cc/2026/Conference/Senior_Action_Editors/Invited')
        assert group.readers == [
            'ICLR.cc/2026/Conference',
            'ICLR.cc/2026/Conference/Senior_Action_Editors/Invited'
        ]

        group = openreview.tools.get_group(openreview_client, 'ICLR.cc/2026/Conference/Senior_Action_Editors/Declined')
        assert group.readers == [
            'ICLR.cc/2026/Conference',
            'ICLR.cc/2026/Conference/Senior_Action_Editors/Declined'
        ]

        domain_content = openreview.tools.get_group(openreview_client, 'ICLR.cc/2026/Conference').content
        assert domain_content['senior_area_chair_roles']['value'] == ['Senior_Action_Editors']
        assert domain_content['senior_area_chairs_id']['value'] == 'ICLR.cc/2026/Conference/Senior_Action_Editors'
        assert domain_content['senior_area_chairs_assignment_id']['value'] == 'ICLR.cc/2026/Conference/Senior_Action_Editors/-/Assignment'
        assert domain_content['senior_area_chairs_affinity_score_id']['value'] == 'ICLR.cc/2026/Conference/Senior_Action_Editors/-/Affinity_Score'
        assert domain_content['senior_area_chairs_name']['value'] == 'Senior_Action_Editors'
        assert domain_content['sac_paper_assignments']['value'] == False
        assert domain_content['senior_area_chairs_conflict_id']['value'] == 'ICLR.cc/2026/Conference/Senior_Action_Editors/-/Conflict'

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
                'due_date': { 'value': openreview.tools.datetime_millis(now - datetime.timedelta(hours=5)) }
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
        assert submissions[0].odate
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
        # make sure pdfs remain hidden
        content = full_submission_inv.edit['invitation']['edit']['note']['content']
        content['pdf']['readers'] = [
            'ICLR.cc/2026/Conference',
            'ICLR.cc/2026/Conference/Submission1/Authors'
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
        assert 'readers' in submission.content['pdf'] and submission.content['pdf']['readers'] == ['ICLR.cc/2026/Conference', f'ICLR.cc/2026/Conference/Submission{submission.number}/Authors']
        assert 'readers' in submission.content['authors'] and submission.content['authors']['readers'] == ['ICLR.cc/2026/Conference', f'ICLR.cc/2026/Conference/Submission{submission.number}/Authors']
        assert 'readers' in submission.content['authorids'] and submission.content['authorids']['readers'] == ['ICLR.cc/2026/Conference', f'ICLR.cc/2026/Conference/Submission{submission.number}/Authors']
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
        assert openreview_client.get_invitation('ICLR.cc/2026/Conference/Senior_Action_Editors/-/Affinity_Score')
        assert openreview_client.get_invitation('ICLR.cc/2026/Conference/Senior_Action_Editors/-/Affinity_Score/Model')
        assert openreview_client.get_invitation('ICLR.cc/2026/Conference/Senior_Action_Editors/-/Affinity_Score/Dates')
        assert not openreview.tools.get_invitation(openreview_client, 'ICLR.cc/2026/Conference/Senior_Action_Editors/-/Conflict')
        inv = openreview_client.get_invitation('ICLR.cc/2026/Conference/Senior_Action_Editors/-/Assignment_Configuration')
        assert inv and inv.content['committee_name']['value'] == 'Senior_Action_Editors'
        assert inv.edit['note']['content']['paper_invitation']['value']['param']['default'] == 'ICLR.cc/2026/Conference/Action_Editors'
        assert inv.edit['note']['content']['match_group']['value']['param']['default'] == 'ICLR.cc/2026/Conference/Senior_Action_Editors'

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

def test_sac_deployment(client, openreview_client, helpers):

    pc_client=openreview.api.OpenReviewClient(username='programchair@iclr.cc', password=helpers.strong_password)

    inv = openreview_client.get_invitation('ICLR.cc/2026/Conference/Senior_Action_Editors/-/Assignment')
    assert inv and inv.content['committee_role']['value'] == 'senior_area_chairs'
    assert inv.edit['head']['param']['inGroup'] == 'ICLR.cc/2026/Conference/Action_Editors'
    assert inv.edit['tail']['param']['options']['group'] == 'ICLR.cc/2026/Conference/Senior_Action_Editors'
    assert openreview_client.get_invitation('ICLR.cc/2026/Conference/Senior_Action_Editors/-/Assignment/Dates')
    assert openreview_client.get_invitation('ICLR.cc/2026/Conference/Senior_Action_Editors/-/Proposed_Assignment')
    assert openreview_client.get_invitation('ICLR.cc/2026/Conference/Senior_Action_Editors/-/Aggregate_Score')
    assert openreview_client.get_invitation('ICLR.cc/2026/Conference/Senior_Action_Editors/-/Custom_Max_Papers')
    assert openreview_client.get_invitation('ICLR.cc/2026/Conference/Senior_Action_Editors/-/Custom_User_Demands')
    assert openreview_client.get_invitation('ICLR.cc/2026/Conference/Senior_Action_Editors/-/Assignment_Configuration')
    assert openreview_client.get_invitation('ICLR.cc/2026/Conference/-/Senior_Action_Editors_Assignment_Deployment')
    assert openreview_client.get_invitation('ICLR.cc/2026/Conference/-/Senior_Action_Editors_Assignment_Deployment/Dates')
    assert openreview_client.get_invitation('ICLR.cc/2026/Conference/-/Senior_Action_Editors_Assignment_Deployment/Match')

    #submit Assignment_Configuration
    config_note = openreview_client.post_note_edit(
        invitation='ICLR.cc/2026/Conference/Senior_Action_Editors/-/Assignment_Configuration',
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
                'paper_invitation': { 'value': 'ICLR.cc/2026/Conference/Action_Editors' },
                'match_group': { 'value': 'ICLR.cc/2026/Conference/Senior_Action_Editors' },
                'scores_specification': {
                    'value': {
                        'ICLR.cc/2026/Conference/Senior_Action_Editors/-/Affinity_Score': {
                            'weight': 1,
                            'default': 0
                        },
                        'ICLR.cc/2026/Conference/Senior_Action_Editors/-/Bid': {
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
                'aggregate_score_invitation': { 'value': 'ICLR.cc/2026/Conference/Senior_Action_Editors/-/Aggregate_Score'},
                'conflicts_invitation': { 'value': 'ICLR.cc/2026/Conference/Senior_Action_Editors/-/Conflict'},
                'solver': { 'value': 'FairFlow'},
                'status': { 'value': 'Initialized'},
            }
        )
    )
    helpers.await_queue_edit(openreview_client, invitation=f'ICLR.cc/2026/Conference/Senior_Action_Editors/-/Assignment_Configuration')

    match_invitation = openreview_client.get_invitation('ICLR.cc/2026/Conference/-/Senior_Action_Editors_Assignment_Deployment/Match')
    assert match_invitation.edit['content']['match_name']['value']['param']['enum'] == ['sac-matching-1']

    now = datetime.datetime.now()
    now = openreview.tools.datetime_millis(now)

    # trigger deployment date process without selecting match name
    openreview_client.post_invitation_edit(
        invitations='ICLR.cc/2026/Conference/-/Senior_Action_Editors_Assignment_Deployment/Dates',
        content={
            'activation_date': { 'value': now }
        }
    )

    helpers.await_queue_edit(openreview_client,  edit_id=f'ICLR.cc/2026/Conference/-/Senior_Action_Editors_Assignment_Deployment-0-1', count=2)

    # assert status comment posted to request form
    venue = openreview_client.get_group('ICLR.cc/2026/Conference')
    notes = openreview_client.get_notes(invitation='openreview.net/Support/Venue_Request/Conference_Review_Workflow/-/Status', forum=venue.content['request_form_id']['value'], sort='number:asc')
    assert len(notes) == 1
    assert notes[-1].content['title']['value'] == 'Senior Action Editors Assignment Deployment Failed'

    # try to deploy initialized configuration and get an error
    with pytest.raises(openreview.OpenReviewException, match=r'The matching configuration with title "sac-matching-1" does not have status "Complete".'):
        pc_client.post_invitation_edit(
            invitations='ICLR.cc/2026/Conference/-/Senior_Action_Editors_Assignment_Deployment/Match',
            content = {
                'match_name': { 'value': 'sac-matching-1' }
            }
        )

    # post proposed assignments to test deployment process
    openreview_client.post_edge(openreview.api.Edge(
            invitation = 'ICLR.cc/2026/Conference/Senior_Action_Editors/-/Proposed_Assignment',
            head = '~AC_ICLROne1',
            tail = '~SAE_ICLROne1',
            signatures = ['ICLR.cc/2026/Conference/Program_Chairs'],
            weight = 1,
            label = 'sac-matching-1'
        ))

    openreview_client.post_edge(openreview.api.Edge(
                invitation = 'ICLR.cc/2026/Conference/Senior_Action_Editors/-/Proposed_Assignment',
                head = '~AC_ICLRTwo1',
                tail = '~SAE_ICLRTwo1',
                signatures = ['ICLR.cc/2026/Conference/Program_Chairs'],
                weight = 1,
                label = 'sac-matching-1'
            ))

    assert len(openreview_client.get_grouped_edges(
        invitation='ICLR.cc/2026/Conference/Senior_Action_Editors/-/Proposed_Assignment',
        groupby='id'
    )) == 2

    assert len(openreview_client.get_grouped_edges(
        invitation='ICLR.cc/2026/Conference/Senior_Action_Editors/-/Assignment',
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
        invitations='ICLR.cc/2026/Conference/-/Senior_Action_Editors_Assignment_Deployment/Match',
        content = {
            'match_name': { 'value': 'sac-matching-1' }
        }
    )
    helpers.await_queue_edit(openreview_client,  edit_id=f'ICLR.cc/2026/Conference/-/Senior_Action_Editors_Assignment_Deployment-0-1', count=3)

    grouped_edges = openreview_client.get_grouped_edges(invitation='ICLR.cc/2026/Conference/Senior_Action_Editors/-/Assignment', groupby='id')
    assert len(grouped_edges) == 2

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
        invitations='ICLR.cc/2026/Conference/Action_Editors/-/Submission_Group/Dates',
        content={
            'activation_date': { 'value': openreview.tools.datetime_millis(now - datetime.timedelta(minutes=30)) }
        }
    )

    helpers.await_queue_edit(openreview_client, edit_id='ICLR.cc/2026/Conference/Action_Editors/-/Submission_Group-0-1', count=2)

    pc_client.post_invitation_edit(
        invitations='ICLR.cc/2026/Conference/Senior_Action_Editors/-/Submission_Group/Dates',
        content={
            'activation_date': { 'value': openreview.tools.datetime_millis(now - datetime.timedelta(minutes=30)) }
        }
    )

    helpers.await_queue_edit(openreview_client, edit_id='ICLR.cc/2026/Conference/Senior_Action_Editors/-/Submission_Group-0-1', count=2)

    submission_groups = openreview_client.get_all_groups(prefix='ICLR.cc/2026/Conference/Submission')
    reviewer_groups = [group for group in submission_groups if group.id.endswith('/Reviewers')]
    assert len(reviewer_groups) == 10
    action_editor_groups = [group for group in submission_groups if group.id.endswith('/Action_Editors')]
    assert len(action_editor_groups) == 10
    senior_action_editor_groups = [group for group in submission_groups if group.id.endswith('/Senior_Action_Editors')]
    assert len(senior_action_editor_groups) == 10

    withdrawal_invitations = openreview_client.get_all_invitations(invitation='ICLR.cc/2026/Conference/-/Withdrawal')
    assert len(withdrawal_invitations) == 10

    desk_rejection_invitations = openreview_client.get_all_invitations(invitation='ICLR.cc/2026/Conference/-/Desk_Rejection')
    assert len(desk_rejection_invitations) == 10

    submissions = openreview_client.get_notes(invitation='ICLR.cc/2026/Conference/-/Submission', sort='number:asc')
    assert len(submissions) == 10
    assert submissions[0].readers == ['everyone']
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
    assert 'readers' in submission.content['authorids'] and submission.content['authorids']['readers'] == ['ICLR.cc/2026/Conference', f'ICLR.cc/2026/Conference/Submission{submission.number}/Authors']

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
        'ICLR.cc/2026/Conference/Submission1/Senior_Action_Editors', ## SACs are added by default as readers of reviews
        'ICLR.cc/2026/Conference/Submission1/Action_Editors', ## ACs are added by default as readers of reviews
        '${3/signatures}'
    ]

    assert pc_client.get_invitation('ICLR.cc/2026/Conference/-/Official_Review_Release')
    assert pc_client.get_invitation('ICLR.cc/2026/Conference/-/Official_Review_Release/Dates')
    assert pc_client.get_invitation('ICLR.cc/2026/Conference/-/Official_Review_Release/Readers')

    review_release_inv = openreview.tools.get_invitation(openreview_client, 'ICLR.cc/2026/Conference/-/Official_Review_Release')
    assert review_release_inv.edit['invitation']['edit']['invitation']['edit']['note']['readers'] == [
        'ICLR.cc/2026/Conference/Program_Chairs',
        'ICLR.cc/2026/Conference/Submission${5/content/noteNumber/value}/Senior_Action_Editors',
        'ICLR.cc/2026/Conference/Submission${5/content/noteNumber/value}/Action_Editors',
        'ICLR.cc/2026/Conference/Submission${5/content/noteNumber/value}/Reviewers',
        'ICLR.cc/2026/Conference/Submission${5/content/noteNumber/value}/Authors'
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
        'ICLR.cc/2026/Conference/Submission1/Senior_Action_Editors',
        'ICLR.cc/2026/Conference/Submission1/Action_Editors',
        'ICLR.cc/2026/Conference/Submission1/Reviewers',
        'ICLR.cc/2026/Conference/Submission1/Authors'
    ]
    assert invitation and invitation.edit['note']['readers']['param']['items'] == [
      {
        "value": "ICLR.cc/2026/Conference/Program_Chairs",
        "optional": False
      },
      {
        "value": "ICLR.cc/2026/Conference/Submission1/Senior_Action_Editors",
        "optional": False
      },
      {
        "value": "ICLR.cc/2026/Conference/Submission1/Action_Editors",
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
            "value": "ICLR.cc/2026/Conference/Submission1/Senior_Action_Editors",
            "optional": True
        },
        {
            "prefix": "ICLR.cc/2026/Conference/Submission1/Action_Editor_.*",
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
        'ICLR.cc/2026/Conference/Submission1/Senior_Action_Editors',
        'ICLR.cc/2026/Conference/Submission1/Action_Editors',
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

    assert pc_client.get_invitation('ICLR.cc/2026/Conference/-/Meta_Review_SAE_Revision/Dates')
    assert pc_client.get_invitation('ICLR.cc/2026/Conference/-/Meta_Review_SAE_Revision/Form_Fields')

    metareview_sac_revision_inv = pc_client.get_invitation('ICLR.cc/2026/Conference/-/Meta_Review_SAE_Revision')
    assert metareview_sac_revision_inv
    assert pc_client.get_invitation('ICLR.cc/2026/Conference/-/Meta_Review_SAE_Revision/Dates')
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
        'ICLR.cc/2026/Conference/Submission1/Action_Editors'
    ]

    assert invitation and invitation.edit['readers'] == [
        'ICLR.cc/2026/Conference/Submission1/Senior_Action_Editors',
        'ICLR.cc/2026/Conference/Submission1/Action_Editors',
        'ICLR.cc/2026/Conference/Program_Chairs'
    ]
    assert all(field in invitation.edit['note']['content'] for field in ['final_metareview', 'final_recommendation', 'final_confidence'])
    assert not all (field in invitation.edit['note']['content'] for field in ['metareview', 'recommendation', 'confidence'])

    # assert meta review revision invitation is edited with metareview fields
    meta_review_revision_inv = openreview_client.get_invitation('ICLR.cc/2026/Conference/-/Meta_Review_SAE_Revision')
    content = meta_review_revision_inv.edit['invitation']['edit']['note']['content']
    assert all(field in content for field in ['final_metareview', 'final_recommendation', 'final_confidence'])
    assert not all (field in content for field in ['metareview', 'recommendation', 'confidence'])

    assert pc_client.get_invitation('ICLR.cc/2026/Conference/-/Meta_Review_Release')
    assert pc_client.get_invitation('ICLR.cc/2026/Conference/-/Meta_Review_Release/Dates')
    assert pc_client.get_invitation('ICLR.cc/2026/Conference/-/Meta_Review_Release/Readers')

    # allow PC to directly edit metareview revision invitation content
    pc_client.post_invitation_edit(
        invitations='ICLR.cc/2026/Conference/-/Meta_Review_SAE_Revision/Form_Fields',
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
                            "ICLR.cc/2026/Conference/Submission${7/content/noteNumber/value}/Senior_Action_Editors"
                        ]
                    }
                }
            }
        }
    )
    helpers.await_queue_edit(openreview_client, edit_id='ICLR.cc/2026/Conference/-/Meta_Review_SAE_Revision-0-1', count=3)

    # assert metareview revision invitation has metareview fields plus the new private comment field
    meta_review_revision_inv = openreview_client.get_invitation('ICLR.cc/2026/Conference/-/Meta_Review_SAE_Revision')
    content = meta_review_revision_inv.edit['invitation']['edit']['note']['content']
    assert all(field in content for field in ['final_metareview', 'final_recommendation', 'final_confidence', 'private_comment_to_PCs'])
    assert not all (field in content for field in ['metareview', 'recommendation', 'confidence'])

    meta_review_release_inv = openreview.tools.get_invitation(openreview_client, 'ICLR.cc/2026/Conference/-/Meta_Review_Release')
    assert meta_review_release_inv.edit['invitation']['edit']['invitation']['edit']['note']['readers'] == [
        'ICLR.cc/2026/Conference/Program_Chairs',
        'ICLR.cc/2026/Conference/Submission${5/content/noteNumber/value}/Senior_Action_Editors',
        'ICLR.cc/2026/Conference/Submission${5/content/noteNumber/value}/Action_Editors',
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
    assert 'ICLR.cc/2026/Conference/Senior_Action_Editors' in reader_values
    assert 'ICLR.cc/2026/Conference/Submission${5/content/noteNumber/value}/Senior_Action_Editors' in reader_values

def test_decision_release_stage(client, openreview_client, helpers):

    pc_client = openreview.api.OpenReviewClient(username='programchair@iclr.cc', password=helpers.strong_password)
    assert pc_client.get_invitation('ICLR.cc/2026/Conference/-/Decision_Release')
    assert pc_client.get_invitation('ICLR.cc/2026/Conference/-/Decision_Release/Dates')
    assert pc_client.get_invitation('ICLR.cc/2026/Conference/-/Decision_Release/Readers')

    decision_release_inv = openreview.tools.get_invitation(openreview_client, 'ICLR.cc/2026/Conference/-/Decision_Release')
    assert decision_release_inv.edit['invitation']['edit']['invitation']['edit']['note']['readers'] == [
        'ICLR.cc/2026/Conference/Program_Chairs',
        'ICLR.cc/2026/Conference/Submission${5/content/noteNumber/value}/Senior_Action_Editors',
        'ICLR.cc/2026/Conference/Submission${5/content/noteNumber/value}/Action_Editors',
        'ICLR.cc/2026/Conference/Submission${5/content/noteNumber/value}/Reviewers',
        'ICLR.cc/2026/Conference/Submission${5/content/noteNumber/value}/Authors'
    ]
    assert decision_release_inv.edit['invitation']['edit']['invitation']['edit']['note']['nonreaders'] == []