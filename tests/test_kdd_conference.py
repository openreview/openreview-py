import datetime
import re
import pytest
from selenium.webdriver.common.by import By
import openreview

class TestKDDConference():
    def test_create_conference(self, client, openreview_client, helpers, selenium, request_page):
        now = datetime.datetime.now()
        due_date = now + datetime.timedelta(days=3)
        first_date = now + datetime.timedelta(days=1)

        helpers.create_user('pc@kdd.org', 'Program', 'KDDChair')
        pc_client = openreview.Client(username='pc@kdd.org', password=helpers.strong_password)

        request_form_note = pc_client.post_note(openreview.Note(
            invitation='openreview.net/Support/-/Request_Form',
            signatures=['~Program_KDDChair1'],
            readers=[
                'openreview.net/Support',
                '~Program_KDDChair1'
            ],
            writers=[],
            content={
                'title': 'KDD Research Track August',
                'Official Venue Name': 'KDD Research Track August',
                'Abbreviated Venue Name': 'KDD 2026',
                'Official Website URL': 'https://kdd.org',
                'program_chair_emails': ['pc@kdd.org'],
                'contact_email': 'pc@kdd.org',
                'publication_chairs':'No, our venue does not have Publication Chairs',
                'Area Chairs (Metareviewers)': 'Yes, our venue has Area Chairs',
                'senior_area_chairs': 'Yes, our venue has Senior Area Chairs',
                'Venue Start Date': '2026/08/01',
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'abstract_registration_deadline': first_date.strftime('%Y/%m/%d'),
                'Location': 'Virtual',
                'submission_reviewer_assignment': 'Automatic',
                'Author and Reviewer Anonymity': 'Double-blind',
                'reviewer_identity': ['Program Chairs', 'Assigned Senior Area Chair', 'Assigned Area Chair', 'Assigned Reviewers'],
                'area_chair_identity': ['Program Chairs', 'Assigned Senior Area Chair', 'Assigned Area Chair', 'Assigned Reviewers'],
                'senior_area_chair_identity': ['Program Chairs', 'Assigned Senior Area Chair', 'Assigned Area Chair', 'Assigned Reviewers'],
                'Open Reviewing Policy': 'Submissions and reviews should both be private.',
                'submission_readers': 'Assigned program committee (assigned reviewers, assigned area chairs, assigned senior area chairs if applicable)',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100',
                'api_version': '2',
                'submission_deadline_author_reorder': 'Yes',
                'submission_license': ['CC BY 4.0'],
                'venue_organizer_agreement': [
                    'OpenReview natively supports a wide variety of reviewing workflow configurations. However, if we want significant reviewing process customizations or experiments, we will detail these requests to the OpenReview staff at least three months in advance.',
                    'We will ask authors and reviewers to create an OpenReview Profile at least two weeks in advance of the paper submission deadlines.',
                    'When assembling our group of reviewers and meta-reviewers, we will only include email addresses or OpenReview Profile IDs of people we know to have authored publications relevant to our venue.  (We will not solicit new reviewers using an open web form, because unfortunately some malicious actors sometimes try to create "fake ids" aiming to be assigned to review their own paper submissions.)',
                    'We acknowledge that, if our venue\'s reviewing workflow is non-standard, or if our venue is expecting more than a few hundred submissions for any one deadline, we should designate our own Workflow Chair, who will read the OpenReview documentation and manage our workflow configurations throughout the reviewing process.',
                    'We acknowledge that OpenReview staff work Monday-Friday during standard business hours US Eastern time, and we cannot expect support responses outside those times.  For this reason, we recommend setting submission and reviewing deadlines Monday through Thursday.',
                    'We will treat the OpenReview staff with kindness and consideration.'
                ]
            }))

        helpers.await_queue()

        client.post_note(openreview.Note(
            content={'venue_id': 'KDD.org/2026/Research_Track_August'},
            forum=request_form_note.forum,
            invitation='openreview.net/Support/-/Request{}/Deploy'.format(request_form_note.number),
            readers=['openreview.net/Support'],
            referent=request_form_note.forum,
            replyto=request_form_note.forum,
            signatures=['openreview.net/Support'],
            writers=['openreview.net/Support']
        ))

        helpers.await_queue()

        venue_group = openreview_client.get_group('KDD.org/2026/Research_Track_August')
        assert venue_group
        assert venue_group.host == 'KDD.org'
        assert openreview_client.get_group('KDD.org/2026/Research_Track_August/Senior_Area_Chairs')
        acs=openreview_client.get_group('KDD.org/2026/Research_Track_August/Area_Chairs')
        assert acs
        assert 'KDD.org/2026/Research_Track_August/Senior_Area_Chairs' in acs.readers
        reviewers=openreview_client.get_group('KDD.org/2026/Research_Track_August/Reviewers')
        assert reviewers
        assert 'KDD.org/2026/Research_Track_August/Senior_Area_Chairs' in reviewers.readers
        assert 'KDD.org/2026/Research_Track_August/Area_Chairs' in reviewers.readers

        assert openreview_client.get_group('KDD.org/2026/Research_Track_August/Authors')
        post_submission =  openreview_client.get_invitation('KDD.org/2026/Research_Track_August/-/Post_Submission')
        assert 'authors' in post_submission.edit['note']['content']

        assert 'authorids' in post_submission.edit['note']['content']

        full_submission =  openreview_client.get_invitation('KDD.org/2026/Research_Track_August/-/Full_Submission')
        assert 'authors' in full_submission.edit['invitation']['edit']['note']['content']
        assert 'readers' in full_submission.edit['invitation']['edit']['note']['content']['authors']
        assert full_submission.edit['invitation']['edit']['note']['content']['authors']['readers'] == ["KDD.org/2026/Research_Track_August", "KDD.org/2026/Research_Track_August/Submission${{4/id}/number}/Authors"]
        assert 'authorids' in full_submission.edit['invitation']['edit']['note']['content']
        assert 'readers' in full_submission.edit['invitation']['edit']['note']['content']['authorids']      
        assert full_submission.edit['invitation']['edit']['note']['content']['authorids']['readers'] == ["KDD.org/2026/Research_Track_August", "KDD.org/2026/Research_Track_August/Submission${{4/id}/number}/Authors"]

    def test_revision(self, client, openreview_client, selenium, request_page, helpers):
        pc_client=openreview.Client(username='pc@kdd.org', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        now = datetime.datetime.now()
        due_date = now + datetime.timedelta(days=3)
        first_date = now + datetime.timedelta(days=1)

        pc_client.post_note(openreview.Note(
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Revision',
            forum=request_form.id,
            readers=['KDD.org/2026/Research_Track_August/Program_Chairs', 'openreview.net/Support'],
            referent=request_form.id,
            replyto=request_form.id,
            signatures=['~Program_KDDChair1'],
            writers=[],
            content={
                'title': 'KDD Research Track August',
                'Official Venue Name': 'KDD Research Track August',
                'Abbreviated Venue Name': 'KDD 2026',
                'Official Website URL': 'https://kdd.org',
                'program_chair_emails': ['pc@kdd.org'],
                'contact_email': 'pc@kdd.org',
                'publication_chairs':'No, our venue does not have Publication Chairs',
                'Venue Start Date': '2026/08/01',
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'abstract_registration_deadline': first_date.strftime('%Y/%m/%d'),
                'Location': 'Virtual',
                'submission_reviewer_assignment': 'Automatic',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100',
                'use_recruitment_template': 'Yes',
                'homepage_override': {
                    'instructions': '''**Authors**\nPlease see our [call for papers](https://kdd.org/Conferences/2026/CallForPapers) and read the [ethics guidelines](https://kdd.org/public/EthicsGuidelines)'''
                },
                'Additional Submission Options': {
                    "corresponding_author": {
                        "value": {
                            "param": {
                                "type": "group",
                                "regex": "~.*",
                                "optional": False
                            }
                        },
                        "description": "Specify which author (only one) is designated as the corresponding author. ACM requires that every submitted and published Work be assigned a single Corresponding Author. This Corresponding Author will be responsible for all direct communication and correspondence with ACM. They will also be responsible for obtaining ORCIDs from all listed co-authors, collecting and communicating declarations of potential Conflicts of Interest in connection with their papers on behalf of all listed co-authors, and completing ACM’s Rights Assignment process for their Work. The Corresponding Author is often the first-named author on the Work, but this need not be the case. The co-authors determine which author shall be the Corresponding Author for the Work, but there may only be one Corresponding Author.",
                        "order": 9,
                        "readers": [
                            "KDD.org/2026/Research_Track_August",
                            "KDD.org/2026/Research_Track_August/Submission${{4/id}/number}/Authors"
                        ]
                    }
                }
            }
        ))
        helpers.await_queue()

        full_submission =  openreview_client.get_invitation('KDD.org/2026/Research_Track_August/-/Full_Submission')

        assert 'authors' in full_submission.edit['invitation']['edit']['note']['content']
        assert 'readers' in full_submission.edit['invitation']['edit']['note']['content']['authors']
        assert full_submission.edit['invitation']['edit']['note']['content']['authors']['readers'] == ["KDD.org/2026/Research_Track_August", "KDD.org/2026/Research_Track_August/Submission${{4/id}/number}/Authors"]

        assert 'authorids' in full_submission.edit['invitation']['edit']['note']['content']
        assert 'readers' in full_submission.edit['invitation']['edit']['note']['content']['authorids']      
        assert full_submission.edit['invitation']['edit']['note']['content']['authorids']['readers'] == ["KDD.org/2026/Research_Track_August", "KDD.org/2026/Research_Track_August/Submission${{4/id}/number}/Authors"]        

        assert 'corresponding_author' in full_submission.edit['invitation']['edit']['note']['content']
        assert 'readers' in full_submission.edit['invitation']['edit']['note']['content']['corresponding_author']      
        assert full_submission.edit['invitation']['edit']['note']['content']['corresponding_author']['readers'] == ["KDD.org/2026/Research_Track_August", "KDD.org/2026/Research_Track_August/Submission${{4/id}/number}/Authors"]        


    def test_submit_papers(self, test_client, client, helpers, openreview_client):

        pc_client=openreview.Client(username='pc@kdd.org', password=helpers.strong_password)
        request_form=client.get_notes(invitation='openreview.net/Support/-/Request_Form', sort='tmdate')[0]

        test_client = openreview.api.OpenReviewClient(username='test@mail.com', password=helpers.strong_password)

        domains = ['umass.edu', 'amazon.com', 'fb.com', 'cs.umass.edu', 'google.com', 'mit.edu']
        for i in range(1,6):
            note = openreview.api.Note(
                content = {
                    'title': { 'value': 'Paper title ' + str(i) },
                    'abstract': { 'value': 'This is an abstract ' + str(i) },
                    'authorids': { 'value': ['~SomeFirstName_User1', 'peter@mail.com', 'andrew@' + domains[i]] },
                    'authors': { 'value': ['SomeFirstName User', 'Peter SomeLastName', 'Andrew Mc'] },
                    'keywords': { 'value': ['machine learning', 'nlp'] },
                    'corresponding_author': { 'value': '~SomeFirstName_User1'}
                }
            )

            edit = test_client.post_note_edit(invitation='KDD.org/2026/Research_Track_August/-/Submission',
                signatures=['~SomeFirstName_User1'],
                note=note)
            
            helpers.await_queue_edit(openreview_client, edit['id'])


        submissions = openreview_client.get_notes(invitation='KDD.org/2026/Research_Track_August/-/Submission')
        assert len(submissions) == 5
        for submission in submissions:
            assert submission.content['corresponding_author']['value'] == '~SomeFirstName_User1'
            assert submission.content['corresponding_author']['readers'] == ["KDD.org/2026/Research_Track_August", f"KDD.org/2026/Research_Track_August/Submission{submission.number}/Authors"]

    def test_full_submission(self, test_client, client, helpers, openreview_client):

        pc_client=openreview.Client(username='pc@kdd.org', password=helpers.strong_password)
        request_form=client.get_notes(invitation='openreview.net/Support/-/Request_Form', sort='tmdate')[0]

        test_client = openreview.api.OpenReviewClient(username='test@mail.com', password=helpers.strong_password)

        ## finish abstract deadline
        now = datetime.datetime.now()
        start_date = now - datetime.timedelta(days=10)
        due_date = now + datetime.timedelta(days=3)
        first_date = now - datetime.timedelta(minutes=27)

        pc_client.post_note(openreview.Note(
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Revision',
            forum=request_form.id,
            readers=['KDD.org/2026/Research_Track_August/Program_Chairs', 'openreview.net/Support'],
            referent=request_form.id,
            replyto=request_form.id,
            signatures=['~Program_KDDChair1'],
            writers=[],
            content={
                'title': 'KDD Research Track August',
                'Official Venue Name': 'KDD Research Track August',
                'Abbreviated Venue Name': 'KDD 2026',
                'Official Website URL': 'https://kdd.org',
                'program_chair_emails': ['pc@kdd.org'],
                'contact_email': 'pc@kdd.org',
                'publication_chairs':'No, our venue does not have Publication Chairs',
                'Venue Start Date': '2026/08/01',
                'Submission Deadline': due_date.strftime('%Y/%m/%d %H:%M'),
                'Submission Start Date': start_date.strftime('%Y/%m/%d %H:%M'),
                'abstract_registration_deadline': first_date.strftime('%Y/%m/%d %H:%M'),
                'Location': 'Virtual',
                'submission_reviewer_assignment': 'Automatic',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100',
                'use_recruitment_template': 'Yes',
                'homepage_override': {
                    'instructions': '''**Authors**\nPlease see our [call for papers](https://kdd.org/Conferences/2026/CallForPapers) and read the [ethics guidelines](https://kdd.org/public/EthicsGuidelines)'''
                },
                'Additional Submission Options': {
                    "corresponding_author": {
                        "value": {
                            "param": {
                                "type": "group",
                                "regex": "~.*",
                                "optional": False
                            }
                        },
                        "description": "Specify which author (only one) is designated as the corresponding author. ACM requires that every submitted and published Work be assigned a single Corresponding Author. This Corresponding Author will be responsible for all direct communication and correspondence with ACM. They will also be responsible for obtaining ORCIDs from all listed co-authors, collecting and communicating declarations of potential Conflicts of Interest in connection with their papers on behalf of all listed co-authors, and completing ACM’s Rights Assignment process for their Work. The Corresponding Author is often the first-named author on the Work, but this need not be the case. The co-authors determine which author shall be the Corresponding Author for the Work, but there may only be one Corresponding Author.",
                        "order": 9,
                        "readers": [
                            "KDD.org/2026/Research_Track_August",
                            "KDD.org/2026/Research_Track_August/Submission${{4/id}/number}/Authors"
                        ]
                    }
                }
            }
        ))
        helpers.await_queue()
        helpers.await_queue_edit(openreview_client, 'KDD.org/2026/Research_Track_August/-/Post_Submission-0-0')
        helpers.await_queue_edit(openreview_client, 'KDD.org/2026/Research_Track_August/-/Full_Submission-0-0')

        full_submission =  openreview_client.get_invitation('KDD.org/2026/Research_Track_August/-/Full_Submission')

        assert 'authors' in full_submission.edit['invitation']['edit']['note']['content']
        assert 'readers' in full_submission.edit['invitation']['edit']['note']['content']['authors']
        assert full_submission.edit['invitation']['edit']['note']['content']['authors']['readers'] == ["KDD.org/2026/Research_Track_August", "KDD.org/2026/Research_Track_August/Submission${{4/id}/number}/Authors"]

        assert 'authorids' in full_submission.edit['invitation']['edit']['note']['content']
        assert 'readers' in full_submission.edit['invitation']['edit']['note']['content']['authorids']      
        assert full_submission.edit['invitation']['edit']['note']['content']['authorids']['readers'] == ["KDD.org/2026/Research_Track_August", "KDD.org/2026/Research_Track_August/Submission${{4/id}/number}/Authors"]        

        assert 'corresponding_author' in full_submission.edit['invitation']['edit']['note']['content']
        assert 'readers' in full_submission.edit['invitation']['edit']['note']['content']['corresponding_author']      
        assert full_submission.edit['invitation']['edit']['note']['content']['corresponding_author']['readers'] == ["KDD.org/2026/Research_Track_August", "KDD.org/2026/Research_Track_August/Submission${{4/id}/number}/Authors"]        

        submissions = openreview_client.get_notes(invitation='KDD.org/2026/Research_Track_August/-/Submission')
        assert len(submissions) == 5
        for submission in submissions:
            assert submission.readers == ["KDD.org/2026/Research_Track_August", 
                                          f"KDD.org/2026/Research_Track_August/Submission{submission.number}/Senior_Area_Chairs",
                                          f"KDD.org/2026/Research_Track_August/Submission{submission.number}/Area_Chairs",
                                          f"KDD.org/2026/Research_Track_August/Submission{submission.number}/Reviewers",
                                          f"KDD.org/2026/Research_Track_August/Submission{submission.number}/Authors"
                                          ]
            assert submission.content['corresponding_author']['value'] == '~SomeFirstName_User1'
            assert submission.content['corresponding_author']['readers'] == ["KDD.org/2026/Research_Track_August", f"KDD.org/2026/Research_Track_August/Submission{submission.number}/Authors"]        


        invitations = openreview_client.get_invitations(invitation='KDD.org/2026/Research_Track_August/-/Full_Submission')
        assert len(invitations) == 5
        for invitation in invitations:
            assert 'readers' in invitation.edit['note']['content']['corresponding_author']

        revision_note = test_client.post_note_edit(invitation='KDD.org/2026/Research_Track_August/Submission1/-/Full_Submission',
            signatures=['KDD.org/2026/Research_Track_August/Submission1/Authors'],
            note=openreview.api.Note(
                content={
                    'title': { 'value': 'Paper title 2 Updated' },
                    'abstract': { 'value': 'This is an abstract 2 updated' },
                    'authorids': { 'value': ['~SomeFirstName_User1', 'peter@mail.com', 'andrew@amazon.com'] },
                    'authors': { 'value': ['SomeFirstName User', 'Peter SomeLastName', 'Andrew Mc'] },
                    'keywords': { 'value': ['machine learning', 'nlp'] },
                    'corresponding_author': { 'value': '~SomeFirstName_User1'}
                }
            ))
        
        helpers.await_queue_edit(openreview_client, edit_id=revision_note['id'])            
    
    def test_revision_after_abstract_deadline(self, client, openreview_client, selenium, request_page, helpers):
        pc_client=openreview.Client(username='pc@kdd.org', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        now = datetime.datetime.now()
        due_date = now + datetime.timedelta(days=3)
        first_date = now + datetime.timedelta(days=1)

        pc_client.post_note(openreview.Note(
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Revision',
            forum=request_form.id,
            readers=['KDD.org/2026/Research_Track_August/Program_Chairs', 'openreview.net/Support'],
            referent=request_form.id,
            replyto=request_form.id,
            signatures=['~Program_KDDChair1'],
            writers=[],
            content={
                'title': 'KDD Research Track August',
                'Official Venue Name': 'KDD Research Track August',
                'Abbreviated Venue Name': 'KDD 2026',
                'Official Website URL': 'https://kdd.org',
                'program_chair_emails': ['pc@kdd.org', 'pc2@kdd.org'],
                'contact_email': 'pc@kdd.org',
                'publication_chairs':'No, our venue does not have Publication Chairs',
                'Venue Start Date': '2026/08/01',
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'abstract_registration_deadline': first_date.strftime('%Y/%m/%d'),
                'Location': 'Virtual',
                'submission_reviewer_assignment': 'Automatic',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100',
                'use_recruitment_template': 'Yes',
                'homepage_override': {
                    'instructions': '''**Authors**\nPlease see our [call for papers](https://kdd.org/Conferences/2026/CallForPapers) and read the [ethics guidelines](https://kdd.org/public/EthicsGuidelines)'''
                },
                'Additional Submission Options': {
                    "corresponding_author": {
                        "value": {
                            "param": {
                                "type": "group",
                                "regex": "~.*",
                                "optional": False
                            }
                        },
                        "description": "Specify which author (only one) is designated as the corresponding author. ACM requires that every submitted and published Work be assigned a single Corresponding Author. This Corresponding Author will be responsible for all direct communication and correspondence with ACM. They will also be responsible for obtaining ORCIDs from all listed co-authors, collecting and communicating declarations of potential Conflicts of Interest in connection with their papers on behalf of all listed co-authors, and completing ACM’s Rights Assignment process for their Work. The Corresponding Author is often the first-named author on the Work, but this need not be the case. The co-authors determine which author shall be the Corresponding Author for the Work, but there may only be one Corresponding Author.",
                        "order": 9,
                        "readers": [
                            "KDD.org/2026/Research_Track_August",
                            "KDD.org/2026/Research_Track_August/Submission${{4/id}/number}/Authors"
                        ]
                    }
                }
            }
        ))
        helpers.await_queue()
        helpers.await_queue_edit(openreview_client, 'KDD.org/2026/Research_Track_August/-/Full_Submission-0-1', count=4)

        full_submission =  openreview_client.get_invitation('KDD.org/2026/Research_Track_August/-/Full_Submission')

        assert 'authors' in full_submission.edit['invitation']['edit']['note']['content']
        assert 'readers' in full_submission.edit['invitation']['edit']['note']['content']['authors']
        assert full_submission.edit['invitation']['edit']['note']['content']['authors']['readers'] == ["KDD.org/2026/Research_Track_August", "KDD.org/2026/Research_Track_August/Submission${{4/id}/number}/Authors"]

        assert 'authorids' in full_submission.edit['invitation']['edit']['note']['content']
        assert 'readers' in full_submission.edit['invitation']['edit']['note']['content']['authorids']      
        assert full_submission.edit['invitation']['edit']['note']['content']['authorids']['readers'] == ["KDD.org/2026/Research_Track_August", "KDD.org/2026/Research_Track_August/Submission${{4/id}/number}/Authors"]        

        assert 'corresponding_author' in full_submission.edit['invitation']['edit']['note']['content']
        assert 'readers' in full_submission.edit['invitation']['edit']['note']['content']['corresponding_author']      
        assert full_submission.edit['invitation']['edit']['note']['content']['corresponding_author']['readers'] == ["KDD.org/2026/Research_Track_August", "KDD.org/2026/Research_Track_August/Submission${{4/id}/number}/Authors"]        


        submissions = openreview_client.get_notes(invitation='KDD.org/2026/Research_Track_August/-/Submission')
        assert len(submissions) == 5
        for submission in submissions:
            assert submission.readers == ["KDD.org/2026/Research_Track_August", 
                                          f"KDD.org/2026/Research_Track_August/Submission{submission.number}/Senior_Area_Chairs",
                                          f"KDD.org/2026/Research_Track_August/Submission{submission.number}/Area_Chairs",
                                          f"KDD.org/2026/Research_Track_August/Submission{submission.number}/Reviewers",
                                          f"KDD.org/2026/Research_Track_August/Submission{submission.number}/Authors"
                                          ]
            assert submission.content['corresponding_author']['value'] == '~SomeFirstName_User1'
            assert submission.content['corresponding_author']['readers'] == ["KDD.org/2026/Research_Track_August", f"KDD.org/2026/Research_Track_August/Submission{submission.number}/Authors"]


    def test_revision_after_full_submission(self, client, openreview_client, selenium, request_page, helpers):
        pc_client=openreview.Client(username='pc@kdd.org', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form')[0]

        now = datetime.datetime.now()
        start_date = now - datetime.timedelta(days=10)
        due_date = now - datetime.timedelta(days=3)
        first_date = now - datetime.timedelta(days=7)

        pc_client.post_note(openreview.Note(
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Revision',
            forum=request_form.id,
            readers=['KDD.org/2026/Research_Track_August/Program_Chairs', 'openreview.net/Support'],
            referent=request_form.id,
            replyto=request_form.id,
            signatures=['~Program_KDDChair1'],
            writers=[],
            content={
                'title': 'KDD Research Track August',
                'Official Venue Name': 'KDD Research Track August',
                'Abbreviated Venue Name': 'KDD 2026',
                'Official Website URL': 'https://kdd.org',
                'program_chair_emails': ['pc@kdd.org', 'pc2@kdd.org'],
                'contact_email': 'pc@kdd.org',
                'publication_chairs':'No, our venue does not have Publication Chairs',
                'Venue Start Date': '2026/08/01',
                'Submission Deadline': due_date.strftime('%Y/%m/%d %H:%M'),
                'Submission Start Date': start_date.strftime('%Y/%m/%d %H:%M'),
                'abstract_registration_deadline': first_date.strftime('%Y/%m/%d %H:%M'),
                'Location': 'Virtual',
                'submission_reviewer_assignment': 'Automatic',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '100',
                'use_recruitment_template': 'Yes',
                'homepage_override': {
                    'instructions': '''**Authors**\nPlease see our [call for papers](https://kdd.org/Conferences/2026/CallForPapers) and read the [ethics guidelines](https://kdd.org/public/EthicsGuidelines)'''
                },
                'Additional Submission Options': {
                    "corresponding_author": {
                        "value": {
                            "param": {
                                "type": "group",
                                "regex": "~.*",
                                "optional": False
                            }
                        },
                        "description": "Specify which author (only one) is designated as the corresponding author. ACM requires that every submitted and published Work be assigned a single Corresponding Author. This Corresponding Author will be responsible for all direct communication and correspondence with ACM. They will also be responsible for obtaining ORCIDs from all listed co-authors, collecting and communicating declarations of potential Conflicts of Interest in connection with their papers on behalf of all listed co-authors, and completing ACM’s Rights Assignment process for their Work. The Corresponding Author is often the first-named author on the Work, but this need not be the case. The co-authors determine which author shall be the Corresponding Author for the Work, but there may only be one Corresponding Author.",
                        "order": 9,
                        "readers": [
                            "KDD.org/2026/Research_Track_August",
                            "KDD.org/2026/Research_Track_August/Submission${{4/id}/number}/Authors"
                        ]
                    }
                }
            }
        ))
        helpers.await_queue()
        helpers.await_queue_edit(openreview_client, 'KDD.org/2026/Research_Track_August/-/Full_Submission-0-1', count=5) 

        submissions = openreview_client.get_notes(invitation='KDD.org/2026/Research_Track_August/-/Submission')
        assert len(submissions) == 5
        for submission in submissions:
            assert submission.readers == ["KDD.org/2026/Research_Track_August", 
                                          f"KDD.org/2026/Research_Track_August/Submission{submission.number}/Senior_Area_Chairs",
                                          f"KDD.org/2026/Research_Track_August/Submission{submission.number}/Area_Chairs",
                                          f"KDD.org/2026/Research_Track_August/Submission{submission.number}/Reviewers",
                                          f"KDD.org/2026/Research_Track_August/Submission{submission.number}/Authors"
                                          ]
            assert submission.content['corresponding_author']['value'] == '~SomeFirstName_User1'
            assert submission.content['corresponding_author']['readers'] == ["KDD.org/2026/Research_Track_August", f"KDD.org/2026/Research_Track_August/Submission{submission.number}/Authors"]             