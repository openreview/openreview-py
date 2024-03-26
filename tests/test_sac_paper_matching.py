import csv
import os
import random
import openreview
import datetime

class TestSACAssignments():

    def test_create_conference(self, client, openreview_client, helpers):

        now = datetime.datetime.utcnow()
        due_date = now + datetime.timedelta(days=3)
        first_date = now + datetime.timedelta(days=1)

        # Post the request form note
        helpers.create_user('pc@matching.org', 'Program', 'MatchingChair')
        pc_client = openreview.Client(username='pc@matching.org', password=helpers.strong_password)

        helpers.create_user('sac@umass.edu', 'SAC', 'MatchingOne')
        helpers.create_user('sac2@ucla.edu', 'SAC', 'MatchingTwo')
        helpers.create_user('sac3@gmail.com', 'SAC', 'MatchingThree')

        request_form_note = pc_client.post_note(openreview.Note(
            invitation='openreview.net/Support/-/Request_Form',
            signatures=['~Program_MatchingChair1'],
            readers=[
                'openreview.net/Support',
                '~Program_MatchingChair1'
            ],
            writers=[],
            content={
                'title': 'Test SAC Matching Venue',
                'Official Venue Name': 'Test SAC Matching Venue',
                'Abbreviated Venue Name': 'SAC Matching 2024',
                'Official Website URL': 'https://2024.matching.org/',
                'program_chair_emails': ['pc@matching.org'],
                'contact_email': 'pc@matching.org',
                'publication_chairs':'No, our venue does not have Publication Chairs',
                'Area Chairs (Metareviewers)': 'Yes, our venue has Area Chairs',
                'senior_area_chairs': 'Yes, our venue has Senior Area Chairs',
                'senior_area_chairs_assignment': 'Submissions',
                'Venue Start Date': '2024/07/01',
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'Location': 'Amherst',
                'submission_reviewer_assignment': 'Automatic',
                'Author and Reviewer Anonymity': 'Double-blind',
                'reviewer_identity': ['Program Chairs', 'Assigned Senior Area Chair', 'Assigned Area Chair'],
                'area_chair_identity': ['Program Chairs', 'Assigned Senior Area Chair', 'Assigned Area Chair'],
                'senior_area_chair_identity': ['Program Chairs', 'Assigned Senior Area Chair'],
                'submission_readers': 'All program committee (all reviewers, all area chairs, all senior area chairs if applicable)',
                'How did you hear about us?': 'ML conferences',
                'email_pcs_for_withdrawn_submissions': 'No, do not email PCs.',
                'email_pcs_for_desk_rejected_submissions': 'No, do not email PCs.',
                'Expected Submissions': '50',
                'use_recruitment_template': 'Yes',
                'api_version': '2',
                'submission_license': ['CC BY 4.0']
            }))

        helpers.await_queue()

        # Post a deploy note
        client.post_note(openreview.Note(
            content={'venue_id': 'TSACM/2024/Conference'},
            forum=request_form_note.forum,
            invitation='openreview.net/Support/-/Request{}/Deploy'.format(request_form_note.number),
            readers=['openreview.net/Support'],
            referent=request_form_note.forum,
            replyto=request_form_note.forum,
            signatures=['openreview.net/Support'],
            writers=['openreview.net/Support']
        ))

        helpers.await_queue()

        assert openreview_client.get_group('TSACM/2024/Conference')
        assert openreview_client.get_group('TSACM/2024/Conference/Senior_Area_Chairs')

        assert openreview_client.get_invitation('TSACM/2024/Conference/-/Submission')

    def test_submit_papers(self, test_client, client, openreview_client, helpers):

        test_client = openreview.api.OpenReviewClient(username='test@mail.com', password=helpers.strong_password)

        domains = ['smith.edu', 'umass.edu', 'ucla.edu', 'meta.com']
        for i in range(1, 4):
            note = openreview.api.Note(
                content = {
                    'title': { 'value': 'Test Paper ' + str(i) },
                    'abstract': { 'value': 'This is a test abstract ' + str(i) },
                    'authorids': { 'value': ['test@mail.com', 'maria@' + domains[i-1]] },
                    'authors': { 'value': ['SomeFirstName User', 'Maria SomeLastName'] },
                    'keywords': { 'value': ['computer vision', 'nlp'] },
                    'pdf': {'value': '/pdf/' + 'p' * 40 +'.pdf' }
                }
            )

            test_client.post_note_edit(invitation='TSACM/2024/Conference/-/Submission',
                signatures=['~SomeFirstName_User1'],
                note=note)  
            
        #close submissions
        now = datetime.datetime.utcnow()
        due_date = now - datetime.timedelta(days=1)

        pc_client = openreview.Client(username='pc@matching.org', password=helpers.strong_password)
        request_form=client.get_notes(invitation='openreview.net/Support/-/Request_Form', sort='tmdate')[0]

        venue_revision_note = pc_client.post_note(openreview.Note(
            content={
                'title': 'Test SAC Matching Venue',
                'Official Venue Name': 'Test SAC Matching Venue',
                'Abbreviated Venue Name': 'SAC Matching 2024',
                'Official Website URL': 'https://2024.matching.org/',
                'program_chair_emails': ['pc@matching.org'],
                'contact_email': 'pc@matching.org',
                'publication_chairs':'No, our venue does not have Publication Chairs',
                'Venue Start Date': '2024/07/01',
                'Submission Deadline': due_date.strftime('%Y/%m/%d'),
                'Location': 'Amherst',
                'submission_reviewer_assignment': 'Automatic',
                'How did you hear about us?': 'ML conferences',
                'Expected Submissions': '50',
                'use_recruitment_template': 'Yes',
            },
            forum=request_form.forum,
            invitation='openreview.net/Support/-/Request{}/Revision'.format(request_form.number),
            readers=['{}/Program_Chairs'.format('TSACM/2024/Conference'), 'openreview.net/Support'],
            referent=request_form.forum,
            replyto=request_form.forum,
            signatures=['~Program_MatchingChair1'],
            writers=[]
        ))

        helpers.await_queue()

    def test_setup_matching(self, client, openreview_client, helpers):

        pc_client = openreview.Client(username='pc@matching.org', password=helpers.strong_password)
        request_form=pc_client.get_notes(invitation='openreview.net/Support/-/Request_Form', sort='tmdate')[0]

        submissions = openreview_client.get_notes(invitation='TSACM/2024/Conference/-/Submission', sort='number:asc')

        ## setup matching with no SACs
        matching_setup_note = pc_client.post_note(openreview.Note(
            content={
                'title': 'Paper Matching Setup',
                'matching_group': 'TSACM/2024/Conference/Senior_Area_Chairs',
                'compute_conflicts': 'Default',
                'compute_affinity_scores': 'No'

            },
            forum=request_form.id,
            replyto=request_form.id,
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Paper_Matching_Setup',
            readers=['TSACM/2024/Conference/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_MatchingChair1'],
            writers=[]
        ))
        helpers.await_queue()

        comment_invitation_id = f'openreview.net/Support/-/Request{request_form.number}/Paper_Matching_Setup_Status'
        matching_status = client.get_notes(invitation=comment_invitation_id, replyto=matching_setup_note.id, forum=request_form.forum, sort='tmdate')[0]
        assert matching_status
        assert 'Could not compute affinity scores and conflicts since there are no Senior Area Chairs. You can use the \'Recruitment\' button to recruit Senior Area Chairs.' in matching_status.content['error']

        openreview_client.add_members_to_group(
            'TSACM/2024/Conference/Senior_Area_Chairs', 
            ['~SAC_MatchingOne1', '~SAC_MatchingTwo1', '~SAC_MatchingThree1']
        )

        with open(os.path.join(os.path.dirname(__file__), 'data/sac_scores_matching.csv'), 'w') as file_handle:
            writer = csv.writer(file_handle)
            for submission in submissions:
                for sac in openreview_client.get_group('TSACM/2024/Conference/Senior_Area_Chairs').members:
                    writer.writerow([submission.id, sac, round(random.random(), 2)])

        affinity_scores_url = client.put_attachment(os.path.join(os.path.dirname(__file__), 'data/sac_scores_matching.csv'), f'openreview.net/Support/-/Request{request_form.number}/Paper_Matching_Setup', 'upload_affinity_scores')
        
        ## setup matching to assign SAC to papers
        matching_setup_note = client.post_note(openreview.Note(
            content={
                'title': 'Paper Matching Setup',
                'matching_group': 'TSACM/2024/Conference/Senior_Area_Chairs',
                'compute_conflicts': 'Default',
                'compute_affinity_scores': 'No',
                'upload_affinity_scores': affinity_scores_url

            },
            forum=request_form.id,
            replyto=request_form.id,
            invitation=f'openreview.net/Support/-/Request{request_form.number}/Paper_Matching_Setup',
            readers=['TSACM/2024/Conference/Program_Chairs', 'openreview.net/Support'],
            signatures=['~Program_MatchingChair1'],
            writers=[]
        ))

        helpers.await_queue()

        comment_invitation_id = f'openreview.net/Support/-/Request{request_form.number}/Paper_Matching_Setup_Status'
        matching_status = client.get_notes(invitation=comment_invitation_id, replyto=matching_setup_note.id, forum=request_form.forum, sort='tmdate')[0]
        assert matching_status
        assert matching_status.content['comment'] == '''Affinity scores and/or conflicts were successfully computed. To run the matcher, click on the 'Senior Area Chairs Paper Assignment' link in the PC console: https://openreview.net/group?id=TSACM/2024/Conference/Program_Chairs

Please refer to the documentation for instructions on how to run the matcher: https://docs.openreview.net/how-to-guides/paper-matching-and-assignment/how-to-do-automatic-assignments'''

        scores_invitation = openreview_client.get_invitation('TSACM/2024/Conference/Senior_Area_Chairs/-/Affinity_Score')
        assert scores_invitation
        affinity_scores = openreview_client.get_edges_count(invitation=scores_invitation.id)
        assert affinity_scores == 9

        conflict_invitation = openreview_client.get_invitation('TSACM/2024/Conference/Senior_Area_Chairs/-/Conflict')
        assert conflict_invitation
        conflicts = openreview_client.get_edges_count(invitation=conflict_invitation.id)
        assert conflicts