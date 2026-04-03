import pytest
import datetime
import openreview

class TestVenueDeployment():

    def test_deploy_venue(self, openreview_client, helpers):

        super_id = 'openreview.net'
        support_group_id = super_id + '/Support'

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
                        'reviewers_name': { 'value': 'Reviewers' },
                        'area_chairs_name': { 'value': 'Area_Chairs' },
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
                        'reviewers_name': { 'value': 'Reviewers' },
                        'area_chairs_name': { 'value': 'Area_Chairs' },
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
                        'reviewers_name': { 'value': 'Reviewers' },
                        'area_chairs_name': { 'value': 'Area_Chairs' },
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