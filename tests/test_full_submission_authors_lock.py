import datetime
import pytest
import openreview
from openreview.api import Note, OpenReviewClient


class TestFullSubmissionAuthorsLock():

    def test_setup(self, openreview_client, helpers):

        super_id = 'openreview.net'
        support_group_id = super_id + '/Support'

        helpers.create_user('programchair@flock.cc', 'ProgramChair', 'FLOCK')
        helpers.create_user('author_one@flock.cc', 'AuthorOne', 'FLOCK')
        helpers.create_user('author_two@flock.cc', 'AuthorTwo', 'FLOCK')
        helpers.create_user('author_three@flock.cc', 'AuthorThree', 'FLOCK')
        pc_client = openreview.api.OpenReviewClient(username='programchair@flock.cc', password=helpers.strong_password)

        now = datetime.datetime.now()
        due_date = now + datetime.timedelta(days=2)
        full_submission_due_date = due_date + datetime.timedelta(days=4)

        request = pc_client.post_note_edit(invitation='openreview.net/Support/Venue_Request/-/Conference_Review_Workflow',
            signatures=['~ProgramChair_FLOCK1'],
            note=openreview.api.Note(
                content={
                    'official_venue_name': { 'value': 'Full Submission Lock Conference' },
                    'abbreviated_venue_name': { 'value': 'FLOCK 2026' },
                    'venue_website_url': { 'value': 'https://flock.cc/Conferences/2026' },
                    'location': { 'value': 'Online' },
                    'venue_start_date': { 'value': openreview.tools.datetime_millis(now + datetime.timedelta(weeks=52)) },
                    'program_chair_emails': { 'value': ['programchair@flock.cc'] },
                    'contact_email': { 'value': 'flock2026.programchairs@gmail.com' },
                    'submission_start_date': { 'value': openreview.tools.datetime_millis(now - datetime.timedelta(days=1)) },
                    'submission_deadline': { 'value': openreview.tools.datetime_millis(due_date) },
                    'full_submission_deadline': { 'value': openreview.tools.datetime_millis(full_submission_due_date) },
                    'reviewer_groups_names': { 'value': ['Reviewers'] },
                    'area_chair_groups_names': { 'value': ['Area_Chairs'] },
                    'senior_area_chair_groups_names': { 'value': ['Senior_Area_Chairs'] },
                    'expected_submissions': { 'value': 5 },
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
        edit = openreview_client.post_note_edit(
            invitation='openreview.net/Support/Venue_Request/Conference_Review_Workflow/-/Deployment',
            signatures=[support_group_id],
            note=openreview.api.Note(
                id=request['note']['id'],
                content={
                    'venue_id': { 'value': 'flock.cc/2026/Conference' }
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])
        helpers.await_queue_edit(openreview_client, 'flock.cc/2026/Conference/-/Full_Submission-0-1', count=1)

        assert openreview_client.get_invitation('flock.cc/2026/Conference/-/Submission')
        assert openreview_client.get_invitation('flock.cc/2026/Conference/-/Full_Submission')
        assert openreview_client.get_invitation('flock.cc/2026/Conference/-/Full_Submission/Form_Fields')

    def test_post_abstract_submission(self, openreview_client, test_client, helpers):

        test_client = openreview.api.OpenReviewClient(token=test_client.token)

        edit = test_client.post_note_edit(
            invitation='flock.cc/2026/Conference/-/Submission',
            signatures=['~SomeFirstName_User1'],
            note=openreview.api.Note(
                license='CC BY 4.0',
                content={
                    'title': { 'value': 'Locked Authors Submission' },
                    'abstract': { 'value': 'Abstract for the locked-authors test.' },
                    'authors': {
                        'value': [
                            {
                                'fullname': 'SomeFirstName User',
                                'username': '~SomeFirstName_User1',
                                'institutions': [{ 'domain': 'mail.com', 'country': 'US' }]
                            },
                            {
                                'fullname': 'AuthorOne FLOCK',
                                'username': '~AuthorOne_FLOCK1',
                                'institutions': [{ 'domain': 'flock.cc', 'country': 'US' }]
                            },
                            {
                                'fullname': 'AuthorTwo FLOCK',
                                'username': '~AuthorTwo_FLOCK1',
                                'institutions': [{ 'domain': 'flock.cc', 'country': 'US' }]
                            }
                        ]
                    },
                    'keywords': { 'value': ['locking', 'authors'] },
                    'email_sharing': { 'value': 'We authorize the sharing of all author emails with Program Chairs.' },
                    'data_release': { 'value': 'We authorize the release of our submission and author names to the public in the event of acceptance.' },
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        submissions = openreview_client.get_notes(invitation='flock.cc/2026/Conference/-/Submission', sort='number:asc')
        assert len(submissions) == 1
        assert submissions[0].authorids == ['~SomeFirstName_User1', '~AuthorOne_FLOCK1', '~AuthorTwo_FLOCK1']

    def test_close_abstract_deadline(self, openreview_client, helpers):
        '''Close the abstract deadline so the per-paper Full_Submission invitations
        are materialized.'''

        pc_client = openreview.api.OpenReviewClient(username='programchair@flock.cc', password=helpers.strong_password)

        now = datetime.datetime.now()
        new_duedate = openreview.tools.datetime_millis(now - datetime.timedelta(minutes=30))
        submission_inv = pc_client.get_invitation('flock.cc/2026/Conference/-/Submission')

        edit = pc_client.post_invitation_edit(
            invitations='flock.cc/2026/Conference/-/Submission/Dates',
            content={
                'activation_date': { 'value': submission_inv.cdate },
                'due_date': { 'value': new_duedate }
            }
        )

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])
        # Wait for Full_Submission to activate and materialize per-paper invitations
        helpers.await_queue_edit(openreview_client, 'flock.cc/2026/Conference/-/Full_Submission-0-1', count=2)

        per_paper_full_submission = pc_client.get_invitation('flock.cc/2026/Conference/Submission1/-/Full_Submission')
        assert per_paper_full_submission

    def test_lock_full_submission_authors(self, openreview_client, helpers):
        '''After the abstract deadline, override the Full_Submission authors field so it
        is a $ reference to the current submission's authors. This should let authors
        re-order the list but not add or remove any.'''

        pc_client = openreview.api.OpenReviewClient(username='programchair@flock.cc', password=helpers.strong_password)

        full_submission_inv = pc_client.get_invitation('flock.cc/2026/Conference/-/Full_Submission')
        content = full_submission_inv.edit['invitation']['edit']['note']['content']

        # Replace the authors field schema with a $ reference to the current submission's authors.
        content['authors'] = {
            'value': ['${{4/id}/content/authors/value}'],
            'order': content.get('authors', {}).get('order', 2)
        }

        pc_client.post_invitation_edit(
            invitations='flock.cc/2026/Conference/-/Full_Submission/Form_Fields',
            content={
                'content': {
                    'value': content
                },
                'license': {
                    'value': [
                        {'value': 'CC BY 4.0', 'description': 'CC BY 4.0'}
                    ]
                }
            }
        )

        helpers.await_queue_edit(openreview_client, edit_id='flock.cc/2026/Conference/-/Full_Submission-0-1', count=3)

        # Confirm the schema was updated
        full_submission_inv = pc_client.get_invitation('flock.cc/2026/Conference/-/Full_Submission')
        new_authors_schema = full_submission_inv.edit['invitation']['edit']['note']['content']['authors']
        assert new_authors_schema['value'] == ['${{4/id}/content/authors/value}']

    def _full_submission_content(self, submission, authors_value):
        return {
            'title': submission.content['title'],
            'abstract': submission.content['abstract'],
            'keywords': submission.content['keywords'],
            'authors': { 'value': authors_value },
            'email_sharing': submission.content['email_sharing'],
            'data_release': submission.content['data_release'],
        }

    def test_full_submission_reorder_authors_succeeds(self, openreview_client, test_client, helpers):
        '''Posting a Full_Submission revision that reorders the authors should be allowed.'''

        test_client = openreview.api.OpenReviewClient(token=test_client.token)

        submissions = openreview_client.get_notes(invitation='flock.cc/2026/Conference/-/Submission', sort='number:asc')
        submission = submissions[0]
        original_authors = submission.content['authors']['value']

        # Reorder: move AuthorTwo to the front, keep all three.
        reordered = [original_authors[2], original_authors[0], original_authors[1]]

        revision = test_client.post_note_edit(
            invitation=f'flock.cc/2026/Conference/Submission{submission.number}/-/Full_Submission',
            signatures=[f'flock.cc/2026/Conference/Submission{submission.number}/Authors'],
            note=openreview.api.Note(
                license='CC BY 4.0',
                content=self._full_submission_content(submission, reordered)
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=revision['id'])

        submission = openreview_client.get_note(submission.id)
        assert submission.authorids == [a['username'] for a in reordered]
        assert submission.authorids == ['~AuthorTwo_FLOCK1', '~SomeFirstName_User1', '~AuthorOne_FLOCK1']

    def test_full_submission_remove_author_fails(self, openreview_client, test_client, helpers):
        '''Posting a Full_Submission revision that removes an author should be rejected
        because the authors field is locked to a $ reference of the current value.'''

        test_client = openreview.api.OpenReviewClient(token=test_client.token)

        submissions = openreview_client.get_notes(invitation='flock.cc/2026/Conference/-/Submission', sort='number:asc')
        submission = submissions[0]
        current_authors = submission.content['authors']['value']

        # Drop one author from the list — should be rejected.
        truncated = current_authors[:-1]

        with pytest.raises(openreview.OpenReviewException):
            test_client.post_note_edit(
                invitation=f'flock.cc/2026/Conference/Submission{submission.number}/-/Full_Submission',
                signatures=[f'flock.cc/2026/Conference/Submission{submission.number}/Authors'],
                note=openreview.api.Note(
                    license='CC BY 4.0',
                    content=self._full_submission_content(submission, truncated)
                )
            )
