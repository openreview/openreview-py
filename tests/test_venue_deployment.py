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
                                'We acknowledge that role participation will be collected for all participants—reviewers, area chairs, and senior area chairs—and made publicly available in the OpenReview profile of each participant.',
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
                                'We acknowledge that role participation will be collected for all participants—reviewers, area chairs, and senior area chairs—and made publicly available in the OpenReview profile of each participant.',
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
                                'We acknowledge that role participation will be collected for all participants—reviewers, area chairs, and senior area chairs—and made publicly available in the OpenReview profile of each participant.',
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
                        'reviewer_groups_names': { 'value': ['Reviewers'] },
                        'area_chairs_support': { 'value': True },
                        'area_chair_groups_names': { 'value': ['Reviewers'] },
                        'senior_area_chair_groups_names': { 'value': ['Senior_Area_Chairs'] },
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
                                'We acknowledge that role participation will be collected for all participants—reviewers, area chairs, and senior area chairs—and made publicly available in the OpenReview profile of each participant.',
                                'We acknowledge that metadata for accepted papers will be publicly released in OpenReview.'
                            ]
                        }
                    }
                ))

        with pytest.raises(openreview.OpenReviewException, match=r'The senior area chair role name and reviewer role name must be different'):
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
                        'reviewer_groups_names': { 'value': ['Reviewers'] },
                        'area_chairs_support': { 'value': True },
                        'area_chair_groups_names': { 'value': ['Area_Chairs'] },
                        'senior_area_chairs_support': { 'value': True },
                        'senior_area_chair_groups_names': { 'value': ['Reviewers'] },
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
                                'We acknowledge that role participation will be collected for all participants—reviewers, area chairs, and senior area chairs—and made publicly available in the OpenReview profile of each participant.',
                                'We acknowledge that metadata for accepted papers will be publicly released in OpenReview.'
                            ]
                        }
                    }
                ))

        with pytest.raises(openreview.OpenReviewException, match=r'The senior area chair role name and area chair role name must be different'):
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
                        'reviewer_groups_names': { 'value': ['Reviewers'] },
                        'area_chairs_support': { 'value': True },
                        'area_chair_groups_names': { 'value': ['Area_Chairs'] },
                        'senior_area_chairs_support': { 'value': True },
                        'senior_area_chair_groups_names': { 'value': ['Area_Chairs'] },
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
                                'We acknowledge that role participation will be collected for all participants—reviewers, area chairs, and senior area chairs—and made publicly available in the OpenReview profile of each participant.',
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
                    'reviewer_groups_names': { 'value': ['Program_Committee'] },
                    'area_chairs_support': { 'value': True },
                    'area_chair_groups_names': { 'value': ['Senior_Program_Committee'] },
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
                            'We acknowledge that role participation will be collected for all participants—reviewers, area chairs, and senior area chairs—and made publicly available in the OpenReview profile of each participant.',
                            'We acknowledge that metadata for accepted papers will be publicly released in OpenReview.'
                        ]
                    }
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=request['id'])

        request_note = openreview_client.get_note(request['note']['id'])
        assert request_note.content['reviewer_groups_names']['value'] == ['Program_Committee']
        assert request_note.content['area_chair_groups_names']['value'] == ['Senior_Program_Committee']

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

    def test_rename_reschedules_date_processes(self, openreview_client, helpers):

        # Regression test: when a venue is renamed to a new domain, its date process
        # functions must be re-scheduled under the new domain (the rename moves the
        # process logs and queued jobs to the new domain), and nothing must be left
        # pointing at the old domain. This is handled by the API rename.

        super_id = 'openreview.net'
        support_group_id = super_id + '/Support'

        helpers.create_user('programchair@venuerename.cc', 'ProgramChair', 'VenueRename')
        pc_client = openreview.api.OpenReviewClient(username='programchair@venuerename.cc', password=helpers.strong_password)

        now = datetime.datetime.now()
        due_date = now + datetime.timedelta(days=2)

        # 1. create and deploy a venue
        request = pc_client.post_note_edit(
            invitation='openreview.net/Support/Venue_Request/-/Conference_Review_Workflow',
            signatures=['~ProgramChair_VenueRename1'],
            note=openreview.api.Note(
                content={
                    'official_venue_name': { 'value': 'Test Venue Rename Conference 2026' },
                    'abbreviated_venue_name': { 'value': 'TVRN 2026' },
                    'venue_website_url': { 'value': 'https://venue-rename-test.cc' },
                    'location': { 'value': 'Virtual' },
                    'venue_start_date': { 'value': openreview.tools.datetime_millis(now + datetime.timedelta(weeks=26)) },
                    'program_chair_emails': { 'value': ['programchair@venuerename.cc'] },
                    'contact_email': { 'value': 'programchair@venuerename.cc' },
                    'submission_start_date': { 'value': openreview.tools.datetime_millis(now) },
                    'submission_deadline': { 'value': openreview.tools.datetime_millis(due_date) },
                    'reviewer_groups_names': { 'value': ['Reviewers'] },
                    'area_chairs_support': { 'value': True },
                    'area_chair_groups_names': { 'value': ['Area_Chairs'] },
                    'senior_area_chair_groups_names': { 'value': ['Senior_Area_Chairs'] },
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

        venue_id = 'TVRN.cc/2026/Conference'
        renamed_venue_id = 'TVRN.org/2026/Conference'

        edit = openreview_client.post_note_edit(
            invitation='openreview.net/Support/Venue_Request/Conference_Review_Workflow/-/Deployment',
            signatures=[support_group_id],
            note=openreview.api.Note(
                id=request_note.id,
                content={ 'venue_id': { 'value': venue_id } }
            ))
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])
        helpers.await_queue_edit(openreview_client, edit_id=f'{venue_id}/-/Withdrawal-0-1', count=1)

        assert openreview.tools.get_group(openreview_client, venue_id)
        assert openreview.tools.get_invitation(openreview_client, f'{venue_id}/-/Withdrawal').date_processes
        assert openreview.tools.get_invitation(openreview_client, f'{venue_id}/-/Preferred_Emails').date_processes

        # Schedule the Withdrawal cdate date process (-0-0) to run a few minutes from now,
        # so it is still a pending (in-flight) job when we rename. This lets us verify the
        # rename re-schedules the pending job to actually run under the new domain. The
        # request form rejects past dates, but the /Dates invitation lets us set the
        # activation date directly.
        activation_date = openreview.tools.datetime_millis(datetime.datetime.now() + datetime.timedelta(minutes=3))
        dates_edit = pc_client.post_invitation_edit(
            invitations=f'{venue_id}/-/Withdrawal/Dates',
            content={
                'activation_date': { 'value': activation_date },
                'expiration_date': { 'value': openreview.tools.datetime_millis(datetime.datetime.now() + datetime.timedelta(weeks=52)) }
            })
        helpers.await_queue_edit(openreview_client, edit_id=dates_edit['id'])

        # the -0-0 cdate process must be scheduled but not yet executed
        assert openreview.tools.get_invitation(openreview_client, f'{venue_id}/-/Withdrawal').cdate == activation_date
        assert not [
            log for log in openreview_client.get_process_logs(id=f'{venue_id}/-/Withdrawal-0-0')
            if log['status'] in ['running', 'ok', 'error']
        ]

        # 2. rename the venue to a new domain
        openreview_client.rename_venue(venue_id, renamed_venue_id, request_note.id)
        helpers.await_queue(openreview_client, queue_names=['internalQueueMQStatus'])

        assert openreview.tools.get_group(openreview_client, renamed_venue_id)

        # 3. the date processes must be re-scheduled under the new domain
        helpers.await_queue_edit(openreview_client, edit_id=f'{renamed_venue_id}/-/Withdrawal-0-1', count=1)

        assert openreview.tools.get_invitation(openreview_client, f'{renamed_venue_id}/-/Withdrawal')
        assert openreview.tools.get_invitation(openreview_client, f'{renamed_venue_id}/-/Withdrawal/Dates')

        renamed_preferred_emails = openreview.tools.get_invitation(openreview_client, f'{renamed_venue_id}/-/Preferred_Emails')
        assert renamed_preferred_emails
        assert renamed_preferred_emails.date_processes

        # 4. nothing must be left pointing at the old domain: the invitation is gone and
        #    no process logs remain under the old name (they were moved to the new domain)
        assert openreview.tools.get_invitation(openreview_client, f'{venue_id}/-/Preferred_Emails') is None
        assert not openreview_client.get_process_logs(invitation=f'{venue_id}/-/Preferred_Emails')

        # 5. the pending Withdrawal -0-0 date process must actually execute under the new
        #    domain (the rename re-scheduled the in-flight job to run under the new domain),
        #    and it must not run under the old domain
        helpers.await_queue_edit(openreview_client, edit_id=f'{renamed_venue_id}/-/Withdrawal-0-0', count=1)
        assert not [
            log for log in openreview_client.get_process_logs(id=f'{venue_id}/-/Withdrawal-0-0')
            if log['status'] in ['running', 'ok', 'error']
        ]

        
    def test_cancel_request(self, openreview_client, helpers):

        ## the requester or the support team can cancel a request that is still in the queue
        ## (e.g. we asked for more information and the requester never replied) by setting the
        ## note ddate through the Cancel_Request invitation
        helpers.create_user('programchair@venuedeployment.cc', 'ProgramChair', 'VenueDeployment')
        pc_client = openreview.api.OpenReviewClient(username='programchair@venuedeployment.cc', password=helpers.strong_password)
        support_group_id = 'openreview.net/Support'
        cancel_invitation_id = 'openreview.net/Support/Venue_Request/Conference_Review_Workflow/-/Cancel_Request'
        now = datetime.datetime.now()

        agreement_value = [
            'OpenReview natively supports a wide variety of reviewing workflow configurations. However, if we want significant reviewing process customizations or experiments, we will detail these requests to the OpenReview staff at least three months in advance.',
            'We will ask authors and reviewers to create an OpenReview Profile at least two weeks in advance of the paper submission deadlines.',
            'When assembling our group of reviewers, we will only include email addresses or OpenReview Profile IDs of people we know to have authored publications relevant to our venue.  (We will not solicit new reviewers using an open web form, because unfortunately some malicious actors sometimes try to create "fake ids" aiming to be assigned to review their own paper submissions.)',
            'We acknowledge that, if our venue\'s reviewing workflow is non-standard, or if our venue is expecting more than a few hundred submissions for any one deadline, we should designate our own Workflow Chair, who will read the OpenReview documentation and manage our workflow configurations throughout the reviewing process.',
            'We acknowledge that OpenReview staff work Monday-Friday during standard business hours US Eastern time, and we cannot expect support responses outside those times.  For this reason, we recommend setting submission and reviewing deadlines Monday through Thursday.',
            'We will treat the OpenReview staff with kindness and consideration.',
            'We acknowledge that authors and reviewers will be required to share their preferred email.',
            'We acknowledge that role participation will be collected for all participants—reviewers, area chairs, and senior area chairs—and made publicly available in the OpenReview profile of each participant.',
            'We acknowledge that metadata for accepted papers will be publicly released in OpenReview.'
        ]

        def post_request(name):
            request = pc_client.post_note_edit(
                invitation='openreview.net/Support/Venue_Request/-/Conference_Review_Workflow',
                signatures=['~ProgramChair_VenueDeployment1'],
                note=openreview.api.Note(
                    content={
                        'official_venue_name': { 'value': name },
                        'abbreviated_venue_name': { 'value': name },
                        'venue_website_url': { 'value': 'https://venue-deployment-test.cc' },
                        'location': { 'value': 'Virtual' },
                        'venue_start_date': { 'value': openreview.tools.datetime_millis(now + datetime.timedelta(weeks=26)) },
                        'program_chair_emails': { 'value': ['programchair@venuedeployment.cc'] },
                        'contact_email': { 'value': 'programchair@venuedeployment.cc' },
                        'submission_start_date': { 'value': openreview.tools.datetime_millis(now + datetime.timedelta(days=2)) },
                        'submission_deadline': { 'value': openreview.tools.datetime_millis(now + datetime.timedelta(days=20)) },
                        'expected_submissions': { 'value': 50 },
                        'venue_organizer_agreement': { 'value': agreement_value }
                    }
                ))
            helpers.await_queue_edit(openreview_client, edit_id=request['id'])
            return request['note']['id']

        ## the requester can cancel their own request
        request_note_id = post_request('Cancel By Requester 2026')
        assert openreview_client.get_note(request_note_id).ddate is None

        ## Cancel_Request has no process function, so the ddate edit applies synchronously
        cancel_ddate = openreview.tools.datetime_millis(now)
        pc_client.post_note_edit(
            invitation=cancel_invitation_id,
            signatures=['~ProgramChair_VenueDeployment1'],
            note=openreview.api.Note(
                id=request_note_id,
                ddate=cancel_ddate
            ))
        ## the note is deleted: its ddate matches the value we posted and it no longer
        ## appears in the active request queue
        assert openreview_client.get_note(request_note_id).ddate == cancel_ddate
        active_request_ids = [ n.id for n in openreview_client.get_notes(invitation='openreview.net/Support/Venue_Request/-/Conference_Review_Workflow') ]
        assert request_note_id not in active_request_ids

        ## the support team can cancel a request
        request_note_id = post_request('Cancel By Support 2026')
        assert openreview_client.get_note(request_note_id).ddate is None

        cancel_ddate = openreview.tools.datetime_millis(now)
        openreview_client.post_note_edit(
            invitation=cancel_invitation_id,
            signatures=[support_group_id],
            note=openreview.api.Note(
                id=request_note_id,
                ddate=cancel_ddate
            ))
        assert openreview_client.get_note(request_note_id).ddate == cancel_ddate
        active_request_ids = [ n.id for n in openreview_client.get_notes(invitation='openreview.net/Support/Venue_Request/-/Conference_Review_Workflow') ]
        assert request_note_id not in active_request_ids

