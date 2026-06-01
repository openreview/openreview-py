import datetime
import pytest
import openreview
from openreview.api import Note, OpenReviewClient


class TestSubmissionAuthorsEmail():
    '''Covers entering submission authors by email address instead of profile ID,
    using the unified ``author{}`` schema. The default schema constrains the
    ``username`` field to a profile ID (regex ``^~\\S+$``); this test relaxes that
    regex on the Submission invitation so a venue can opt into email-based authors,
    then posts a few submissions whose authors are entered by email.'''

    # profile-id-or-email regex, matching the force_profiles authorids field
    profile_or_email_regex = r"^~\S+$|^[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$"

    def test_setup(self, openreview_client, helpers):

        super_id = 'openreview.net'
        support_group_id = super_id + '/Support'

        helpers.create_user('programchair@eauth.cc', 'ProgramChair', 'EAUTH')
        helpers.create_user('author_one@eauth.cc', 'AuthorOne', 'EAUTH')
        helpers.create_user('author_two@eauth.cc', 'AuthorTwo', 'EAUTH')
        pc_client = openreview.api.OpenReviewClient(username='programchair@eauth.cc', password=helpers.strong_password)

        now = datetime.datetime.now()
        due_date = now + datetime.timedelta(days=2)
        full_submission_due_date = due_date + datetime.timedelta(days=4)

        request = pc_client.post_note_edit(invitation='openreview.net/Support/Venue_Request/-/Conference_Review_Workflow',
            signatures=['~ProgramChair_EAUTH1'],
            note=openreview.api.Note(
                content={
                    'official_venue_name': { 'value': 'Email Authors Conference' },
                    'abbreviated_venue_name': { 'value': 'EAUTH 2026' },
                    'venue_website_url': { 'value': 'https://eauth.cc/Conferences/2026' },
                    'location': { 'value': 'Online' },
                    'venue_start_date': { 'value': openreview.tools.datetime_millis(now + datetime.timedelta(weeks=52)) },
                    'program_chair_emails': { 'value': ['programchair@eauth.cc'] },
                    'contact_email': { 'value': 'eauth2026.programchairs@gmail.com' },
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
                    'venue_id': { 'value': 'eauth.cc/2026/Conference' }
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])
        helpers.await_queue_edit(openreview_client, 'eauth.cc/2026/Conference/-/Full_Submission-0-1', count=1)

        submission_inv = openreview_client.get_invitation('eauth.cc/2026/Conference/-/Submission')
        assert submission_inv
        # the venue is deployed with the unified author object schema
        authors_field = submission_inv.edit['note']['content']['authors']
        assert authors_field['value']['param']['type'] == 'author{}'
        assert authors_field['value']['param']['properties']['username']['param']['regex'] == r'^~\S+$'

    def test_email_author_rejected_by_default(self, openreview_client, test_client, helpers):
        '''Out of the box the unified schema only accepts profile IDs, so entering an
        author by email should be rejected by the ``username`` regex.'''

        test_client = openreview.api.OpenReviewClient(token=test_client.token)

        with pytest.raises(openreview.OpenReviewException, match='must be a valid profile ID'):
            test_client.post_note_edit(
                invitation='eauth.cc/2026/Conference/-/Submission',
                signatures=['~SomeFirstName_User1'],
                note=openreview.api.Note(
                    license='CC BY 4.0',
                    content={
                        'title': { 'value': 'Rejected Email Author Submission' },
                        'abstract': { 'value': 'Author entered by email should be rejected.' },
                        'authors': {
                            'value': [
                                {
                                    'fullname': 'SomeFirstName User',
                                    'username': '~SomeFirstName_User1',
                                    'institutions': [{ 'domain': 'mail.com', 'country': 'US' }]
                                },
                                {
                                    'fullname': 'AuthorOne EAUTH',
                                    'username': 'author_one@eauth.cc',
                                    'institutions': [{ 'domain': 'eauth.cc', 'country': 'US' }]
                                }
                            ]
                        },
                        'keywords': { 'value': ['authors', 'email'] },
                        'email_sharing': { 'value': 'We authorize the sharing of all author emails with Program Chairs.' },
                        'data_release': { 'value': 'We authorize the release of our submission and author names to the public in the event of acceptance.' },
                    }
                )
            )

    def test_allow_email_in_authors(self, openreview_client, helpers):
        '''Relax the Submission invitation so the author ``username`` accepts either a
        profile ID or an email address.'''

        pc_client = openreview.api.OpenReviewClient(username='programchair@eauth.cc', password=helpers.strong_password)

        submission_inv = pc_client.get_invitation('eauth.cc/2026/Conference/-/Submission')
        content = submission_inv.edit['note']['content']

        # relax the username regex to allow a profile ID or an email address
        username_param = content['authors']['value']['param']['properties']['username']['param']
        username_param['regex'] = self.profile_or_email_regex
        username_param['mismatchError'] = 'must be a valid email or profile ID'

        edit = pc_client.post_invitation_edit(
            invitations='eauth.cc/2026/Conference/-/Submission/Form_Fields',
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

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        submission_inv = pc_client.get_invitation('eauth.cc/2026/Conference/-/Submission')
        updated_regex = submission_inv.edit['note']['content']['authors']['value']['param']['properties']['username']['param']['regex']
        assert updated_regex == self.profile_or_email_regex

    def test_post_submissions_with_email_authors(self, openreview_client, test_client, helpers):
        '''Post a few submissions whose authors are entered by email instead of a
        profile ID.'''

        test_client = openreview.api.OpenReviewClient(token=test_client.token)

        # Submission 1: a registered co-author entered by email
        edit = test_client.post_note_edit(
            invitation='eauth.cc/2026/Conference/-/Submission',
            signatures=['~SomeFirstName_User1'],
            note=openreview.api.Note(
                license='CC BY 4.0',
                content={
                    'title': { 'value': 'Email Authors Submission 1' },
                    'abstract': { 'value': 'A registered co-author entered by email.' },
                    'authors': {
                        'value': [
                            {
                                'fullname': 'SomeFirstName User',
                                'username': '~SomeFirstName_User1',
                                'institutions': [{ 'domain': 'mail.com', 'country': 'US' }]
                            },
                            {
                                'fullname': 'AuthorOne EAUTH',
                                'username': 'author_one@eauth.cc',
                                'institutions': [{ 'domain': 'eauth.cc', 'country': 'US' }]
                            }
                        ]
                    },
                    'keywords': { 'value': ['authors', 'email'] },
                    'email_sharing': { 'value': 'We authorize the sharing of all author emails with Program Chairs.' },
                    'data_release': { 'value': 'We authorize the release of our submission and author names to the public in the event of acceptance.' },
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        # Submission 2: a mix of profile IDs and emails, including an unregistered email
        edit = test_client.post_note_edit(
            invitation='eauth.cc/2026/Conference/-/Submission',
            signatures=['~SomeFirstName_User1'],
            note=openreview.api.Note(
                license='CC BY 4.0',
                content={
                    'title': { 'value': 'Email Authors Submission 2' },
                    'abstract': { 'value': 'A mix of profile IDs and email addresses.' },
                    'authors': {
                        'value': [
                            {
                                'fullname': 'SomeFirstName User',
                                'username': '~SomeFirstName_User1',
                                'institutions': [{ 'domain': 'mail.com', 'country': 'US' }]
                            },
                            {
                                'fullname': 'AuthorTwo EAUTH',
                                'username': '~AuthorTwo_EAUTH1',
                                'institutions': [{ 'domain': 'eauth.cc', 'country': 'US' }]
                            },
                            {
                                'fullname': 'Unregistered Author',
                                'username': 'unregistered_author@eauth.cc',
                                'institutions': [{ 'domain': 'eauth.cc', 'country': 'US' }]
                            }
                        ]
                    },
                    'keywords': { 'value': ['authors', 'email'] },
                    'email_sharing': { 'value': 'We authorize the sharing of all author emails with Program Chairs.' },
                    'data_release': { 'value': 'We authorize the release of our submission and author names to the public in the event of acceptance.' },
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        submissions = openreview_client.get_notes(invitation='eauth.cc/2026/Conference/-/Submission', sort='number:asc')
        assert len(submissions) == 2

        # authorids are derived from each author's username, so emails flow through verbatim
        assert submissions[0].authorids == ['~SomeFirstName_User1', 'author_one@eauth.cc']
        assert submissions[1].authorids == ['~SomeFirstName_User1', '~AuthorTwo_EAUTH1', 'unregistered_author@eauth.cc']

        # the authors group is populated with the email-based authorids as members
        authors_group = openreview_client.get_group(f'eauth.cc/2026/Conference/Submission{submissions[0].number}/Authors')
        assert 'author_one@eauth.cc' in authors_group.members
