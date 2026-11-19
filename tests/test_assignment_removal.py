import datetime
import openreview
import pytest


class TestAssignmentRemoval():

    def test_setup_venue(self, openreview_client, helpers):

        helpers.create_user('programchair@arv.cc', 'ProgramChair', 'ARV')
        helpers.create_user('reviewer@arv.cc', 'Reviewer', 'ARV')

        pc_client = openreview.api.OpenReviewClient(username='programchair@arv.cc', password=helpers.strong_password)

        now = datetime.datetime.now()

        request = pc_client.post_note_edit(
            invitation='openreview.net/Support/Venue_Request/-/Conference_Review_Workflow',
            signatures=['~ProgramChair_ARV1'],
            note=openreview.api.Note(
                content={
                    'official_venue_name': { 'value': 'The ARV Conference' },
                    'abbreviated_venue_name': { 'value': 'ARV 2026' },
                    'venue_website_url': { 'value': 'https://arv.cc/Conferences/2026' },
                    'location': { 'value': 'Amherst, Massachusetts' },
                    'venue_start_date': { 'value': openreview.tools.datetime_millis(now + datetime.timedelta(weeks=52)) },
                    'program_chair_emails': { 'value': ['programchair@arv.cc'] },
                    'contact_email': { 'value': 'arv2026.programchairs@gmail.com' },
                    'submission_start_date': { 'value': openreview.tools.datetime_millis(now) },
                    'submission_deadline': { 'value': openreview.tools.datetime_millis(now + datetime.timedelta(days=2)) },
                    'expected_submissions': { 'value': 100 },
                    'venue_organizer_agreement': {
                        'value': [
                            'OpenReview natively supports a wide variety of reviewing workflow configurations. However, if we want significant reviewing process customizations or experiments, we will detail these requests to the OpenReview staff at least three months in advance.',
                            'We will ask authors and reviewers to create an OpenReview Profile well in advance of the paper submission deadlines.',
                            'When assembling our group of reviewers, we will only include email addresses or OpenReview Profile IDs of people we know to have authored publications relevant to our venue.  (We will not solicit new reviewers using an open web form, because unfortunately some malicious actors sometimes try to create "fake ids" aiming to be assigned to review their own paper submissions.)',
                            'We acknowledge that, if our venue\'s reviewing workflow is non-standard, or if our venue is expecting more than a few hundred submissions for any one deadline, we should designate our own Workflow Chair, who will read the OpenReview documentation and manage our workflow configurations throughout the reviewing process.',
                            'We acknowledge that OpenReview staff work Monday-Friday during standard business hours US Eastern time, and we cannot expect support responses outside those times.  For this reason, we recommend setting submission and reviewing deadlines Monday through Thursday.',
                            'We will treat the OpenReview staff with kindness and consideration.',
                            'We acknowledge that authors and reviewers will be required to share their preferred email.',
                            'We acknowledge that certain metadata for accepted papers, specifically the paper title, abstract and author list, will be publicly released on OpenReview.',
                        ]
                    }
                }
            )
        )
        helpers.await_queue_edit(openreview_client, edit_id=request['id'])

        edit = openreview_client.post_note_edit(
            invitation='openreview.net/Support/Venue_Request/Conference_Review_Workflow/-/Deployment',
            signatures=['openreview.net/Support'],
            note=openreview.api.Note(
                id=request['note']['id'],
                content={ 'venue_id': { 'value': 'ARV.cc/2026/Conference' } }
            )
        )
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        assert openreview.tools.get_group(openreview_client, 'ARV.cc/2026/Conference')

        openreview_client.post_group_edit(
            invitation='ARV.cc/2026/Conference/Reviewers/-/Members',
            signatures=['ARV.cc/2026/Conference'],
            group=openreview.api.Group(
                members={ 'append': ['~Reviewer_ARV1', '~ProgramChair_ARV1'] }
            )
        )

        assert set(openreview_client.get_group('ARV.cc/2026/Conference/Reviewers').members) == { '~Reviewer_ARV1', '~ProgramChair_ARV1' }

    def test_post_submission(self, openreview_client, test_client, helpers):

        test_client = openreview.api.OpenReviewClient(token=test_client.token)

        submission_edit = test_client.post_note_edit(
            invitation='ARV.cc/2026/Conference/-/Submission',
            signatures=['~SomeFirstName_User1'],
            note=openreview.api.Note(
                license='CC BY 4.0',
                content={
                    'title': { 'value': 'ARV Paper title 1' },
                    'abstract': { 'value': 'ARV abstract 1' },
                    'authors': {
                        'value': [
                            {
                                'fullname': 'SomeFirstName User',
                                'username': '~SomeFirstName_User1'
                            }
                        ]
                    },
                    'keywords': { 'value': ['key'] },
                    'pdf': { 'value': '/pdf/' + 'p' * 40 + '.pdf' },
                    'email_sharing': { 'value': 'We authorize the sharing of all author emails with Program Chairs.' },
                    'data_release': { 'value': 'We authorize the release of our submission and author names to the public in the event of acceptance.' },
                }
            )
        )
        helpers.await_queue_edit(openreview_client, edit_id=submission_edit['id'])

        assert len(openreview_client.get_notes(invitation='ARV.cc/2026/Conference/-/Submission')) == 1

    def test_assign_reviewers(self, openreview_client, helpers):

        pc_client = openreview.api.OpenReviewClient(username='programchair@arv.cc', password=helpers.strong_password)
        now = datetime.datetime.now()

        pc_client.post_invitation_edit(
            invitations='ARV.cc/2026/Conference/Reviewers/-/Submission_Group/Dates',
            content={
                'activation_date': { 'value': openreview.tools.datetime_millis(now - datetime.timedelta(minutes=30)) }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id='ARV.cc/2026/Conference/Reviewers/-/Submission_Group-0-1', count=2)

        assert openreview_client.get_group('ARV.cc/2026/Conference/Submission1/Reviewers')

        openreview_client.post_group_edit(
            invitation='ARV.cc/2026/Conference/-/Edit',
            signatures=['ARV.cc/2026/Conference'],
            group=openreview.api.Group(
                id='ARV.cc/2026/Conference/Submission1/Reviewer_1111',
                readers=['ARV.cc/2026/Conference'],
                writers=['ARV.cc/2026/Conference'],
                signatures=['ARV.cc/2026/Conference'],
                signatories=['ARV.cc/2026/Conference'],
                members=['~Reviewer_ARV1']
            )
        )

        submission = openreview_client.get_notes(invitation='ARV.cc/2026/Conference/-/Submission')[0]

        for reviewer_id in ['~Reviewer_ARV1', '~ProgramChair_ARV1']:
            edge = pc_client.post_edge(openreview.api.Edge(
                invitation='ARV.cc/2026/Conference/Reviewers/-/Assignment',
                head=submission.id,
                tail=reviewer_id,
                signatures=['ARV.cc/2026/Conference/Program_Chairs'],
                weight=1
            ))
            helpers.await_queue_edit(openreview_client, edit_id=edge.id)

        assert openreview_client.get_group('ARV.cc/2026/Conference/Submission1/Reviewers').members == ['~Reviewer_ARV1', '~ProgramChair_ARV1']

        anon_groups = { g.members[0]: g.id for g in openreview_client.get_groups(prefix='ARV.cc/2026/Conference/Submission1/Reviewer_') }
        assert len(anon_groups) == 2
        assert anon_groups['~Reviewer_ARV1'] == 'ARV.cc/2026/Conference/Submission1/Reviewer_1111'
        assert anon_groups['~ProgramChair_ARV1'] > anon_groups['~Reviewer_ARV1']

        pc_signatory_groups = openreview_client.get_groups(prefix='ARV.cc/2026/Conference/Submission1/Reviewer_', signatory='~ProgramChair_ARV1')
        assert set(g.id for g in pc_signatory_groups) == set(anon_groups.values())

        pc_member_groups = openreview_client.get_groups(prefix='ARV.cc/2026/Conference/Submission1/Reviewer_', member='~ProgramChair_ARV1')
        assert [g.id for g in pc_member_groups] == [anon_groups['~ProgramChair_ARV1']]

    def test_post_review(self, openreview_client, helpers):

        pc_client = openreview.api.OpenReviewClient(username='programchair@arv.cc', password=helpers.strong_password)
        now = datetime.datetime.now()

        pc_client.post_invitation_edit(
            invitations='ARV.cc/2026/Conference/-/Submission_Change_Before_Reviewing/Dates',
            content={
                'activation_date': { 'value': openreview.tools.datetime_millis(now - datetime.timedelta(minutes=30)) }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id='ARV.cc/2026/Conference/-/Submission_Change_Before_Reviewing-0-1', count=2)

        due_date = openreview.tools.datetime_millis(now + datetime.timedelta(days=3))
        pc_client.post_invitation_edit(
            invitations='ARV.cc/2026/Conference/-/Official_Review/Dates',
            content={
                'activation_date': { 'value': openreview.tools.datetime_millis(now) },
                'due_date': { 'value': due_date },
                'expiration_date': { 'value': due_date }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id='ARV.cc/2026/Conference/-/Official_Review-0-1', count=2)

        assert openreview_client.get_invitation('ARV.cc/2026/Conference/Submission1/-/Official_Review')

        reviewer_client = openreview.api.OpenReviewClient(username='reviewer@arv.cc', password=helpers.strong_password)
        anon_groups = reviewer_client.get_groups(prefix='ARV.cc/2026/Conference/Submission1/Reviewer_', member='~Reviewer_ARV1')
        assert [g.id for g in anon_groups] == ['ARV.cc/2026/Conference/Submission1/Reviewer_1111']

        review_edit = reviewer_client.post_note_edit(
            invitation='ARV.cc/2026/Conference/Submission1/-/Official_Review',
            signatures=[anon_groups[0].id],
            note=openreview.api.Note(
                content={
                    'title': { 'value': 'Review for Paper 1' },
                    'review': { 'value': 'good paper' },
                    'rating': { 'value': 8 },
                    'confidence': { 'value': 4 }
                }
            )
        )
        helpers.await_queue_edit(openreview_client, edit_id=review_edit['id'])

        assert len(openreview_client.get_notes(invitation='ARV.cc/2026/Conference/Submission1/-/Official_Review')) == 1

    def test_remove_assignments(self, openreview_client, helpers):

        pc_client = openreview.api.OpenReviewClient(username='programchair@arv.cc', password=helpers.strong_password)
        submission = openreview_client.get_notes(invitation='ARV.cc/2026/Conference/-/Submission')[0]

        assignment = pc_client.get_edges(invitation='ARV.cc/2026/Conference/Reviewers/-/Assignment', head=submission.id, tail='~Reviewer_ARV1')[0]
        assignment.ddate = openreview.tools.datetime_millis(datetime.datetime.now())
        assignment.cdate = None

        with pytest.raises(openreview.OpenReviewException, match=r'Can not remove assignment, the user ~Reviewer_ARV1 already posted a Official Review'):
            pc_client.post_edge(assignment)

        assignment = pc_client.get_edges(invitation='ARV.cc/2026/Conference/Reviewers/-/Assignment', head=submission.id, tail='~ProgramChair_ARV1')[0]
        assignment.ddate = openreview.tools.datetime_millis(datetime.datetime.now())
        assignment.cdate = None
        pc_client.post_edge(assignment)

        helpers.await_queue_edit(openreview_client, edit_id=assignment.id, count=2)

        assert openreview_client.get_group('ARV.cc/2026/Conference/Submission1/Reviewers').members == ['~Reviewer_ARV1']
