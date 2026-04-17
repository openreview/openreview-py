import datetime
import pytest
import openreview
from openreview.api import OpenReviewClient
from selenium.webdriver.common.by import By


class TestVenueRestriction():

    def test_setup(self, openreview_client, helpers):

        super_id = 'openreview.net'
        support_group_id = super_id + '/Support'

        helpers.create_user('programchair@restrict.cc', 'Program', 'ChairRestrict')
        helpers.create_user('author@restrict.cc', 'Author', 'Restrict')

        pc_client = openreview.api.OpenReviewClient(
            username='programchair@restrict.cc', password=helpers.strong_password
        )

        now = datetime.datetime.now()
        due_date = now + datetime.timedelta(days=3)

        request = pc_client.post_note_edit(
            invitation='openreview.net/Support/Venue_Request/-/Conference_Review_Workflow',
            signatures=['~Program_ChairRestrict1'],
            note=openreview.api.Note(
                content={
                    'official_venue_name': {'value': 'The Restrict Conference'},
                    'abbreviated_venue_name': {'value': 'RESTRICT 2025'},
                    'venue_website_url': {'value': 'https://restrict.cc/Conferences/2025'},
                    'location': {'value': 'Virtual'},
                    'venue_start_date': {'value': openreview.tools.datetime_millis(now + datetime.timedelta(weeks=52))},
                    'program_chair_emails': {'value': ['programchair@restrict.cc']},
                    'contact_email': {'value': 'programchair@restrict.cc'},
                    'submission_start_date': {'value': openreview.tools.datetime_millis(now)},
                    'submission_deadline': {'value': openreview.tools.datetime_millis(due_date)},
                    'reviewer_role_name': {'value': 'Reviewers'},
                    'area_chair_role_name': {'value': 'Area_Chairs'},
                    'colocated': {'value': 'Independent'},
                    'previous_venue': {'value': 'RESTRICT.cc/2024/Conference'},
                    'expected_submissions': {'value': 10},
                    'how_did_you_hear_about_us': {'value': 'We have used OpenReview for our previous conferences.'},
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
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=request['id'])

        request_note = openreview_client.get_note(request['note']['id'])
        assert request_note.domain == 'openreview.net/Support'

        # Deploy the venue
        edit = openreview_client.post_note_edit(
            invitation='openreview.net/Support/Venue_Request/Conference_Review_Workflow/-/Deployment',
            signatures=[support_group_id],
            note=openreview.api.Note(
                id=request_note.id,
                content={
                    'venue_id': {'value': 'RESTRICT.cc/2025/Conference'}
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        # Verify basic setup
        assert openreview.tools.get_group(openreview_client, 'RESTRICT.cc/2025/Conference')
        assert openreview.tools.get_group(openreview_client, 'RESTRICT.cc/2025/Conference/Program_Chairs')

        submission_inv = openreview_client.get_invitation('RESTRICT.cc/2025/Conference/-/Submission')
        assert submission_inv

    def test_restriction(self, openreview_client, helpers):

        pc_client = openreview.api.OpenReviewClient(
            username='programchair@restrict.cc', password=helpers.strong_password
        )
        author_client = openreview.api.OpenReviewClient(
            username='author@restrict.cc', password=helpers.strong_password
        )

        # Author submits a paper
        submission_edit = author_client.post_note_edit(
            invitation='RESTRICT.cc/2025/Conference/-/Submission',
            signatures=['~Author_Restrict1'],
            note=openreview.api.Note(
                license = 'CC BY 4.0',
                content={
                    'title': {'value': 'A Submission for Restriction Testing'},
                    'abstract': {'value': 'This paper tests venue restriction.'},
                    'authorids': {'value': ['~Author_Restrict1']},
                    'authors': {'value': ['Author Restrict']},
                    'pdf': {'value': '/pdf/' + 'p' * 40 + '.pdf'},
                    'keywords': {'value': ['testing', 'venue restriction']},
                    'email_sharing': { 'value': 'We authorize the sharing of all author emails with Program Chairs.' },
                    'data_release': { 'value': 'We authorize the release of our submission and author names to the public in the event of acceptance.' },                    
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=submission_edit['id'])

        submission_id = submission_edit['note']['id']

        # Verify the author can access the submission before restriction
        notes_before = author_client.get_notes(invitation='RESTRICT.cc/2025/Conference/-/Submission')
        assert len(notes_before) == 1
        assert notes_before[0].id == submission_id

        # PC restricts the venue
        pc_client.restrict('RESTRICT.cc/2025/Conference')

        # Author should no longer be able to access the submission data
        notes_after_author = author_client.get_notes(invitation='RESTRICT.cc/2025/Conference/-/Submission')
        assert len(notes_after_author) == 0, 'Author should not have access to notes after restriction'

        # PC should still be able to access the submission data
        notes_after_pc = pc_client.get_notes(invitation='RESTRICT.cc/2025/Conference/-/Submission')
        assert len(notes_after_pc) == 1, 'PC should still have access to notes after restriction'
        assert notes_after_pc[0].id == submission_id

        # Super client (admin) should also still have access
        notes_after_super = openreview_client.get_notes(invitation='RESTRICT.cc/2025/Conference/-/Submission')
        assert len(notes_after_super) == 1

        with pytest.raises(openreview.OpenReviewException) as openReviewError:
            author_client.get_note(submission_id)
        assert openReviewError.value.args[0].get('name') == 'NotFoundError'

        note = pc_client.get_note(submission_id)  # PC should still be able to access the note directly by ID
        assert note.id == submission_id

    def test_profile_edit_selenium(self, openreview_client, helpers, selenium, request_page):
        """
        Regression test: When the venue is restricted, authors visiting /profile
        should see their own profile — not be redirected to an unrelated public profile.
        """
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        author_client = openreview.api.OpenReviewClient(
            username='author@restrict.cc', password=helpers.strong_password
        )

        request_page(
            selenium,
            'http://localhost:3030/profile',
            author_client,
            wait_for_element='content'
        )

        # Wait for the title-container h1 to be present in the DOM.
        title_h1 = WebDriverWait(selenium, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'h1'))
        )

        # Assert the h1 shows the logged-in author's own name, not another user's.
        assert title_h1.text == 'Author Restrict', (
            f'Expected profile title to be "Author Restrict" but got "{title_h1.text}". '
            'Possible regression: page is showing a different user\'s profile.'
        )

    def test_submission_as_pc(self, openreview_client, helpers):
        """
        Regression test: When the venue is restricted, the PC should still be able
        to post a new submission and the process function must not fail.
        """
        pc_client = openreview.api.OpenReviewClient(
            username='programchair@restrict.cc', password=helpers.strong_password
        )

        # PC posts a new submission while the venue is restricted.
        # The process function associated with the Submission invitation must complete
        # without error (the regression caused it to fail due to the domain restriction).
        submission_edit = pc_client.post_note_edit(
            invitation='RESTRICT.cc/2025/Conference/-/Submission',
            signatures=['~Program_ChairRestrict1'],
            note=openreview.api.Note(
                license = 'CC BY 4.0',
                content={
                    'title': {'value': 'A PC Submission While Restricted'},
                    'abstract': {'value': 'Testing that the process function works when domain is restricted.'},
                    'authorids': {'value': ['~Program_ChairRestrict1']},
                    'authors': {'value': ['Program ChairRestrict']},
                    'pdf': {'value': '/pdf/' + 'p' * 40 + '.pdf'},
                    'keywords': {'value': ['testing', 'venue restriction']},
                    'email_sharing': { 'value': 'We authorize the sharing of all author emails with Program Chairs.' },
                    'data_release': { 'value': 'We authorize the release of our submission and author names to the public in the event of acceptance.' },                    
                }
            )
        )

        # Wait for the process function to complete and assert it did not error.
        helpers.await_queue_edit(openreview_client, edit_id=submission_edit['id'])

        # Verify the submission is visible to the PC
        notes = pc_client.get_notes(invitation='RESTRICT.cc/2025/Conference/-/Submission')
        assert len(notes) == 2, 'PC should see both submissions (author\'s and their own)'
