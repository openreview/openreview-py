import datetime
import os
import pytest
from concurrent.futures import ThreadPoolExecutor
import openreview
from openreview.api import Note, OpenReviewClient


class TestSubmissionLimits():

    def test_setup_venue(self, openreview_client, helpers):
        support_group_id = 'openreview.net/Support'

        helpers.create_user('programchair@hvtest.cc', 'ProgramChair', 'HVTest')
        pc_client = OpenReviewClient(username='programchair@hvtest.cc', password=helpers.strong_password)

        now = datetime.datetime.now()
        due_date = now + datetime.timedelta(days=2)

        request = pc_client.post_note_edit(
            invitation='openreview.net/Support/Venue_Request/-/Conference_Review_Workflow',
            signatures=['~ProgramChair_HVTest1'],
            note=openreview.api.Note(
                content={
                    'official_venue_name': { 'value': 'The HVTest Conference' },
                    'abbreviated_venue_name': { 'value': 'HVTest 2025' },
                    'venue_website_url': { 'value': 'https://hvtest.cc/Conferences/2025' },
                    'location': { 'value': 'Amherst, Massachusetts' },
                    'venue_start_date': { 'value': openreview.tools.datetime_millis(now + datetime.timedelta(weeks=52)) },
                    'program_chair_emails': { 'value': ['programchair@hvtest.cc'] },
                    'contact_email': { 'value': 'hvtest2025.programchairs@gmail.com' },
                    'submission_start_date': { 'value': openreview.tools.datetime_millis(now) },
                    'submission_deadline': { 'value': openreview.tools.datetime_millis(due_date) },
                    'reviewers_name': { 'value': 'Reviewers' },
                    'area_chairs_name': { 'value': 'Area_Chairs' },
                    'senior_area_chair_groups_names': { 'value': 'Senior_Area_Chairs' },
                    'colocated': { 'value': 'Independent' },
                    'previous_venue': { 'value': 'HVTest.cc/2024/Conference' },
                    'expected_submissions': { 'value': 50 },
                    'how_did_you_hear_about_us': { 'value': 'We have used OpenReview for our previous conferences.' },
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
                    'venue_id': { 'value': 'HVTest.cc/2025/Conference' }
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        assert openreview_client.get_invitation('HVTest.cc/2025/Conference/-/Submission')
        assert openreview_client.get_invitation('HVTest.cc/2025/Conference/-/Edit')

    def test_human_verification_on_submission(self, openreview_client, helpers):
        # add humanVerificationRequired to the submission invitation via the meta invitation
        openreview_client.post_invitation_edit(
            invitations='HVTest.cc/2025/Conference/-/Edit',
            signatures=['HVTest.cc/2025/Conference'],
            invitation=openreview.api.Invitation(
                id='HVTest.cc/2025/Conference/-/Submission',
                humanVerificationRequired={ 'limit': 1, 'windowMs': 300000 }
            )
        )

        submission_inv = openreview_client.get_invitation('HVTest.cc/2025/Conference/-/Submission')
        assert submission_inv.humanVerificationRequired == { 'limit': 1, 'windowMs': 300000 }

        helpers.create_user('hvauthor@hvtest.cc', 'HVAuthor', 'One')
        author_client = OpenReviewClient(username='hvauthor@hvtest.cc', password=helpers.strong_password)

        # first submission succeeds (within the limit)
        first_edit = author_client.post_note_edit(
            invitation='HVTest.cc/2025/Conference/-/Submission',
            signatures=['~HVAuthor_One1'],
            note=Note(
                license='CC BY 4.0',
                content={
                    'title': { 'value': 'First HV Paper' },
                    'abstract': { 'value': 'First abstract' },
                    'authors': { 'value': ['HVAuthor One'] },
                    'authorids': { 'value': ['~HVAuthor_One1'] },
                    'pdf': { 'value': '/pdf/' + 'p' * 40 + '.pdf' },
                    'keywords': { 'value': ['kw'] },
                    'email_sharing': { 'value': 'We authorize the sharing of all author emails with Program Chairs.' },
                    'data_release': { 'value': 'We authorize the release of our submission and author names to the public in the event of acceptance.' },
                }
            )
        )
        assert first_edit['id']

        # second submission within the window must trigger human verification
        with pytest.raises(openreview.OpenReviewException, match=r'Human verification required'):
            author_client.post_note_edit(
                invitation='HVTest.cc/2025/Conference/-/Submission',
                signatures=['~HVAuthor_One1'],
                note=Note(
                    license='CC BY 4.0',
                    content={
                        'title': { 'value': 'Second HV Paper' },
                        'abstract': { 'value': 'Second abstract' },
                        'authors': { 'value': ['HVAuthor One'] },
                        'authorids': { 'value': ['~HVAuthor_One1'] },
                        'pdf': { 'value': '/pdf/' + 'p' * 40 + '.pdf' },
                        'keywords': { 'value': ['kw'] },
                        'email_sharing': { 'value': 'We authorize the sharing of all author emails with Program Chairs.' },
                        'data_release': { 'value': 'We authorize the release of our submission and author names to the public in the event of acceptance.' },
                    }
                )
            )

    def test_max_replies_on_submission(self, openreview_client, helpers):
        # remove humanVerificationRequired and set maxReplies to 1 on the submission invitation
        openreview_client.post_invitation_edit(
            invitations='HVTest.cc/2025/Conference/-/Edit',
            signatures=['HVTest.cc/2025/Conference'],
            invitation=openreview.api.Invitation(
                id='HVTest.cc/2025/Conference/-/Submission',
                maxReplies=1,
                humanVerificationRequired={ 'delete': True }
            )
        )

        submission_inv = openreview_client.get_invitation('HVTest.cc/2025/Conference/-/Submission')
        assert submission_inv.maxReplies == 1

        helpers.create_user('maxreplies@hvtest.cc', 'MaxReplies', 'One')
        author_client = OpenReviewClient(username='maxreplies@hvtest.cc', password=helpers.strong_password)

        # first submission succeeds
        first_edit = author_client.post_note_edit(
            invitation='HVTest.cc/2025/Conference/-/Submission',
            signatures=['~MaxReplies_One1'],
            note=Note(
                license='CC BY 4.0',
                content={
                    'title': { 'value': 'First MaxReplies Paper' },
                    'abstract': { 'value': 'First abstract' },
                    'authors': { 'value': ['MaxReplies One'] },
                    'authorids': { 'value': ['~MaxReplies_One1'] },
                    'pdf': { 'value': '/pdf/' + 'p' * 40 + '.pdf' },
                    'keywords': { 'value': ['kw'] },
                    'email_sharing': { 'value': 'We authorize the sharing of all author emails with Program Chairs.' },
                    'data_release': { 'value': 'We authorize the release of our submission and author names to the public in the event of acceptance.' },
                }
            )
        )
        assert first_edit['id']

        # second submission must fail due to maxReplies=1
        with pytest.raises(openreview.OpenReviewException, match=r'reached the maximum number \(1\) of replies'):
            author_client.post_note_edit(
                invitation='HVTest.cc/2025/Conference/-/Submission',
                signatures=['~MaxReplies_One1'],
                note=Note(
                    license='CC BY 4.0',
                    content={
                        'title': { 'value': 'Second MaxReplies Paper' },
                        'abstract': { 'value': 'Second abstract' },
                        'authors': { 'value': ['MaxReplies One'] },
                        'authorids': { 'value': ['~MaxReplies_One1'] },
                        'pdf': { 'value': '/pdf/' + 'p' * 40 + '.pdf' },
                        'keywords': { 'value': ['kw'] },
                        'email_sharing': { 'value': 'We authorize the sharing of all author emails with Program Chairs.' },
                        'data_release': { 'value': 'We authorize the release of our submission and author names to the public in the event of acceptance.' },
                    }
                )
            )

    def test_max_replies_limit_three(self, openreview_client, helpers):
        # update maxReplies to 3 on the submission invitation
        openreview_client.post_invitation_edit(
            invitations='HVTest.cc/2025/Conference/-/Edit',
            signatures=['HVTest.cc/2025/Conference'],
            invitation=openreview.api.Invitation(
                id='HVTest.cc/2025/Conference/-/Submission',
                maxReplies=3
            )
        )

        submission_inv = openreview_client.get_invitation('HVTest.cc/2025/Conference/-/Submission')
        assert submission_inv.maxReplies == 3

        helpers.create_user('maxreplies3@hvtest.cc', 'MaxReplies', 'Three')
        author_client = OpenReviewClient(username='maxreplies3@hvtest.cc', password=helpers.strong_password)

        # first three submissions succeed (within the limit)
        for i in range(3):
            edit = author_client.post_note_edit(
                invitation='HVTest.cc/2025/Conference/-/Submission',
                signatures=['~MaxReplies_Three1'],
                note=Note(
                    license='CC BY 4.0',
                    content={
                        'title': { 'value': f'MaxReplies Three Paper {i + 1}' },
                        'abstract': { 'value': f'Abstract {i + 1}' },
                        'authors': { 'value': ['MaxReplies Three'] },
                        'authorids': { 'value': ['~MaxReplies_Three1'] },
                        'pdf': { 'value': '/pdf/' + 'p' * 40 + '.pdf' },
                        'keywords': { 'value': ['kw'] },
                        'email_sharing': { 'value': 'We authorize the sharing of all author emails with Program Chairs.' },
                        'data_release': { 'value': 'We authorize the release of our submission and author names to the public in the event of acceptance.' },
                    }
                )
            )
            assert edit['id']

        # fourth submission must fail due to maxReplies=3
        with pytest.raises(openreview.OpenReviewException, match=r'reached the maximum number \(3\) of replies'):
            author_client.post_note_edit(
                invitation='HVTest.cc/2025/Conference/-/Submission',
                signatures=['~MaxReplies_Three1'],
                note=Note(
                    license='CC BY 4.0',
                    content={
                        'title': { 'value': 'MaxReplies Three Paper 4' },
                        'abstract': { 'value': 'Abstract 4' },
                        'authors': { 'value': ['MaxReplies Three'] },
                        'authorids': { 'value': ['~MaxReplies_Three1'] },
                        'pdf': { 'value': '/pdf/' + 'p' * 40 + '.pdf' },
                        'keywords': { 'value': ['kw'] },
                        'email_sharing': { 'value': 'We authorize the sharing of all author emails with Program Chairs.' },
                        'data_release': { 'value': 'We authorize the release of our submission and author names to the public in the event of acceptance.' },
                    }
                )
            )

    def test_max_replies_race_condition(self, openreview_client, helpers):
        # set maxReplies back to 1 on the submission invitation
        openreview_client.post_invitation_edit(
            invitations='HVTest.cc/2025/Conference/-/Edit',
            signatures=['HVTest.cc/2025/Conference'],
            invitation=openreview.api.Invitation(
                id='HVTest.cc/2025/Conference/-/Submission',
                maxReplies=1
            )
        )

        helpers.create_user('racecondition@hvtest.cc', 'RaceCondition', 'One')
        author_client = OpenReviewClient(username='racecondition@hvtest.cc', password=helpers.strong_password)

        def submit(title):
            return author_client.post_note_edit(
                invitation='HVTest.cc/2025/Conference/-/Submission',
                signatures=['~RaceCondition_One1'],
                note=Note(
                    license='CC BY 4.0',
                    content={
                        'title': { 'value': title },
                        'abstract': { 'value': 'Concurrent abstract' },
                        'authors': { 'value': ['RaceCondition One'] },
                        'authorids': { 'value': ['~RaceCondition_One1'] },
                        'pdf': { 'value': '/pdf/' + 'p' * 40 + '.pdf' },
                        'keywords': { 'value': ['kw'] },
                        'email_sharing': { 'value': 'We authorize the sharing of all author emails with Program Chairs.' },
                        'data_release': { 'value': 'We authorize the release of our submission and author names to the public in the event of acceptance.' },
                    }
                )
            )

        # fire two submissions concurrently; the atomic counter must let exactly one through
        successes = []
        errors = []
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(submit, f'Race Paper {i + 1}') for i in range(2)]
            for f in futures:
                try:
                    successes.append(f.result())
                except openreview.OpenReviewException as e:
                    errors.append(str(e))

        assert len(successes) == 1, f'expected exactly one success, got {len(successes)}'
        assert len(errors) == 1, f'expected exactly one failure, got {len(errors)}'
        assert 'reached the maximum number (1) of replies' in errors[0]

    def test_human_verification_on_attachment(self, helpers):
        # API is configured to allow 10 attachment uploads per hour per user
        helpers.create_user('hvattachment@hvtest.cc', 'HVAttachment', 'One')
        author_client = OpenReviewClient(username='hvattachment@hvtest.cc', password=helpers.strong_password)

        pdf_path = os.path.join(os.path.dirname(__file__), 'data/paper.pdf')

        # first 10 attachment uploads succeed (within the limit)
        for _ in range(10):
            url = author_client.put_attachment(pdf_path, 'HVTest.cc/2025/Conference/-/Submission', 'pdf')
            assert url

        # 11th upload within the window must trigger human verification
        with pytest.raises(openreview.OpenReviewException, match=r'Human verification required'):
            author_client.put_attachment(pdf_path, 'HVTest.cc/2025/Conference/-/Submission', 'pdf')
