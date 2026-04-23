import datetime
import openreview


class TestAssignCommitteeOpenDeadline():

    def test_setup_venue(self, openreview_client, helpers):
        """Setup a new venue with the submission deadline kept open (30 days out)
        so that the Submission_Group invitation has not been activated yet and
        the per-submission Reviewers groups have not been created."""

        support_group_id = 'openreview.net/Support'

        helpers.create_user('programchair@xyz.cc', 'ProgramChair', 'XYZ')
        helpers.create_user('reviewer_one@xyz.cc', 'ReviewerOne', 'XYZ')
        helpers.create_user('reviewer_two@xyz.cc', 'ReviewerTwo', 'XYZ')
        helpers.create_user('reviewer_three@xyz.cc', 'ReviewerThree', 'XYZ')
        helpers.create_user('ac_one@xyz.cc', 'AreaChairOne', 'XYZ')
        helpers.create_user('ac_two@xyz.cc', 'AreaChairTwo', 'XYZ')

        pc_client = openreview.api.OpenReviewClient(username='programchair@xyz.cc', password=helpers.strong_password)

        now = datetime.datetime.now()
        # keep the submission deadline far in the future so the deadline is still open
        due_date = now + datetime.timedelta(days=30)

        request = pc_client.post_note_edit(
            invitation='openreview.net/Support/Venue_Request/-/Conference_Review_Workflow',
            signatures=['~ProgramChair_XYZ1'],
            note=openreview.api.Note(
                content={
                    'official_venue_name': { 'value': 'The XYZ Conference' },
                    'abbreviated_venue_name': { 'value': 'XYZ 2025' },
                    'venue_website_url': { 'value': 'https://xyz.cc/Conferences/2025' },
                    'location': { 'value': 'Amherst, Massachusetts' },
                    'venue_start_date': { 'value': openreview.tools.datetime_millis(now + datetime.timedelta(weeks=52)) },
                    'program_chair_emails': { 'value': ['programchair@xyz.cc'] },
                    'contact_email': { 'value': 'xyz2025.programchairs@gmail.com' },
                    'submission_start_date': { 'value': openreview.tools.datetime_millis(now) },
                    'submission_deadline': { 'value': openreview.tools.datetime_millis(due_date) },
                    'reviewer_role_name': { 'value': ['Reviewers'] },
                    'area_chairs_support': { 'value': True },
                    'area_chair_role_name': { 'value': ['Area_Chairs'] },
                    'colocated': { 'value': 'Independent' },
                    'previous_venue': { 'value': 'XYZ.cc/2024/Conference' },
                    'expected_submissions': { 'value': 100 },
                    'how_did_you_hear_about_us': { 'value': 'We have used OpenReview before.' },
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

        request = openreview_client.get_note(request['note']['id'])

        # deploy the venue
        edit = openreview_client.post_note_edit(
            invitation='openreview.net/Support/Venue_Request/Conference_Review_Workflow/-/Deployment',
            signatures=[support_group_id],
            note=openreview.api.Note(
                id=request.id,
                content={ 'venue_id': { 'value': 'XYZ.cc/2025/Conference' } }
            )
        )
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        venue_group = openreview.tools.get_group(openreview_client, 'XYZ.cc/2025/Conference')
        assert venue_group

        # the Submission_Group invitation should be scheduled in the future, after the submission deadline
        submission_inv = openreview_client.get_invitation('XYZ.cc/2025/Conference/-/Submission')
        submission_group_inv = openreview_client.get_invitation('XYZ.cc/2025/Conference/Reviewers/-/Submission_Group')
        assert submission_group_inv.cdate == submission_inv.expdate
        assert submission_group_inv.cdate > openreview.tools.datetime_millis(datetime.datetime.now())

        # add reviewers directly to the Reviewers group (skip the recruitment flow)
        openreview_client.post_group_edit(
            invitation='XYZ.cc/2025/Conference/Reviewers/-/Members',
            signatures=['XYZ.cc/2025/Conference'],
            group=openreview.api.Group(
                members={ 'append': ['~ReviewerOne_XYZ1', '~ReviewerTwo_XYZ1', '~ReviewerThree_XYZ1'] }
            )
        )

        reviewers_group = openreview_client.get_group('XYZ.cc/2025/Conference/Reviewers')
        assert '~ReviewerOne_XYZ1' in reviewers_group.members
        assert '~ReviewerTwo_XYZ1' in reviewers_group.members
        assert '~ReviewerThree_XYZ1' in reviewers_group.members

        # Area Chairs group should exist and Submission_Group invitation should be scheduled in the future
        ac_submission_group_inv = openreview_client.get_invitation('XYZ.cc/2025/Conference/Area_Chairs/-/Submission_Group')
        assert ac_submission_group_inv.cdate == submission_inv.expdate
        assert ac_submission_group_inv.cdate > openreview.tools.datetime_millis(datetime.datetime.now())

        # add area chairs directly to the Area_Chairs group
        openreview_client.post_group_edit(
            invitation='XYZ.cc/2025/Conference/Area_Chairs/-/Members',
            signatures=['XYZ.cc/2025/Conference'],
            group=openreview.api.Group(
                members={ 'append': ['~AreaChairOne_XYZ1', '~AreaChairTwo_XYZ1'] }
            )
        )

        ac_group = openreview_client.get_group('XYZ.cc/2025/Conference/Area_Chairs')
        assert '~AreaChairOne_XYZ1' in ac_group.members
        assert '~AreaChairTwo_XYZ1' in ac_group.members

    def test_post_submissions(self, openreview_client, test_client, helpers):
        """Post a few submissions while the deadline is still open."""

        test_client = openreview.api.OpenReviewClient(token=test_client.token)

        for i in range(1, 6):
            note = openreview.api.Note(
                license='CC BY 4.0',
                content={
                    'title': { 'value': f'XYZ Paper title {i}' },
                    'abstract': { 'value': f'XYZ abstract {i}' },
                    'authorids': { 'value': ['~SomeFirstName_User1'] },
                    'authors': { 'value': ['SomeFirstName User'] },
                    'keywords': { 'value': ['key'] },
                    'pdf': { 'value': '/pdf/' + 'p' * 40 + '.pdf' },
                    'email_sharing': { 'value': 'We authorize the sharing of all author emails with Program Chairs.' },
                    'data_release': { 'value': 'We authorize the release of our submission and author names to the public in the event of acceptance.' },
                }
            )
            test_client.post_note_edit(
                invitation='XYZ.cc/2025/Conference/-/Submission',
                signatures=['~SomeFirstName_User1'],
                note=note
            )

        helpers.await_queue_edit(openreview_client, invitation='XYZ.cc/2025/Conference/-/Submission', count=5)

        submissions = openreview_client.get_notes(invitation='XYZ.cc/2025/Conference/-/Submission', sort='number:asc')
        assert len(submissions) == 5

        # since the submission deadline is still open, the per-submission Reviewers
        # and Area_Chairs groups should NOT exist yet
        for submission in submissions:
            assert openreview.tools.get_group(openreview_client, f'XYZ.cc/2025/Conference/Submission{submission.number}/Reviewers') is None
            assert openreview.tools.get_group(openreview_client, f'XYZ.cc/2025/Conference/Submission{submission.number}/Area_Chairs') is None

    def test_assign_reviewers_individually(self, openreview_client, helpers):
        """Posting individual Assignment edges while the deadline is still open should
        cause the assignment_post_process to create the per-submission Reviewers group
        on the fly via the Submission_Group invitation."""

        submissions = openreview_client.get_notes(invitation='XYZ.cc/2025/Conference/-/Submission', sort='number:asc')
        assert len(submissions) == 5

        # confirm the group does not exist yet
        assert openreview.tools.get_group(openreview_client, 'XYZ.cc/2025/Conference/Submission1/Reviewers') is None

        # post an assignment edge for paper 1, ReviewerOne
        edge = openreview_client.post_edge(openreview.api.Edge(
            invitation='XYZ.cc/2025/Conference/Reviewers/-/Assignment',
            head=submissions[0].id,
            tail='~ReviewerOne_XYZ1',
            signatures=['XYZ.cc/2025/Conference/Program_Chairs'],
            weight=1
        ))
        helpers.await_queue_edit(openreview_client, edit_id=edge.id)

        # the group should have been created with ReviewerOne as a member
        reviewers_group = openreview_client.get_group('XYZ.cc/2025/Conference/Submission1/Reviewers')
        assert reviewers_group is not None
        assert '~ReviewerOne_XYZ1' in reviewers_group.members

        # post a second assignment edge for paper 1, ReviewerTwo - the existing group should be updated
        edge = openreview_client.post_edge(openreview.api.Edge(
            invitation='XYZ.cc/2025/Conference/Reviewers/-/Assignment',
            head=submissions[0].id,
            tail='~ReviewerTwo_XYZ1',
            signatures=['XYZ.cc/2025/Conference/Program_Chairs'],
            weight=1
        ))
        helpers.await_queue_edit(openreview_client, edit_id=edge.id)

        reviewers_group = openreview_client.get_group('XYZ.cc/2025/Conference/Submission1/Reviewers')
        assert '~ReviewerOne_XYZ1' in reviewers_group.members
        assert '~ReviewerTwo_XYZ1' in reviewers_group.members

        # post an assignment edge for paper 2 - again the group should be created on the fly
        assert openreview.tools.get_group(openreview_client, 'XYZ.cc/2025/Conference/Submission2/Reviewers') is None

        edge = openreview_client.post_edge(openreview.api.Edge(
            invitation='XYZ.cc/2025/Conference/Reviewers/-/Assignment',
            head=submissions[1].id,
            tail='~ReviewerThree_XYZ1',
            signatures=['XYZ.cc/2025/Conference/Program_Chairs'],
            weight=1
        ))
        helpers.await_queue_edit(openreview_client, edit_id=edge.id)

        reviewers_group = openreview_client.get_group('XYZ.cc/2025/Conference/Submission2/Reviewers')
        assert reviewers_group is not None
        assert '~ReviewerThree_XYZ1' in reviewers_group.members

        # Case: group already exists - manually create the group for paper 3 via the
        # Submission_Group invitation, then post an assignment edge and verify the
        # existing group is updated (member added) instead of being recreated.
        assert openreview.tools.get_group(openreview_client, 'XYZ.cc/2025/Conference/Submission3/Reviewers') is None

        openreview_client.post_group_edit(
            invitation='XYZ.cc/2025/Conference/Reviewers/-/Submission_Group',
            content={
                'noteId': { 'value': submissions[2].id },
                'noteNumber': { 'value': submissions[2].number }
            },
            group=openreview.api.Group()
        )
        openreview_client.add_members_to_group('XYZ.cc/2025/Conference/Submission3/Reviewers', ['~ReviewerOne_XYZ1'])

        reviewers_group = openreview_client.get_group('XYZ.cc/2025/Conference/Submission3/Reviewers')
        assert reviewers_group is not None
        assert reviewers_group.members == ['~ReviewerOne_XYZ1']

        # Now add a second reviewer via an assignment edge - the existing group should be updated
        edge = openreview_client.post_edge(openreview.api.Edge(
            invitation='XYZ.cc/2025/Conference/Reviewers/-/Assignment',
            head=submissions[2].id,
            tail='~ReviewerTwo_XYZ1',
            signatures=['XYZ.cc/2025/Conference/Program_Chairs'],
            weight=1
        ))
        helpers.await_queue_edit(openreview_client, edit_id=edge.id)

        reviewers_group = openreview_client.get_group('XYZ.cc/2025/Conference/Submission3/Reviewers')
        assert '~ReviewerOne_XYZ1' in reviewers_group.members
        assert '~ReviewerTwo_XYZ1' in reviewers_group.members

    def test_assign_area_chairs_individually(self, openreview_client, helpers):
        """Same scenario as test_assign_reviewers_individually but for Area_Chairs."""

        submissions = openreview_client.get_notes(invitation='XYZ.cc/2025/Conference/-/Submission', sort='number:asc')
        assert len(submissions) == 5

        # confirm the AC group does not exist yet for paper 1
        assert openreview.tools.get_group(openreview_client, 'XYZ.cc/2025/Conference/Submission1/Area_Chairs') is None

        # post an AC assignment edge for paper 1, AreaChairOne - the group should be created on the fly
        edge = openreview_client.post_edge(openreview.api.Edge(
            invitation='XYZ.cc/2025/Conference/Area_Chairs/-/Assignment',
            head=submissions[0].id,
            tail='~AreaChairOne_XYZ1',
            signatures=['XYZ.cc/2025/Conference/Program_Chairs'],
            weight=1
        ))
        helpers.await_queue_edit(openreview_client, edit_id=edge.id)

        ac_group = openreview_client.get_group('XYZ.cc/2025/Conference/Submission1/Area_Chairs')
        assert ac_group is not None
        assert '~AreaChairOne_XYZ1' in ac_group.members

        # post a second AC assignment edge for paper 1, AreaChairTwo - the existing group should be updated
        edge = openreview_client.post_edge(openreview.api.Edge(
            invitation='XYZ.cc/2025/Conference/Area_Chairs/-/Assignment',
            head=submissions[0].id,
            tail='~AreaChairTwo_XYZ1',
            signatures=['XYZ.cc/2025/Conference/Program_Chairs'],
            weight=1
        ))
        helpers.await_queue_edit(openreview_client, edit_id=edge.id)

        ac_group = openreview_client.get_group('XYZ.cc/2025/Conference/Submission1/Area_Chairs')
        assert '~AreaChairOne_XYZ1' in ac_group.members
        assert '~AreaChairTwo_XYZ1' in ac_group.members

        # Case: AC group already exists - manually create it for paper 2, then add via edge
        assert openreview.tools.get_group(openreview_client, 'XYZ.cc/2025/Conference/Submission2/Area_Chairs') is None

        openreview_client.post_group_edit(
            invitation='XYZ.cc/2025/Conference/Area_Chairs/-/Submission_Group',
            content={
                'noteId': { 'value': submissions[1].id },
                'noteNumber': { 'value': submissions[1].number }
            },
            group=openreview.api.Group()
        )
        openreview_client.add_members_to_group('XYZ.cc/2025/Conference/Submission2/Area_Chairs', ['~AreaChairOne_XYZ1'])

        ac_group = openreview_client.get_group('XYZ.cc/2025/Conference/Submission2/Area_Chairs')
        assert ac_group.members == ['~AreaChairOne_XYZ1']

        edge = openreview_client.post_edge(openreview.api.Edge(
            invitation='XYZ.cc/2025/Conference/Area_Chairs/-/Assignment',
            head=submissions[1].id,
            tail='~AreaChairTwo_XYZ1',
            signatures=['XYZ.cc/2025/Conference/Program_Chairs'],
            weight=1
        ))
        helpers.await_queue_edit(openreview_client, edit_id=edge.id)

        ac_group = openreview_client.get_group('XYZ.cc/2025/Conference/Submission2/Area_Chairs')
        assert '~AreaChairOne_XYZ1' in ac_group.members
        assert '~AreaChairTwo_XYZ1' in ac_group.members
