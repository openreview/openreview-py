import csv
import os
import random
import openreview
import datetime

class TestEMNLPConference():

    def test_create_conference(self, client, openreview_client, helpers):

        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)
        first_date = now + datetime.timedelta(days=1)

        # Post the request form note
        helpers.create_user('pc@emnlp.org', 'Program', 'EMNLPChair')
        pc_client = openreview.Client(username='pc@emnlp.org', password=helpers.strong_password)

        helpers.create_user('sac@emnlp.com', 'SAC', 'EMNLPOne')
        helpers.create_user('sac2@emnlp.org', 'SAC', 'EMNLPTwo')
        helpers.create_user('ac1@emnlp.org', 'AC', 'EMNLPOne')
        helpers.create_user('ac2@emnlp.org', 'AC', 'EMNLPTwo')
        helpers.create_user('reviewer1@emnlp.org', 'Reviewer', 'EMNLPOne')
        helpers.create_user('reviewer2@emnlp.org', 'Reviewer', 'EMNLPTwo')
        helpers.create_user('reviewer3@emnlp.org', 'Reviewer', 'EMNLPThree')
        helpers.create_user('reviewer4@emnlp.com', 'Reviewer', 'EMNLPFour')
        helpers.create_user('reviewer5@emnlp.com', 'Reviewer', 'EMNLPFive')
        helpers.create_user('reviewer6@emnlp.com', 'Reviewer', 'EMNLPSix')
        helpers.create_user('ethics_chair1@google.com', 'Ethics', 'ChairOne')
        helpers.create_user('ethics_chair2@emnlp.com', 'Ethics', 'ChairTwo')
        helpers.create_user('ethics_reviewer1@emnlp.com', 'Ethics', 'ReviewerOne')
        helpers.create_user('ethics_reviewer2@emnlp.com', 'Ethics', 'ReviewerTwo')

        request_form_note = pc_client.post_note(openreview.Note(
            invitation='openreview.net/Support/-/Request_Form',
            signatures=['~Program_EMNLPChair1'],
            readers=[
                'openreview.net/Support',
                '~Program_EMNLPChair1'
            ],
            writers=[],
            content={
                'title': 'The 2023 Conference on Empirical Methods in Natural Language Processing',
                'Official Venue Name': 'The 2023 Conference on Empirical Methods in Natural Language Processing',
                'Abbreviated Venue Name': 'EMNLP 2023',
                'Official Website URL': 'https://2023.emnlp.org/',
                'program_chair_emails': ['pc@emnlp.org'],
                'contact_email': 'pc@emnlp.org',
                'publication_chairs':'No, our venue does not have Publication Chairs',
                'Area Chairs (Metareviewers)': 'Yes, our venue has Area Chairs',
                'senior_area_chairs': 'Yes, our venue has Senior Area Chairs',
                'Venue Start Date': '2023/07/01',
                'abstract_registration_deadline': first_date.strftime('%Y/%m/%d %H:%M'),
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'Location': 'Singapore',
                'submission_reviewer_assignment': 'Automatic',
                'Author and Reviewer Anonymity': 'Double-blind',
                'reviewer_identity': ['Program Chairs', 'Assigned Senior Area Chair', 'Assigned Area Chair'],
                'area_chair_identity': ['Program Chairs', 'Assigned Senior Area Chair', 'Assigned Area Chair'],
                'senior_area_chair_identity': ['Program Chairs', 'Assigned Senior Area Chair'],
                'submission_readers': 'All program committee (all reviewers, all area chairs, all senior area chairs if applicable)',
                'How did you hear about us?': 'ML conferences',
                'email_pcs_for_withdrawn_submissions': 'Yes, email PCs.',
                'email_pcs_for_desk_rejected_submissions': 'Yes, email PCs.',
                'Expected Submissions': '1000',
                'use_recruitment_template': 'Yes',
                'api_version': '2',
                'ethics_chairs_and_reviewers': 'Yes, our venue has Ethics Chairs and Reviewers'
            }))

        helpers.await_queue()

        # Post a deploy note
        client.post_note(openreview.Note(
            content={'venue_id': 'EMNLP/2023/Conference'},
            forum=request_form_note.forum,
            invitation='openreview.net/Support/-/Request{}/Deploy'.format(request_form_note.number),
            readers=['openreview.net/Support'],
            referent=request_form_note.forum,
            replyto=request_form_note.forum,
            signatures=['openreview.net/Support'],
            writers=['openreview.net/Support']
        ))

        helpers.await_queue()

        assert openreview_client.get_group('EMNLP/2023/Conference')
        assert openreview_client.get_group('EMNLP/2023/Conference/Senior_Area_Chairs')
        assert openreview_client.get_group('EMNLP/2023/Conference/Area_Chairs')
        assert openreview_client.get_group('EMNLP/2023/Conference/Reviewers')
        assert openreview_client.get_group('EMNLP/2023/Conference/Authors')

        submission_invitation = openreview_client.get_invitation('EMNLP/2023/Conference/-/Submission')
        assert submission_invitation
        assert submission_invitation.duedate

        assert openreview_client.get_invitation('EMNLP/2023/Conference/Reviewers/-/Expertise_Selection')
        assert openreview_client.get_invitation('EMNLP/2023/Conference/Area_Chairs/-/Expertise_Selection')
        assert openreview_client.get_invitation('EMNLP/2023/Conference/Senior_Area_Chairs/-/Expertise_Selection')

        revision = client.get_invitation(f'openreview.net/Support/-/Request{request_form_note.number}/Revision')
        assert 'second_deadline_additional_options' in revision.reply['content']
        assert 'second_deadline_remove_options' in revision.reply['content']

        pc_client.post_note(openreview.Note(
            invitation=f'openreview.net/Support/-/Request{request_form_note.number}/Revision',
            forum=request_form_note.id,
            readers=['EMNLP/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            referent=request_form_note.id,
            replyto=request_form_note.id,
            signatures=['~Program_EMNLPChair1'],
            writers=[],
            content={
                'title': 'The 2023 Conference on Empirical Methods in Natural Language Processing',
                'Official Venue Name': 'The 2023 Conference on Empirical Methods in Natural Language Processing',
                'Abbreviated Venue Name': 'EMNLP 2023',
                'Official Website URL': 'https://2023.emnlp.org/',
                'program_chair_emails': ['pc@emnlp.org'],
                'contact_email': 'pc@emnlp.org',
                'publication_chairs':'No, our venue does not have Publication Chairs',
                'Venue Start Date': '2023/07/01',
                'abstract_registration_deadline': first_date.strftime('%Y/%m/%d %H:%M'),
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'Location': 'Singapore',
                'submission_reviewer_assignment': 'Automatic',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '1000',
                'use_recruitment_template': 'Yes',
                'Additional Submission Options': {
                    "supplementary_materials": {
                        "value": {
                            "param": {
                                "type": "file",
                                "optional": True,
                                "extensions": [
                                    "tgz",
                                    "zip"
                                ],
                                "maxSize": 100
                            }
                        },
                        "description": "Each submission can optionally be accompanied by a single .tgz or .zip archive containing software, and/or a single .tgz or .zip archive containing data. EMNLP 2023 encourages the submission of these supplementary materials to improve the reproducibility of results and to enable authors to provide additional information that does not fit in the paper. All supplementary materials must be properly anonymized.",
                        "order": 9
                    }
                },
                'remove_submission_options': ['TL;DR', 'pdf'],
                'second_deadline_additional_options': {
                    'pdf': {
                        'order': 7,
                        'description': 'Upload a PDF file that ends with .pdf.',
                        'value': {
                            'param': {
                                'type': 'file',
                                'maxSize': 50,
                                'extensions': ['pdf']
                            }
                        }
                    },
                    "submission_type": {
                        "value": {
                            "param": {
                                "type": "string",
                                "enum": [
                                    "Regular Long Paper",
                                    "Regular Short Paper"
                                ],
                                "input": "select"
                            }
                        },
                        "description": "Please enter the category under which the submission should be reviewed. This cannot be changed after the abstract submission deadline.",
                        "order": 1
                    },
                    "supplementary_materials": {
                        "value": {
                            "param": {
                                "type": "file",
                                "extensions": [
                                    "tgz",
                                    "zip"
                                ],
                                "maxSize": 100
                            }
                        },
                        "description": "Each submission can optionally be accompanied by a single .tgz or .zip archive containing software, and/or a single .tgz or .zip archive containing data. EMNLP 2023 encourages the submission of these supplementary materials to improve the reproducibility of results and to enable authors to provide additional information that does not fit in the paper. All supplementary materials must be properly anonymized.",
                        "order": 9
                    }            
                }            
            }
        ))
        helpers.await_queue()
        helpers.await_queue_edit(openreview_client, 'EMNLP/2023/Conference/-/Revision-0-1', count=1)

        submission_invitation = openreview_client.get_invitation('EMNLP/2023/Conference/-/Submission')
        assert submission_invitation
        assert 'supplementary_materials' in submission_invitation.edit['note']['content']
        assert submission_invitation.edit['note']['content']['supplementary_materials']['value']['param']['optional']
        assert 'submission_type' not in submission_invitation.edit['note']['content']
        assert 'TLDR' not in submission_invitation.edit['note']['content']
        assert 'pdf' not in submission_invitation.edit['note']['content']

        revision_invitation = openreview_client.get_invitation('EMNLP/2023/Conference/-/Revision')
        assert submission_invitation.expdate == revision_invitation.cdate
        invitation_due_date = revision_invitation.edit['invitation']['duedate']
        assert invitation_due_date == openreview.tools.datetime_millis(due_date.replace(hour=0, minute=0, second=0, microsecond=0))
        assert 'pdf' in revision_invitation.edit['invitation']['edit']['note']['content']
        assert 'optional' not in revision_invitation.edit['invitation']['edit']['note']['content']['pdf']['value']['param']
        assert 'optional' not in revision_invitation.edit['invitation']['edit']['note']['content']['submission_type']['value']['param']
        assert 'optional' not in revision_invitation.edit['invitation']['edit']['note']['content']['supplementary_materials']['value']['param']
        assert 'TLDR' not in revision_invitation.edit['invitation']['edit']['note']['content']

    def test_submit_papers(self, test_client, client, openreview_client, helpers):

        test_client = openreview.api.OpenReviewClient(username='test@mail.com', password=helpers.strong_password)

        domains = ['smith.edu', 'amazon.com', 'google.com', 'harvard.edu', 'meta.com']
        for i in range(1,6):
            note = openreview.api.Note(
                content = {
                    'title': { 'value': 'Test Paper Title ' + str(i) },
                    'abstract': { 'value': 'This is a test abstract ' + str(i) },
                    'authorids': { 'value': ['test@mail.com', 'john@' + domains[i-1]] },
                    'authors': { 'value': ['SomeFirstName User', 'John SomeLastName'] },
                    'keywords': { 'value': ['machine learning', 'nlp'] },
                }
            )

            test_client.post_note_edit(invitation='EMNLP/2023/Conference/-/Submission',
                signatures=['~SomeFirstName_User1'],
                note=note)   
            
        ## finish abstract deadline
        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)
        first_date = now - datetime.timedelta(minutes=28)

        pc_client=openreview.Client(username='pc@emnlp.org', password=helpers.strong_password)
        request_form=client.get_notes(invitation='openreview.net/Support/-/Request_Form', sort='tmdate')[0]

        venue_revision_note = pc_client.post_note(openreview.Note(
            content={
                'title': 'The 2023 Conference on Empirical Methods in Natural Language Processing',
                'Official Venue Name': 'The 2023 Conference on Empirical Methods in Natural Language Processing',
                'Abbreviated Venue Name': 'EMNLP 2023',
                'Official Website URL': 'https://2023.emnlp.org/',
                'program_chair_emails': ['pc@emnlp.org'],
                'contact_email': 'pc@emnlp.org',
                'publication_chairs':'No, our venue does not have Publication Chairs',
                'Venue Start Date': '2023/07/01',
                'abstract_registration_deadline': first_date.strftime('%Y/%m/%d %H:%M'),
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'Location': 'Singapore',
                'submission_reviewer_assignment': 'Automatic',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '1000',
                'use_recruitment_template': 'Yes',
                'Additional Submission Options': {
                    "supplementary_materials": {
                        "value": {
                            "param": {
                                "type": "file",
                                "extensions": [
                                    "tgz",
                                    "zip"
                                ],
                                "maxSize": 100
                            }
                        },
                        "description": "Each submission can optionally be accompanied by a single .tgz or .zip archive containing software, and/or a single .tgz or .zip archive containing data. EMNLP 2023 encourages the submission of these supplementary materials to improve the reproducibility of results and to enable authors to provide additional information that does not fit in the paper. All supplementary materials must be properly anonymized.",
                        "order": 9
                    }
                },
                'remove_submission_options': ['TL;DR'],
                'second_deadline_additional_options': {
                    'pdf': {
                        'order': 7,
                        'description': 'Upload a PDF file that ends with .pdf.',
                        'value': {
                            'param': {
                                'type': 'file',
                                'maxSize': 50,
                                'extensions': ['pdf']
                            }
                        }
                    },
                    "submission_type": {
                        "value": {
                            "param": {
                                "type": "string",
                                "enum": [
                                    "Regular Long Paper",
                                    "Regular Short Paper"
                                ],
                                "input": "select"
                            }
                        },
                        "description": "Please enter the category under which the submission should be reviewed. This cannot be changed after the abstract submission deadline.",
                        "order": 1
                    },
                    "supplementary_materials": {
                        "value": {
                            "param": {
                                "type": "file",
                                "extensions": [
                                    "tgz",
                                    "zip"
                                ],
                                "maxSize": 100
                            }
                        },
                        "description": "Each submission can optionally be accompanied by a single .tgz or .zip archive containing software, and/or a single .tgz or .zip archive containing data. EMNLP 2023 encourages the submission of these supplementary materials to improve the reproducibility of results and to enable authors to provide additional information that does not fit in the paper. All supplementary materials must be properly anonymized.",
                        "order": 9
                    }            
                }   
            },
            forum=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Revision'.format(request_form.number),
            readers=['{}/Program_Chairs'.format('EMNLP/2023/Conference'), 'openreview.net/Support'],
            referent=request_form.forum,
            replyto=request_form.forum,
            signatures=['~Program_EMNLPChair1'],
            writers=[]
        ))

        helpers.await_queue()
        helpers.await_queue_edit(openreview_client, 'EMNLP/2023/Conference/-/Post_Submission-0-0')
        helpers.await_queue_edit(openreview_client, 'EMNLP/2023/Conference/-/Withdrawal-0-0')
        helpers.await_queue_edit(openreview_client, 'EMNLP/2023/Conference/-/Desk_Rejection-0-0')
        helpers.await_queue_edit(openreview_client, 'EMNLP/2023/Conference/-/Revision-0-0')

        invitations = openreview_client.get_invitations(invitation='EMNLP/2023/Conference/-/Revision')
        assert len(invitations) == 5
        assert invitations[0].duedate == openreview.tools.datetime_millis(due_date.replace(hour=0, minute=0, second=0, microsecond=0))

        submissions = openreview_client.get_notes(invitation='EMNLP/2023/Conference/-/Submission', sort='number:asc')
        assert submissions[4].readers == [
            'EMNLP/2023/Conference',
            'EMNLP/2023/Conference/Senior_Area_Chairs',
            'EMNLP/2023/Conference/Area_Chairs',
            'EMNLP/2023/Conference/Reviewers',
            'EMNLP/2023/Conference/Submission5/Authors'
        ]

        ## withdraw submission
        withdraw_note = test_client.post_note_edit(invitation='EMNLP/2023/Conference/Submission5/-/Withdrawal',
            signatures=['EMNLP/2023/Conference/Submission5/Authors'],
            note=openreview.api.Note(
                content={
                    'withdrawal_confirmation': { 'value': 'I have read and agree with the venue\'s withdrawal policy on behalf of myself and my co-authors.' },
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=withdraw_note['id'])
        helpers.await_queue_edit(openreview_client, invitation='EMNLP/2023/Conference/-/Withdrawn_Submission')

        withdrawn_submission = openreview_client.get_notes(invitation='EMNLP/2023/Conference/-/Withdrawn_Submission')
        assert len(withdrawn_submission) == 1

        year = datetime.datetime.now().year
        valid_bibtex = '''@misc{
anonymous'''+str(year)+'''test,
title={Test Paper Title 5},
author={Anonymous},
year={'''+str(year)+'''},
url={https://openreview.net/forum?id='''

        valid_bibtex = valid_bibtex + withdrawn_submission[0].forum + '''}
}'''

        assert '_bibtex' in withdrawn_submission[0].content and withdrawn_submission[0].content['_bibtex']['value'] == valid_bibtex

        messages = client.get_messages(subject='[EMNLP 2023]: Paper #5 withdrawn by paper authors')
        assert messages and len(messages) == 3
        recipients = [msg['content']['to'] for msg in messages]
        assert 'pc@emnlp.org' in recipients

        pc_openreview_client = openreview.api.OpenReviewClient(username='pc@emnlp.org', password=helpers.strong_password)

        # reverse withdrawal
        withdrawal_reversion_note = pc_openreview_client.post_note_edit(invitation='EMNLP/2023/Conference/Submission5/-/Withdrawal_Reversion',
                                    signatures=['EMNLP/2023/Conference/Program_Chairs'],
                                    note=openreview.api.Note(
                                        content={
                                            'revert_withdrawal_confirmation': { 'value': 'We approve the reversion of withdrawn submission.' },
                                        }
                                    ))

        helpers.await_queue_edit(openreview_client, edit_id=withdrawal_reversion_note['id'])
        helpers.await_queue_edit(openreview_client, invitation='EMNLP/2023/Conference/Submission5/-/Withdrawal_Reversion')

        #desk-reject paper
        desk_reject_note = pc_openreview_client.post_note_edit(invitation=f'EMNLP/2023/Conference/Submission5/-/Desk_Rejection',
                                    signatures=['EMNLP/2023/Conference/Program_Chairs'],
                                    note=openreview.api.Note(
                                        content={
                                            'desk_reject_comments': { 'value': 'No pdf.' },
                                        }
                                    ))

        helpers.await_queue_edit(openreview_client, edit_id=desk_reject_note['id'])
        helpers.await_queue_edit(openreview_client, invitation='EMNLP/2023/Conference/-/Desk_Rejected_Submission')

        desk_rejected_submission = openreview_client.get_notes(invitation='EMNLP/2023/Conference/-/Desk_Rejected_Submission')
        assert len(desk_rejected_submission) == 1

        valid_bibtex = '''@misc{
anonymous'''+str(year)+'''test,
title={Test Paper Title 5},
author={Anonymous},
year={'''+str(year)+'''},
url={https://openreview.net/forum?id='''

        valid_bibtex = valid_bibtex + desk_rejected_submission[0].forum + '''}
}'''

        assert '_bibtex' in desk_rejected_submission[0].content and desk_rejected_submission[0].content['_bibtex']['value'] == valid_bibtex

        desk_rejection_reversion_note = pc_openreview_client.post_note_edit(invitation='EMNLP/2023/Conference/Submission5/-/Desk_Rejection_Reversion',
                                    signatures=['EMNLP/2023/Conference/Program_Chairs'],
                                    note=openreview.api.Note(
                                        content={
                                            'revert_desk_rejection_confirmation': { 'value': 'We approve the reversion of desk-rejected submission.' },
                                        }
                                    ))

        helpers.await_queue_edit(openreview_client, edit_id=desk_rejection_reversion_note['id'])
        helpers.await_queue_edit(openreview_client, invitation='EMNLP/2023/Conference/Submission5/-/Desk_Rejection_Reversion')

        revision_due_date = now + datetime.timedelta(days=10)

        revision_stage_note = pc_client.post_note(openreview.Note(
            content={
                'submission_revision_name': 'Supplementary_Material',
                'submission_revision_start_date': due_date.strftime('%Y/%m/%d'),
                'submission_revision_deadline': revision_due_date.strftime('%Y/%m/%d'),
                'accepted_submissions_only': 'Enable revision for all submissions',
                'submission_author_edition': 'Allow addition and removal of authors',
                'submission_revision_additional_options': {
                    "supplementary_materials": {
                        "value": {
                            "param": {
                                "type": "file",
                                "extensions": [
                                    "zip",
                                    "pdf",
                                    "tgz",
                                    "gz"
                                ],
                                "maxSize": 100
                            }
                        },
                        "description": "All supplementary material must be self-contained and zipped into a single file. Note that supplementary material will be visible to reviewers and the public throughout and after the review period, and ensure all material is anonymized. The maximum file size is 100MB.",
                        "order": 1
                    },            
                },
                'submission_revision_remove_options': ['title', 'authors', 'authorids', 'abstract', 'pdf', 'keywords']
            },
            forum=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Submission_Revision_Stage'.format(request_form.number),
            readers=['{}/Program_Chairs'.format('EMNLP/2023/Conference'), 'openreview.net/Support'],
            referent=request_form.forum,
            replyto=request_form.forum,
            signatures=['~Program_EMNLPChair1'],
            writers=[]
        ))
        assert revision_stage_note

        helpers.await_queue()
        helpers.await_queue_edit(openreview_client, 'EMNLP/2023/Conference/-/Supplementary_Material-0-1', count=1)

        # assert revision invitation did not change
        revision_invitation = openreview_client.get_invitation('EMNLP/2023/Conference/-/Revision')
        assert 'pdf' in revision_invitation.edit['invitation']['edit']['note']['content']
        assert 'optional' not in revision_invitation.edit['invitation']['edit']['note']['content']['pdf']['value']['param']
        assert 'optional' not in revision_invitation.edit['invitation']['edit']['note']['content']['submission_type']['value']['param']
        assert 'optional' not in revision_invitation.edit['invitation']['edit']['note']['content']['supplementary_materials']['value']['param']
        assert 'TLDR' not in revision_invitation.edit['invitation']['edit']['note']['content']

        # assert supplementary material content does not have any extra fields
        supplementary_material_invitation = openreview_client.get_invitation('EMNLP/2023/Conference/-/Supplementary_Material')
        assert revision_invitation.edit['invitation']['duedate'] == supplementary_material_invitation.edit['invitation']['cdate']
        content_keys = supplementary_material_invitation.edit['invitation']['edit']['note']['content'].keys()
        assert ['supplementary_materials'] == list(content_keys)

        #close submissions
        due_date = now - datetime.timedelta(days=1)
        venue_revision_note = pc_client.post_note(openreview.Note(
            content={
                'title': 'The 2023 Conference on Empirical Methods in Natural Language Processing',
                'Official Venue Name': 'The 2023 Conference on Empirical Methods in Natural Language Processing',
                'Abbreviated Venue Name': 'EMNLP 2023',
                'Official Website URL': 'https://2023.emnlp.org/',
                'program_chair_emails': ['pc@emnlp.org'],
                'contact_email': 'pc@emnlp.org',
                'publication_chairs':'No, our venue does not have Publication Chairs',
                'Venue Start Date': '2023/07/01',
                'abstract_registration_deadline': first_date.strftime('%Y/%m/%d %H:%M'),
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'Location': 'Singapore',
                'submission_reviewer_assignment': 'Automatic',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '1000',
                'use_recruitment_template': 'Yes',
                'Additional Submission Options': {
                    "supplementary_materials": {
                        "value": {
                            "param": {
                                "type": "file",
                                "extensions": [
                                    "tgz",
                                    "zip"
                                ],
                                "maxSize": 100
                            }
                        },
                        "description": "Each submission can optionally be accompanied by a single .tgz or .zip archive containing software, and/or a single .tgz or .zip archive containing data. EMNLP 2023 encourages the submission of these supplementary materials to improve the reproducibility of results and to enable authors to provide additional information that does not fit in the paper. All supplementary materials must be properly anonymized.",
                        "order": 9
                    }
                },
                'remove_submission_options': ['TL;DR'],
                'second_deadline_additional_options': {
                    'pdf': {
                        'order': 7,
                        'description': 'Upload a PDF file that ends with .pdf.',
                        'value': {
                            'param': {
                                'type': 'file',
                                'maxSize': 50,
                                'extensions': ['pdf']
                            }
                        }
                    },
                    "submission_type": {
                        "value": {
                            "param": {
                                "type": "string",
                                "enum": [
                                    "Regular Long Paper",
                                    "Regular Short Paper"
                                ],
                                "input": "select"
                            }
                        },
                        "description": "Please enter the category under which the submission should be reviewed. This cannot be changed after the abstract submission deadline.",
                        "order": 1
                    },
                    "supplementary_materials": {
                        "value": {
                            "param": {
                                "type": "file",
                                "extensions": [
                                    "tgz",
                                    "zip"
                                ],
                                "maxSize": 100
                            }
                        },
                        "description": "Each submission can optionally be accompanied by a single .tgz or .zip archive containing software, and/or a single .tgz or .zip archive containing data. EMNLP 2023 encourages the submission of these supplementary materials to improve the reproducibility of results and to enable authors to provide additional information that does not fit in the paper. All supplementary materials must be properly anonymized.",
                        "order": 9
                    }            
                }   
            },
            forum=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Revision'.format(request_form.number),
            readers=['{}/Program_Chairs'.format('EMNLP/2023/Conference'), 'openreview.net/Support'],
            referent=request_form.forum,
            replyto=request_form.forum,
            signatures=['~Program_EMNLPChair1'],
            writers=[]
        ))

        helpers.await_queue()

        # open revisions
        revision_due_date = now + datetime.timedelta(days=10)

        revision_stage_note = pc_client.post_note(openreview.Note(
            content={
                'submission_revision_name': 'Supplementary_Material',
                'submission_revision_start_date': due_date.strftime('%Y/%m/%d'),
                'submission_revision_deadline': revision_due_date.strftime('%Y/%m/%d'),
                'accepted_submissions_only': 'Enable revision for all submissions',
                'submission_author_edition': 'Allow addition and removal of authors',
                'submission_revision_additional_options': {
                    "supplementary_materials": {
                        "value": {
                            "param": {
                                "type": "file",
                                "extensions": [
                                    "zip",
                                    "pdf",
                                    "tgz",
                                    "gz"
                                ],
                                "maxSize": 100
                            }
                        },
                        "description": "All supplementary material must be self-contained and zipped into a single file. Note that supplementary material will be visible to reviewers and the public throughout and after the review period, and ensure all material is anonymized. The maximum file size is 100MB.",
                        "order": 1
                    },            
                },
                'submission_revision_remove_options': ['title', 'authors', 'authorids', 'abstract', 'pdf', 'keywords']
            },
            forum=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Submission_Revision_Stage'.format(request_form.number),
            readers=['{}/Program_Chairs'.format('EMNLP/2023/Conference'), 'openreview.net/Support'],
            referent=request_form.forum,
            replyto=request_form.forum,
            signatures=['~Program_EMNLPChair1'],
            writers=[]
        ))
        assert revision_stage_note

    def test_desk_rejection_by_SAC(self, test_client, client, openreview_client, helpers):

        #update desk-rejection invitation
        openreview_client.post_invitation_edit(
            invitations='EMNLP/2023/Conference/-/Edit',
            readers=['EMNLP/2023/Conference'],
            writers=['EMNLP/2023/Conferencee'],
            signatures=['EMNLP/2023/Conference'],
            invitation=openreview.api.Invitation(
                id='EMNLP/2023/Conference/-/Desk_Rejection',
                edit={
                    'invitation': {
                        'invitees': [
                            'EMNLP/2023/Conference/Program_Chairs',
                            'EMNLP/2023/Conference/Submission${3/content/noteNumber/value}/Senior_Area_Chairs',
                            'EMNLP/2023/Conference/Submission${3/content/noteNumber/value}/Area_Chairs'
                            ],
                        'edit': {
                            'signatures': {
                                'param': { 
                                    'items': [
                                        { 'value': 'EMNLP/2023/Conference/Submission${7/content/noteNumber/value}/Senior_Area_Chairs', 'optional': True }, 
                                        { 'prefix': 'EMNLP/2023/Conference/Submission${7/content/noteNumber/value}/Area_Chair_.*', 'optional': True }, 
                                        { 'value': 'EMNLP/2023/Conference/Program_Chairs', 'optional': True }
                                    ] 
                                }                                
                            },
                            'note': {
                                'content': {
                                    'title': { 'delete': True }
                                }
                            }
                        }
                    }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, 'EMNLP/2023/Conference/-/Desk_Rejection-0-1', count=3)
        invitation = openreview_client.get_invitation('EMNLP/2023/Conference/Submission1/-/Desk_Rejection')
        assert invitation.invitees == [
            'EMNLP/2023/Conference/Program_Chairs',
            'EMNLP/2023/Conference/Submission1/Senior_Area_Chairs',
            'EMNLP/2023/Conference/Submission1/Area_Chairs'
        ]
        assert invitation.edit['signatures']['param']['items'] == [
            { 'value': 'EMNLP/2023/Conference/Submission1/Senior_Area_Chairs', 'optional': True }, 
            { 'prefix': 'EMNLP/2023/Conference/Submission1/Area_Chair_.*', 'optional': True }, 
            { 'value': 'EMNLP/2023/Conference/Program_Chairs', 'optional': True }
        ]

        pc_client=openreview.Client(username='pc@emnlp.org', password=helpers.strong_password)
        pc_client_v2=openreview.api.OpenReviewClient(username='pc@emnlp.org', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        openreview_client.add_members_to_group('EMNLP/2023/Conference/Senior_Area_Chairs', ['sac@emnlp.com', 'sac2@emnlp.org'])
        openreview_client.add_members_to_group('EMNLP/2023/Conference/Area_Chairs', ['ac1@emnlp.org', 'ac2@emnlp.org'])
        openreview.tools.replace_members_with_ids(openreview_client, openreview_client.get_group('EMNLP/2023/Conference/Senior_Area_Chairs'))

        with open(os.path.join(os.path.dirname(__file__), 'data/rev_scores_venue.csv'), 'w') as file_handle:
            writer = csv.writer(file_handle)
            for sac in openreview_client.get_group('EMNLP/2023/Conference/Senior_Area_Chairs').members:
                for ac in openreview_client.get_group('EMNLP/2023/Conference/Area_Chairs').members:
                    writer.writerow([ac, sac, round(random.random(), 2)])

        affinity_scores_url = client.put_attachment(os.path.join(os.path.dirname(__file__), 'data/rev_scores_venue.csv'), f'openreview.net/Support/-/Request{request_form.number}/Paper_Matching_Setup', 'upload_affinity_scores')

        ## setup matching to assign SAC to each AC
        client.post_note(openreview.Note(
            content={
                'title': 'Paper Matching Setup',
                'matching_group': 'EMNLP/2023/Conference/Senior_Area_Chairs',
                'compute_conflicts': 'No',
                'compute_affinity_scores': 'No',
                'upload_affinity_scores': affinity_scores_url

            },
            forum=request_form.id,
            replyto=request_form.id,
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Paper_Matching_Setup',
            readers=['EMNLP/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_EMNLPChair1'],
            writers=[]
        ))
        helpers.await_queue()

        assert pc_client_v2.get_edges_count(invitation='EMNLP/2023/Conference/Senior_Area_Chairs/-/Affinity_Score') == 4

        openreview_client.post_edge(openreview.api.Edge(
            invitation = 'EMNLP/2023/Conference/Senior_Area_Chairs/-/Proposed_Assignment',
            head = '~AC_EMNLPOne1',
            tail = '~SAC_EMNLPOne1',
            signatures = ['EMNLP/2023/Conference/Program_Chairs'],
            weight = 1,
            label = 'sac-matching'
        ))

        openreview_client.post_edge(openreview.api.Edge(
            invitation = 'EMNLP/2023/Conference/Senior_Area_Chairs/-/Proposed_Assignment',
            head = '~AC_EMNLPTwo1',
            tail = '~SAC_EMNLPOne1',
            signatures = ['EMNLP/2023/Conference/Program_Chairs'],
            weight = 1,
            label = 'sac-matching'
        ))

        venue = openreview.helpers.get_conference(pc_client, request_form.id, setup=False)

        venue.set_assignments(assignment_title='sac-matching', committee_id='EMNLP/2023/Conference/Senior_Area_Chairs')

        sac_assignment_count = pc_client_v2.get_edges_count(invitation='EMNLP/2023/Conference/Senior_Area_Chairs/-/Assignment')
        assert sac_assignment_count == 2

        sac_client = openreview.api.OpenReviewClient(username = 'sac@emnlp.com', password=helpers.strong_password)

        ## setup matching ACs to take into account the SAC conflicts
        client.post_note(openreview.Note(
            content={
                'title': 'Paper Matching Setup',
                'matching_group': 'EMNLP/2023/Conference/Area_Chairs',
                'compute_conflicts': 'NeurIPS',
                'compute_conflicts_N_years': '3',
                'compute_affinity_scores': 'No'

            },
            forum=request_form.id,
            replyto=request_form.id,
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Paper_Matching_Setup',
            readers=['EMNLP/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_EMNLPChair1'],
            writers=[]
        ))
        helpers.await_queue()

        submissions = pc_client_v2.get_notes(content= { 'venueid': 'EMNLP/2023/Conference/Submission'}, sort='number:asc')
        assert len(submissions) == 5

        for i in range(0,5):
            acs = ['~AC_EMNLPOne1', '~AC_EMNLPTwo1']

            openreview_client.post_edge(openreview.api.Edge(
                invitation = 'EMNLP/2023/Conference/Area_Chairs/-/Proposed_Assignment',
                head = submissions[i].id,
                tail = acs[i%2],
                signatures = ['EMNLP/2023/Conference/Program_Chairs'],
                weight = 1,
                label = 'ac-matching'
            ))

        venue.set_assignments(assignment_title='ac-matching', committee_id='EMNLP/2023/Conference/Area_Chairs')

        #desk-reject paper
        desk_reject_note = sac_client.post_note_edit(invitation=f'EMNLP/2023/Conference/Submission1/-/Desk_Rejection',
                                    signatures=['EMNLP/2023/Conference/Submission1/Senior_Area_Chairs'],
                                    note=openreview.api.Note(
                                        content={
                                            'desk_reject_comments': { 'value': 'Missing pdf.' },
                                        }
                                    ))

        helpers.await_queue_edit(openreview_client, edit_id=desk_reject_note['id'])
        helpers.await_queue_edit(openreview_client, invitation='EMNLP/2023/Conference/-/Desk_Rejected_Submission', count=2)

        submissions = pc_client_v2.get_notes(content= { 'venueid': 'EMNLP/2023/Conference/Submission'}, sort='number:asc')
        assert len(submissions) == 4

        desk_rejected_note = sac_client.get_notes(invitation='EMNLP/2023/Conference/Submission1/-/Desk_Rejection')[0]
        assert desk_rejected_note
        assert 'EMNLP/2023/Conference/Submission1/Senior_Area_Chairs' == desk_rejected_note.signatures[0]

        messages = client.get_messages(subject='[EMNLP 2023]: Paper #1 desk-rejected by Senior Area Chairs')
        assert messages and len(messages) == 5
        recipients = [msg['content']['to'] for msg in messages]
        assert 'pc@emnlp.org' in recipients

        ac_client = openreview.api.OpenReviewClient(username = 'ac2@emnlp.org', password=helpers.strong_password)
        submissions = ac_client.get_notes(invitation='EMNLP/2023/Conference/-/Submission', sort='number:asc')
        anon_group_id = ac_client.get_groups(prefix='EMNLP/2023/Conference/Submission2/Area_Chair_', signatory='~AC_EMNLPTwo1')[0].id

        #desk-reject paper
        desk_reject_note = ac_client.post_note_edit(invitation=f'EMNLP/2023/Conference/Submission2/-/Desk_Rejection',
                                    signatures=[anon_group_id],
                                    note=openreview.api.Note(
                                        content={
                                            'desk_reject_comments': { 'value': 'Too long.' },
                                        }
                                    ))

        helpers.await_queue_edit(openreview_client, edit_id=desk_reject_note['id'])
        helpers.await_queue_edit(openreview_client, invitation='EMNLP/2023/Conference/-/Desk_Rejected_Submission', count=3)

        submissions = pc_client_v2.get_notes(content= { 'venueid': 'EMNLP/2023/Conference/Submission'}, sort='number:asc')
        assert len(submissions) == 3

        desk_rejected_note = ac_client.get_notes(invitation='EMNLP/2023/Conference/Submission2/-/Desk_Rejection')[0]
        assert desk_rejected_note

        pretty_id = openreview.tools.pretty_id(anon_group_id.split('/')[-1])
        messages = client.get_messages(to='pc@emnlp.org', subject=f'[EMNLP 2023]: Paper #2 desk-rejected by {pretty_id}')
        assert messages and len(messages) == 1

    def test_release_submissions(self, test_client, client, openreview_client, helpers):

        pc_client=openreview.Client(username='pc@emnlp.org', password=helpers.strong_password)
        request_form=client.get_notes(invitation='openreview.net/Support/-/Request_Form', sort='tmdate')[0]

        ## make submissions visible to everyone
        pc_client.post_note(openreview.Note(
            content= {
                'force': 'Yes',
                'submission_readers': 'Assigned program committee (assigned reviewers, assigned area chairs, assigned senior area chairs if applicable)'
            },
            forum= request_form.id,
            invitation= f'openreview.net/Support/-/Request{request_form.number}/Post_Submission',
            readers= ['EMNLP/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            referent= request_form.id,
            replyto= request_form.id,
            signatures= ['~Program_EMNLPChair1'],
            writers= [],
        ))

        helpers.await_queue()

        submissions = openreview_client.get_notes(content={'venueid':'EMNLP/2023/Conference/Submission'}, sort='number:asc')
        assert len(submissions) == 3

        for submission in submissions:
            submission.readers = [
                "EMNLP/2023/Conference",
                f"EMNLP/2023/Conference/Submission{submission.number}/Senior_Area_Chairs",
                f"EMNLP/2023/Conference/Submission{submission.number}/Area_Chairs",
                f"EMNLP/2023/Conference/Submission{submission.number}/Reviewers",
                f"EMNLP/2023/Conference/Submission{submission.number}/Authors"
            ]
        #     assert submission.odate
        #     assert '_bibtex' in submission.content

    def test_enable_ethics_reviewers(self, client, openreview_client, helpers):

        pc_client=openreview.Client(username='pc@emnlp.org', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0] 

        ethics_reviewers_group = openreview_client.get_group('EMNLP/2023/Conference/Ethics_Reviewers')
        assert ethics_reviewers_group
        openreview_client.add_members_to_group(ethics_reviewers_group, ['ethics_reviewer1@emnlp.com','ethics_reviewer2@emnlp.com'])
        ethics_chairs_group = openreview_client.get_group('EMNLP/2023/Conference/Ethics_Chairs')
        openreview_client.add_members_to_group(ethics_chairs_group, ['ethics_chair1@google.com', 'ethics_chair2@emnlp.com'])

        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(days=2)
        due_date = now + datetime.timedelta(days=3)
        stage_note = pc_client.post_note(openreview.Note(
            content={
                'ethics_review_start_date': start_date.strftime('%Y/%m/%d'),
                'ethics_review_deadline': due_date.strftime('%Y/%m/%d'),
                'make_ethics_reviews_public': 'No, ethics reviews should NOT be revealed publicly when they are posted',
                'release_ethics_reviews_to_authors': "No, ethics reviews should NOT be revealed when they are posted to the paper\'s authors",
                'release_ethics_reviews_to_reviewers': 'Ethics Review should not be revealed to any reviewer, except to the author of the ethics review',
                'remove_ethics_review_form_options': 'ethics_review',
                'release_submissions_to_ethics_reviewers': 'We confirm we want to release the submissions and reviews to the ethics reviewers'
            },
            forum=request_form.forum,
            referent=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Ethics_Review_Stage'.format(request_form.number),
            readers=['EMNLP/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_EMNLPChair1'],
            writers=[]
        ))

        helpers.await_queue()
        helpers.await_queue(openreview_client)

        ethics_chairs_group = openreview_client.get_group('EMNLP/2023/Conference/Ethics_Chairs')
        assert '~Ethics_ChairOne1' in ethics_chairs_group.members
        assert '~Ethics_ChairTwo1' in ethics_chairs_group.members

    def test_enable_SAC_ethics_review(self, client, openreview_client, helpers):

        pc_client=openreview.Client(username='pc@emnlp.org', password=helpers.strong_password)
        request_form=client.get_notes(invitation='openreview.net/Support/-/Request_Form', sort='tmdate')[0]


        venue = openreview.helpers.get_conference(pc_client, request_form.id, setup=False)

        venue.set_SAC_ethics_review_process()

        invitations = openreview_client.get_invitations(invitation='EMNLP/2023/Conference/-/SAC_Ethics_Review_Flag')
        assert len(invitations) == 3
        invitation = openreview_client.get_invitation(id='EMNLP/2023/Conference/Submission3/-/SAC_Ethics_Review_Flag')
        assert invitation.invitees == ['EMNLP/2023/Conference', 'EMNLP/2023/Conference/Submission3/Senior_Area_Chairs']

        sac_group = openreview_client.get_group('EMNLP/2023/Conference/Submission3/Senior_Area_Chairs')
        assert '~SAC_EMNLPOne1' in sac_group.members

        sac_client = openreview.api.OpenReviewClient(username='sac@emnlp.com', password=helpers.strong_password)
        sac_ethics_flag_note = sac_client.post_note_edit(invitation=invitation.id,
                                    signatures=['EMNLP/2023/Conference/Submission3/Senior_Area_Chairs'],
                                    note=openreview.api.Note(
                                        content={
                                            'ethics_review_flag': { 'value': 'Yes' },
                                            'comments': { 'value': 'Private comments to PCs.' }
                                        }
                                    ))

        helpers.await_queue_edit(openreview_client, edit_id=sac_ethics_flag_note['id'])
        helpers.await_queue_edit(openreview_client, invitation='EMNLP/2023/Conference/-/Ethics_Review_Flag', count=1)

        sac_group = openreview_client.get_group('EMNLP/2023/Conference/Submission3/Senior_Area_Chairs')
        assert '~SAC_EMNLPOne1' in sac_group.members
        assert '~Ethics_ChairTwo1' in sac_group.members
        assert '~Ethics_ChairOne1' not in sac_group.members

        submissions = openreview_client.get_notes(content={'venueid':'EMNLP/2023/Conference/Submission'}, sort='number:asc')
        assert len(submissions) == 3

        custom_demand_edge = openreview_client.get_edges(invitation='EMNLP/2023/Conference/Ethics_Reviewers/-/Custom_User_Demands', head=submissions[0].id)[0]
        assert custom_demand_edge.weight == 2

        assert 'flagged_for_ethics_review' in submissions[0].content and submissions[0].content['flagged_for_ethics_review']['value'] == True
        assert submissions[0].content['flagged_for_ethics_review']['readers'] == [
            'EMNLP/2023/Conference',
            'EMNLP/2023/Conference/Ethics_Chairs',
            'EMNLP/2023/Conference/Submission3/Ethics_Reviewers',
            'EMNLP/2023/Conference/Submission3/Senior_Area_Chairs',
            'EMNLP/2023/Conference/Submission3/Area_Chairs',
            'EMNLP/2023/Conference/Submission3/Reviewers'
        ]
        assert submissions[0].readers == [
            "EMNLP/2023/Conference",
            "EMNLP/2023/Conference/Submission3/Senior_Area_Chairs",
            "EMNLP/2023/Conference/Submission3/Area_Chairs",
            "EMNLP/2023/Conference/Submission3/Reviewers",
            "EMNLP/2023/Conference/Submission3/Authors",
            "EMNLP/2023/Conference/Submission3/Ethics_Reviewers"
        ]

        invitations = openreview_client.get_invitations(invitation='EMNLP/2023/Conference/-/Ethics_Review')
        assert len(invitations) == 1
        invitation = openreview_client.get_invitations(id='EMNLP/2023/Conference/Submission3/-/Ethics_Review')[0]
        assert invitation
        assert 'EMNLP/2023/Conference/Submission3/Ethics_Reviewers' in invitation.invitees

    def test_enable_ethics_metareview(self, client, openreview_client, helpers):

        pc_client=openreview.Client(username='pc@emnlp.org', password=helpers.strong_password)
        pc_client_v2=openreview.api.OpenReviewClient(username='pc@emnlp.org', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        venue = openreview.helpers.get_conference(pc_client, request_form.id, setup=False)

        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)
            
        venue.custom_stage = openreview.stages.CustomStage(name='Ethics_Meta_Review',
            reply_to=openreview.stages.CustomStage.ReplyTo.FORUM,
            source=openreview.stages.CustomStage.Source.FLAGGED_SUBMISSIONS,
            due_date=due_date,
            invitees=[openreview.stages.CustomStage.Participants.ETHICS_CHAIRS],
            readers=[openreview.stages.CustomStage.Participants.SENIOR_AREA_CHAIRS_ASSIGNED, openreview.stages.CustomStage.Participants.AREA_CHAIRS_ASSIGNED,
                    openreview.stages.CustomStage.Participants.REVIEWERS_SUBMITTED, openreview.stages.CustomStage.Participants.ETHICS_CHAIRS, openreview.stages.CustomStage.Participants.ETHICS_REVIEWERS_ASSIGNED, openreview.stages.CustomStage.Participants.AUTHORS],
            content={
                "ethics_violations": {
                    "value": {
                    "param": {
                        "type": "string",
                        "enum": [
                        "Yes",
                        "No"
                        ],
                        "input": "radio"
                    }
                    },
                    "order": 1,
                    "description": "Are there any substantial ethical issues with the research presented in this submission?"
                },
                "Category": {
                    "order": 2,
                    "description": "Please check **all** issues that apply with respect to the ACL code of ethics. The numbers refer to the sections and subsections in the ACM/ACL Code of Ethics above.",
                    "value": {
                    "param": {
                        "type": "string[]",
                        "enum": [
                        "1.1: Contribute to society and to human well-being, acknowledging that all people are stakeholders in computing",
                        "1.2: Avoid harm",
                        "1.3: Be honest and trustworthy",
                        "1.4: Be fair and take action not to discriminate",
                        "1.5: Respect the work required to produce new ideas, inventions, creative works, and computing artifacts",
                        "1.6: Respect privacy",
                        "1.7: Honor confidentiality",
                        "2.1: Strive to achieve high quality in both the processes and products of professional work",
                        "2.2: Maintain high standards of professional competence, conduct, and ethical practice",
                        "2.3: Know and respect existing rules pertaining to professional work",
                        "2.4: Accept and provide an appropriate professional review",
                        "2.5: Give comprehensive and thorough evaluations of computer systems and their impacts, including analysis of possible risks",
                        "2.6: Perform work only in areas of competence",
                        "2.7: Foster public awareness and understanding of computing, related technologies, and their consequences",
                        "2.8: Access computing and communication resources only when authorized or when compelled by the public good",
                        "2.9: Design and implement systems that are robustly and usably secure",
                        "3.1: Ensure that the public good is the central concern during all professional computing work",
                        "3.2: Articulate, encourage acceptance of, and evaluate fulfillment of social responsibilities by members of the organization or group",
                        "3.3: Manage personnel and resources to enhance the quality of working life",
                        "3.4: Articulate, apply, and support policies and processes that reflect the principles of the Code",
                        "3.5: Create opportunities for members of the organization or group to grow as professionals",
                        "3.6: Use care when modifying or retiring systems",
                        "3.7: Recognize and take special care of systems that become integrated into the infrastructure of society",
                        "4.1: Uphold, promote, and respect the principles of the Code",
                        "4.2: Treat violations of the Code as inconsistent with membership in the ACM"
                        ],
                        "input": "checkbox"
                    }
                    }
                },
                "ethics_concerns": {
                    "order": 3,
                    "description": "3. For each item selected, please enter the number and a short justification, and describe how you would suggest the authors address it.",
                    "value": {
                    "param": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 20000,
                        "input": "textarea"
                    }
                    }
                },
                "ethics_review_recommendation": {
                    "order": 4,
                    "description": "Please select one of the following: ",
                    "value": {
                    "param": {
                        "type": "string",
                        "enum": [
                        "1: No issues, accept as is",
                        "2: Some ethical issues to be addressed before acceptance.",
                        "3: Reject on the basis of serious ethics violations"
                        ],
                        "input": "radio"
                    }
                    }
                }
            },
            notify_readers=False,
            email_sacs=False
        )

        venue.create_custom_stage()
        helpers.await_queue(openreview_client)

        submissions = openreview_client.get_notes(content= { 'venueid': 'EMNLP/2023/Conference/Submission'}, sort='number:asc')

        invitations = openreview_client.get_invitations(invitation='EMNLP/2023/Conference/-/Ethics_Meta_Review')
        assert len(invitations) == 1
        invitation = openreview_client.get_invitation(id='EMNLP/2023/Conference/Submission3/-/Ethics_Meta_Review')
        assert invitation.invitees == ['EMNLP/2023/Conference/Program_Chairs', 'EMNLP/2023/Conference/Ethics_Chairs']
        assert invitation.edit['note']['forum']== submissions[0].id
        assert invitation.edit['note']['replyto'] == submissions[0].id
        assert 'ethics_review_recommendation' in invitations[0].edit['note']['content']
        assert invitation.minReplies == 1
        assert invitation.maxReplies == 1
        assert invitation.edit['note']['readers'] == [
            "EMNLP/2023/Conference/Program_Chairs",
            "EMNLP/2023/Conference/Submission3/Senior_Area_Chairs",
            "EMNLP/2023/Conference/Submission3/Area_Chairs",
            "EMNLP/2023/Conference/Submission3/Reviewers/Submitted",
            "EMNLP/2023/Conference/Submission3/Authors",
            "EMNLP/2023/Conference/Ethics_Chairs",
            "EMNLP/2023/Conference/Submission3/Ethics_Reviewers"
        ]

    def test_add_impersonator(self, client, request_page, selenium, helpers):
        ## Need super user permission to add the venue to the active_venues group
        request_form=client.get_notes(invitation='openreview.net/Support/-/Request_Form', sort='tmdate')[0]
        conference=openreview.helpers.get_conference(client, request_form.id)

        conference.set_impersonators(impersonators=['pc@emnlp.org'])

        pc_client = openreview.Client(username='pc@emnlp.org', password=helpers.strong_password)
        acs_id = conference.get_area_chairs_id()
        area_chairs = client.get_group(acs_id).members
        assert len(area_chairs) > 0
        result = pc_client.impersonate(area_chairs[0])

        assert result.get('token') is not None
        assert result.get('user', {}).get('id') == area_chairs[0]

    def test_release_reviews(self, client, openreview_client, helpers):

        pc_client=openreview.Client(username='pc@emnlp.org', password=helpers.strong_password)
        request_form=client.get_notes(invitation='openreview.net/Support/-/Request_Form', sort='tmdate')[0]

        ## make submissions visible to everyone
        pc_client.post_note(openreview.Note(
            content= {
                'force': 'Yes',
                'submission_readers': 'Everyone (submissions are public)'
            },
            forum=request_form.id,
            invitation= f'openreview.net/Support/-/Request{request_form.number}/Post_Submission',
            readers= ['EMNLP/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            referent= request_form.id,
            replyto= request_form.id,
            signatures= ['~Program_EMNLPChair1'],
            writers= [],
        ))

        helpers.await_queue()

        submissions = openreview_client.get_notes(content={'venueid':'EMNLP/2023/Conference/Submission'}, sort='number:asc')
        assert len(submissions) == 3

        for submission in submissions:
            submission.readers = [
                "everyone"
            ]

        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)

        ## run review stage
        review_stage_note=pc_client.post_note(openreview.Note(
            content={
                'review_deadline': due_date.strftime('%Y/%m/%d'),
                'make_reviews_public': 'Yes, reviews should be revealed publicly when they are posted',
                'release_reviews_to_authors': 'No, reviews should NOT be revealed when they are posted to the paper\'s authors',
                'release_reviews_to_reviewers': 'Review should not be revealed to any reviewer, except to the author of the review',
                'email_program_chairs_about_reviews': 'No, do not email program chairs about received reviews',
            },
            forum=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Review_Stage'.format(request_form.number),
            readers=['EMNLP/2023/Conference/Program_Chairs', 'openreview.net/Support'],
            replyto=request_form.forum,
            referent=request_form.forum,
            signatures=['~Program_EMNLPChair1'],
            writers=[]
        ))
        helpers.await_queue()

        assert len(openreview_client.get_invitations(invitation='EMNLP/2023/Conference/-/Official_Review')) == 3
        invitation = openreview_client.get_invitation('EMNLP/2023/Conference/Submission3/-/Official_Review')
        assert invitation.edit['note']['readers'] == ['everyone']
