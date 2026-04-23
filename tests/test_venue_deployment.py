import pytest
import datetime
import openreview

class TestVenueDeployment():

    def test_request_form_date_validation(self, openreview_client, helpers):

        helpers.create_user('programchair@venuedeployment.cc', 'ProgramChair', 'VenueDeployment')
        pc_client = openreview.api.OpenReviewClient(username='programchair@venuedeployment.cc', password=helpers.strong_password)

        now = datetime.datetime.now()

        with pytest.raises(openreview.OpenReviewException, match=r'The submission deadline must be in the future.'):
            request = pc_client.post_note_edit(
                invitation='openreview.net/Support/Venue_Request/-/Conference_Review_Workflow',
                signatures=['~ProgramChair_VenueDeployment1'],
                note=openreview.api.Note(
                    content={
                        'official_venue_name': { 'value': 'Test Venue Deployment Conference 2026' },
                        'abbreviated_venue_name': { 'value': 'TVD 2026' },
                        'venue_website_url': { 'value': 'https://venue-deployment-test.cc' },
                        'location': { 'value': 'Virtual' },
                        'venue_start_date': { 'value': openreview.tools.datetime_millis(now + datetime.timedelta(weeks=26)) },
                        'program_chair_emails': { 'value': ['programchair@venuedeployment.cc'] },
                        'contact_email': { 'value': 'programchair@venuedeployment.cc' },
                        'submission_start_date': { 'value': openreview.tools.datetime_millis(now - datetime.timedelta(days=10)) },
                        'submission_deadline': { 'value': openreview.tools.datetime_millis(now - datetime.timedelta(days=5)) },
                        'reviewer_role_name': { 'value': ['Reviewers'] },
                        'area_chair_role_name': { 'value': ['Area_Chairs'] },
                        'expected_submissions': { 'value': 50 },
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
            
        with pytest.raises(openreview.OpenReviewException, match=r'The submission start date must be before the submission deadline.'):
            request = pc_client.post_note_edit(
                invitation='openreview.net/Support/Venue_Request/-/Conference_Review_Workflow',
                signatures=['~ProgramChair_VenueDeployment1'],
                note=openreview.api.Note(
                    content={
                        'official_venue_name': { 'value': 'Test Venue Deployment Conference 2026' },
                        'abbreviated_venue_name': { 'value': 'TVD 2026' },
                        'venue_website_url': { 'value': 'https://venue-deployment-test.cc' },
                        'location': { 'value': 'Virtual' },
                        'venue_start_date': { 'value': openreview.tools.datetime_millis(now + datetime.timedelta(weeks=26)) },
                        'program_chair_emails': { 'value': ['programchair@venuedeployment.cc'] },
                        'contact_email': { 'value': 'programchair@venuedeployment.cc' },
                        'submission_start_date': { 'value': openreview.tools.datetime_millis(now + datetime.timedelta(days=3)) },
                        'submission_deadline': { 'value': openreview.tools.datetime_millis(now + datetime.timedelta(days=2)) },
                        'reviewer_role_name': { 'value': ['Reviewers'] },
                        'area_chair_role_name': { 'value': ['Area_Chairs'] },
                        'expected_submissions': { 'value': 50 },
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

        with pytest.raises(openreview.OpenReviewException, match=r'The full submission deadline must be after the submission deadline.'):
            request = pc_client.post_note_edit(
                invitation='openreview.net/Support/Venue_Request/-/Conference_Review_Workflow',
                signatures=['~ProgramChair_VenueDeployment1'],
                note=openreview.api.Note(
                    content={
                        'official_venue_name': { 'value': 'Test Venue Deployment Conference 2026' },
                        'abbreviated_venue_name': { 'value': 'TVD 2026' },
                        'venue_website_url': { 'value': 'https://venue-deployment-test.cc' },
                        'location': { 'value': 'Virtual' },
                        'venue_start_date': { 'value': openreview.tools.datetime_millis(now + datetime.timedelta(weeks=26)) },
                        'program_chair_emails': { 'value': ['programchair@venuedeployment.cc'] },
                        'contact_email': { 'value': 'programchair@venuedeployment.cc' },
                        'submission_start_date': { 'value': openreview.tools.datetime_millis(now) },
                        'submission_deadline': { 'value': openreview.tools.datetime_millis(now + datetime.timedelta(days=2)) },
                        'full_submission_deadline': { 'value': openreview.tools.datetime_millis(now + datetime.timedelta(days=1)) },
                        'reviewer_role_name': { 'value': ['Reviewers'] },
                        'area_chair_role_name': { 'value': ['Area_Chairs'] },
                        'expected_submissions': { 'value': 50 },
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

    def test_same_role_names_rejected(self, openreview_client, helpers):

        pc_client = openreview.api.OpenReviewClient(username='programchair@venuedeployment.cc', password=helpers.strong_password)
        now = datetime.datetime.now()
        due_date = now + datetime.timedelta(days=2)

        with pytest.raises(openreview.OpenReviewException, match=r'The reviewer role name and area chair role name must be different'):
            pc_client.post_note_edit(
                invitation='openreview.net/Support/Venue_Request/-/Conference_Review_Workflow',
                signatures=['~ProgramChair_VenueDeployment1'],
                note=openreview.api.Note(
                    content={
                        'official_venue_name': { 'value': 'Test Venue Deployment Conference 2026' },
                        'abbreviated_venue_name': { 'value': 'TVD 2026' },
                        'venue_website_url': { 'value': 'https://venue-deployment-test.cc' },
                        'location': { 'value': 'Virtual' },
                        'venue_start_date': { 'value': openreview.tools.datetime_millis(now + datetime.timedelta(weeks=26)) },
                        'program_chair_emails': { 'value': ['programchair@venuedeployment.cc'] },
                        'contact_email': { 'value': 'programchair@venuedeployment.cc' },
                        'submission_start_date': { 'value': openreview.tools.datetime_millis(now) },
                        'submission_deadline': { 'value': openreview.tools.datetime_millis(due_date) },
                        'reviewer_role_name': { 'value': ['Reviewers'] },
                        'area_chairs_support': { 'value': True },
                        'area_chair_role_name': { 'value': ['Reviewers'] },
                        'expected_submissions': { 'value': 50 },
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

    def test_new_role_name_fields_accepted(self, openreview_client, helpers):

        pc_client = openreview.api.OpenReviewClient(username='programchair@venuedeployment.cc', password=helpers.strong_password)
        now = datetime.datetime.now()
        due_date = now + datetime.timedelta(days=2)

        request = pc_client.post_note_edit(
            invitation='openreview.net/Support/Venue_Request/-/Conference_Review_Workflow',
            signatures=['~ProgramChair_VenueDeployment1'],
            note=openreview.api.Note(
                content={
                    'official_venue_name': { 'value': 'Test Venue Deployment Conference 2026' },
                    'abbreviated_venue_name': { 'value': 'TVD 2026' },
                    'venue_website_url': { 'value': 'https://venue-deployment-test.cc' },
                    'location': { 'value': 'Virtual' },
                    'venue_start_date': { 'value': openreview.tools.datetime_millis(now + datetime.timedelta(weeks=26)) },
                    'program_chair_emails': { 'value': ['programchair@venuedeployment.cc'] },
                    'contact_email': { 'value': 'programchair@venuedeployment.cc' },
                    'submission_start_date': { 'value': openreview.tools.datetime_millis(now) },
                    'submission_deadline': { 'value': openreview.tools.datetime_millis(due_date) },
                    'reviewer_role_name': { 'value': ['Program_Committee'] },
                    'area_chairs_support': { 'value': True },
                    'area_chair_role_name': { 'value': ['Senior_Program_Committee'] },
                    'expected_submissions': { 'value': 50 },
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

        request_note = openreview_client.get_note(request['note']['id'])
        assert request_note.content['reviewer_role_name']['value'] == ['Program_Committee']
        assert request_note.content['area_chair_role_name']['value'] == ['Senior_Program_Committee']

        # Deploy and verify role names propagate correctly
        support_group_id = 'openreview.net/Support'
        edit = openreview_client.post_note_edit(
            invitation='openreview.net/Support/Venue_Request/Conference_Review_Workflow/-/Deployment',
            signatures=[support_group_id],
            note=openreview.api.Note(
                id=request_note.id,
                content={
                    'venue_id': { 'value': 'TVD.cc/2026/Conference' }
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        venue_group = openreview_client.get_group('TVD.cc/2026/Conference')
        assert venue_group.content['reviewers_name']['value'] == 'Program_Committee'
        assert venue_group.content['area_chairs_name']['value'] == 'Senior_Program_Committee'

        assert openreview.tools.get_group(openreview_client, 'TVD.cc/2026/Conference/Program_Committee')
        assert openreview.tools.get_group(openreview_client, 'TVD.cc/2026/Conference/Senior_Program_Committee')