import datetime
import pytest
import openreview
from openreview.api import Note, OpenReviewClient


class TestServeAsReviewerValidation():
    '''
    Conditional, same-edit validation for note edits.

    A venue wants a new submission field `serve_as_reviewer` where the author enters
    the profile ids of the submission's authors who will serve as reviewers. The API
    should validate that the value of `serve_as_reviewer` (a list) is a subset of the
    `authors` field's usernames *of the same edit*.

    This is expressed with a `$` reference in the field's enum that points at the
    sibling `authors` field of the same edit:

        "${...3/authors/value/*/username}"

    which resolves, per edit, to the list of author usernames. The existing API
    interpreter already supports this (no server-side change needed):
      - `...`      spreads the resolved array into the enum (so enum becomes the
                   flat list of usernames, not a single nested array);
      - `3/`       pops enum-index, `value`, `serve_as_reviewer` off the field's path
                   to land at `note/content`;
      - `authors/value/*/username` reads each author-object's username.

    Because `serve_as_reviewer` is a `string[]` whose allowed values are exactly the
    author usernames, AJV validates it as a subset of the authors: posting a value
    that is NOT one of the authors is rejected, one that IS an author is accepted.
    '''

    def test_setup(self, openreview_client, helpers):

        super_id = 'openreview.net'
        support_group_id = super_id + '/Support'

        helpers.create_user('programchair@sarc.cc', 'ProgramChair', 'SARC')
        helpers.create_user('author_one@sarc.cc', 'AuthorOne', 'SARC')
        helpers.create_user('author_two@sarc.cc', 'AuthorTwo', 'SARC')
        helpers.create_user('author_three@sarc.cc', 'AuthorThree', 'SARC')
        pc_client = openreview.api.OpenReviewClient(username='programchair@sarc.cc', password=helpers.strong_password)

        now = datetime.datetime.now()
        due_date = now + datetime.timedelta(days=2)

        request = pc_client.post_note_edit(invitation='openreview.net/Support/Venue_Request/-/Conference_Review_Workflow',
            signatures=['~ProgramChair_SARC1'],
            note=openreview.api.Note(
                content={
                    'official_venue_name': { 'value': 'Serve As Reviewer Conference' },
                    'abbreviated_venue_name': { 'value': 'SARC 2026' },
                    'venue_website_url': { 'value': 'https://sarc.cc/Conferences/2026' },
                    'location': { 'value': 'Online' },
                    'venue_start_date': { 'value': openreview.tools.datetime_millis(now + datetime.timedelta(weeks=52)) },
                    'program_chair_emails': { 'value': ['programchair@sarc.cc'] },
                    'contact_email': { 'value': 'sarc2026.programchairs@gmail.com' },
                    'submission_start_date': { 'value': openreview.tools.datetime_millis(now - datetime.timedelta(days=1)) },
                    'submission_deadline': { 'value': openreview.tools.datetime_millis(due_date) },
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
                            'We acknowledge that role participation will be collected for all participants—reviewers, area chairs, and senior area chairs—and made publicly available in the OpenReview profile of each participant.',
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
                    'venue_id': { 'value': 'sarc.cc/2026/Conference' }
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        assert openreview_client.get_invitation('sarc.cc/2026/Conference/-/Submission')
        assert openreview_client.get_invitation('sarc.cc/2026/Conference/-/Submission/Form_Fields')

    def test_add_serve_as_reviewer_field(self, openreview_client, helpers):
        '''
        Add the `serve_as_reviewer` field to the submission form. It is a list whose
        allowed values are a `$` reference to the usernames of the authors of the same
        submission edit, so the API can validate that the entered list is a subset of
        the authors.
        '''

        pc_client = openreview.api.OpenReviewClient(username='programchair@sarc.cc', password=helpers.strong_password)

        content_inv = openreview.tools.get_invitation(openreview_client, 'sarc.cc/2026/Conference/-/Submission/Form_Fields')
        assert content_inv

        pc_client.post_invitation_edit(
            invitations=content_inv.id,
            content={
                'content': {
                    'value': {
                        'serve_as_reviewer': {
                            'order': 11,
                            'description': 'Enter the profile ids of the authors of this submission who will serve as reviewers.',
                            'value': {
                                'param': {
                                    'type': 'string[]',
                                    'enum': ['${3/authors/value/*/username}'],
                                    'input': 'select'
                                }
                            }
                        }
                    }
                },
                'license': {
                    'value': [
                        {'value': 'CC BY 4.0', 'description': 'CC BY 4.0'}
                    ]
                }
            }
        )

        helpers.await_queue_edit(openreview_client, invitation='sarc.cc/2026/Conference/-/Submission/Form_Fields')

        submission_inv = openreview.tools.get_invitation(openreview_client, 'sarc.cc/2026/Conference/-/Submission')
        assert submission_inv
        assert 'serve_as_reviewer' in submission_inv.edit['note']['content']
        assert submission_inv.edit['note']['content']['serve_as_reviewer']['value']['param']['enum'] == ['${3/authors/value/*/username}']

    def _submission_content(self, serve_as_reviewer):
        '''Full submission content with a given serve_as_reviewer value. The authors
        are always included because the enum reference resolves against the posted
        edit, not the merged note -- omitting authors would leave the reference
        unresolved and reject even valid values.'''
        return {
            'title': { 'value': 'Serve As Reviewer Submission' },
            'abstract': { 'value': 'Abstract for the serve-as-reviewer test.' },
            'authors': {
                'value': [
                    {
                        'fullname': 'SomeFirstName User',
                        'username': '~SomeFirstName_User1',
                        'institutions': [{ 'domain': 'mail.com', 'country': 'US' }]
                    },
                    {
                        'fullname': 'AuthorOne SARC',
                        'username': '~AuthorOne_SARC1',
                        'institutions': [{ 'domain': 'sarc.cc', 'country': 'US' }]
                    }
                ]
            },
            'keywords': { 'value': ['serve', 'as', 'reviewer'] },
            'pdf': { 'value': '/pdf/' + 'p' * 40 + '.pdf' },
            'serve_as_reviewer': { 'value': serve_as_reviewer },
            'email_sharing': { 'value': 'We authorize the sharing of all author emails with Program Chairs.' },
            'data_release': { 'value': 'We authorize the release of our submission and author names to the public in the event of acceptance.' },
        }

    def test_submission_with_valid_serve_as_reviewer_succeeds(self, openreview_client, test_client, helpers):
        '''
        `serve_as_reviewer` is a list whose every element is one of the authors
        (a valid subset of authors/username). This must be accepted, regardless of
        order and for any subset size.
        '''

        test_client = openreview.api.OpenReviewClient(token=test_client.token)

        # both authors -> valid subset
        edit = test_client.post_note_edit(
            invitation='sarc.cc/2026/Conference/-/Submission',
            signatures=['~SomeFirstName_User1'],
            note=openreview.api.Note(
                license='CC BY 4.0',
                content=self._submission_content(['~SomeFirstName_User1', '~AuthorOne_SARC1'])
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        submissions = openreview_client.get_notes(invitation='sarc.cc/2026/Conference/-/Submission', sort='number:asc')
        assert len(submissions) == 1
        submission = submissions[0]
        assert submission.content['serve_as_reviewer']['value'] == ['~SomeFirstName_User1', '~AuthorOne_SARC1']

        # 1. both authors in reverse order -> still a valid subset (order-independent)
        edit = test_client.post_note_edit(
            invitation='sarc.cc/2026/Conference/-/Submission',
            signatures=['~SomeFirstName_User1'],
            note=openreview.api.Note(
                id=submission.id,
                license='CC BY 4.0',
                content=self._submission_content(['~AuthorOne_SARC1', '~SomeFirstName_User1'])
            )
        )
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])
        submission = openreview_client.get_note(submission.id)
        assert submission.content['serve_as_reviewer']['value'] == ['~AuthorOne_SARC1', '~SomeFirstName_User1']

        # 2. a single author -> still a valid subset
        edit = test_client.post_note_edit(
            invitation='sarc.cc/2026/Conference/-/Submission',
            signatures=['~SomeFirstName_User1'],
            note=openreview.api.Note(
                id=submission.id,
                license='CC BY 4.0',
                content=self._submission_content(['~AuthorOne_SARC1'])
            )
        )
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])
        submission = openreview_client.get_note(submission.id)
        assert submission.content['serve_as_reviewer']['value'] == ['~AuthorOne_SARC1']

        # still just the one submission
        submissions = openreview_client.get_notes(invitation='sarc.cc/2026/Conference/-/Submission', sort='number:asc')
        assert len(submissions) == 1

    def test_submission_with_invalid_serve_as_reviewer_fails(self, openreview_client, test_client, helpers):
        '''
        `serve_as_reviewer` is a list that is NOT a subset of the authors: it contains
        ~ProgramChair_SARC1 (the PC, not an author). This must be rejected.
        '''

        test_client = openreview.api.OpenReviewClient(token=test_client.token)

        with pytest.raises(openreview.OpenReviewException) as openReviewError:
            test_client.post_note_edit(
                invitation='sarc.cc/2026/Conference/-/Submission',
                signatures=['~SomeFirstName_User1'],
                note=openreview.api.Note(
                    license='CC BY 4.0',
                    content={
                        'title': { 'value': 'Serve As Reviewer Invalid Submission' },
                        'abstract': { 'value': 'Abstract for the serve-as-reviewer invalid test.' },
                        'authors': {
                            'value': [
                                {
                                    'fullname': 'SomeFirstName User',
                                    'username': '~SomeFirstName_User1',
                                    'institutions': [{ 'domain': 'mail.com', 'country': 'US' }]
                                },
                                {
                                    'fullname': 'AuthorOne SARC',
                                    'username': '~AuthorOne_SARC1',
                                    'institutions': [{ 'domain': 'sarc.cc', 'country': 'US' }]
                                }
                            ]
                        },
                        'keywords': { 'value': ['serve', 'as', 'reviewer'] },
                        'pdf': { 'value': '/pdf/' + 'p' * 40 + '.pdf' },
                        # ~ProgramChair_SARC1 is NOT one of the authors above, so this
                        # list is not a subset of authors/username
                        'serve_as_reviewer': { 'value': ['~AuthorOne_SARC1', '~ProgramChair_SARC1'] },
                        'email_sharing': { 'value': 'We authorize the sharing of all author emails with Program Chairs.' },
                        'data_release': { 'value': 'We authorize the release of our submission and author names to the public in the event of acceptance.' },
                    }
                )
            )

        # The non-author value is rejected against the resolved enum of author usernames.
        error = str(openReviewError.value)
        assert 'serve_as_reviewer' in error
        assert '~ProgramChair_SARC1' in error
