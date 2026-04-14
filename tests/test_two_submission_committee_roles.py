import datetime
import openreview
import openreview.venue


class TestTwoSubmissionCommitteeRoles():

    def test_setup_venue(self, openreview_client, helpers):
        """Setup a venue using the new workflow configuration with the primary
        reviewer role being 'Expert_Reviewers'."""

        support_group_id = 'openreview.net/Support'

        helpers.create_user('programchair@xyzw.cc', 'ProgramChair', 'XYZW')
        helpers.create_user('expert_one@xyzw.cc', 'ExpertOne', 'XYZW')
        helpers.create_user('expert_two@xyzw.cc', 'ExpertTwo', 'XYZW')
        helpers.create_user('technical_one@xyzw.cc', 'TechnicalOne', 'XYZW')
        helpers.create_user('technical_two@xyzw.cc', 'TechnicalTwo', 'XYZW')
        helpers.create_user('expert_ac@xyzw.cc', 'ExpertAC', 'XYZW')
        helpers.create_user('technical_ac@xyzw.cc', 'TechnicalAC', 'XYZW')

        pc_client = openreview.api.OpenReviewClient(username='programchair@xyzw.cc', password=helpers.strong_password)

        now = datetime.datetime.now()
        due_date = now + datetime.timedelta(days=2)

        request = pc_client.post_note_edit(
            invitation='openreview.net/Support/Venue_Request/-/Conference_Review_Workflow',
            signatures=['~ProgramChair_XYZW1'],
            note=openreview.api.Note(
                content={
                    'official_venue_name': { 'value': 'The XYZW Conference' },
                    'abbreviated_venue_name': { 'value': 'XYZW 2025' },
                    'venue_website_url': { 'value': 'https://xyzw.cc/Conferences/2025' },
                    'location': { 'value': 'Amherst, Massachusetts' },
                    'venue_start_date': { 'value': openreview.tools.datetime_millis(now + datetime.timedelta(weeks=52)) },
                    'program_chair_emails': { 'value': ['programchair@xyzw.cc'] },
                    'contact_email': { 'value': 'xyzw2025.programchairs@gmail.com' },
                    'submission_start_date': { 'value': openreview.tools.datetime_millis(now) },
                    'submission_deadline': { 'value': openreview.tools.datetime_millis(due_date) },
                    'reviewers_name': { 'value': 'Reviewers' },
                    'reviewer_roles': { 'value': ['Expert_Reviewers', 'Technical_Reviewers'] },
                    'reviewer_group_layout': { 'value': 'per_role' },
                    'area_chairs_support': { 'value': True },
                    'area_chairs_name': { 'value': 'Area_Chairs' },
                    'area_chair_roles': { 'value': ['Area_Chairs', 'Technical_Area_Chairs'] },
                    'area_chair_group_layout': { 'value': 'per_role' },
                    'expected_submissions': { 'value': 100 },
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
                content={ 'venue_id': { 'value': 'XYZW.cc/2025/Conference' } }
            )
        )
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        venue_group = openreview_client.get_group('XYZW.cc/2025/Conference')
        assert venue_group
        assert venue_group.content['reviewers_name']['value'] == 'Reviewers'
        assert openreview_client.get_group('XYZW.cc/2025/Conference/Expert_Reviewers')
        assert openreview_client.get_invitation('XYZW.cc/2025/Conference/Expert_Reviewers/-/Submission_Group')

        # Umbrella group created with both reviewer roles as members
        reviewers_umbrella = openreview_client.get_group('XYZW.cc/2025/Conference/Reviewers')
        assert 'XYZW.cc/2025/Conference/Expert_Reviewers' in reviewers_umbrella.members
        assert 'XYZW.cc/2025/Conference/Technical_Reviewers' in reviewers_umbrella.members
        expert_assignment = openreview_client.get_invitation('XYZW.cc/2025/Conference/Expert_Reviewers/-/Assignment')
        assert expert_assignment.content['review_name']['value'] == 'Official_Review'
        assert expert_assignment.content['reviewers_id']['value'] == 'XYZW.cc/2025/Conference/Expert_Reviewers'
        assert expert_assignment.content['reviewers_name']['value'] == 'Expert_Reviewers'
        assert expert_assignment.content['reviewers_anon_name']['value'] == 'Expert_Reviewer_'
        assert expert_assignment.content['committee_role']['value'] == 'reviewers'
        assert expert_assignment.content['submission_committee_name']['value'] == 'Expert_Reviewers'
        assert openreview_client.get_invitation('XYZW.cc/2025/Conference/Expert_Reviewers/-/Proposed_Assignment')
        assert openreview_client.get_invitation('XYZW.cc/2025/Conference/Expert_Reviewers/-/Assignment_Configuration')

        # Second reviewer role auto-created by deployment via reviewer_roles
        assert openreview_client.get_group('XYZW.cc/2025/Conference/Technical_Reviewers')
        assert openreview_client.get_invitation('XYZW.cc/2025/Conference/Technical_Reviewers/-/Submission_Group')
        technical_assignment = openreview_client.get_invitation('XYZW.cc/2025/Conference/Technical_Reviewers/-/Assignment')
        assert technical_assignment.content['review_name']['value'] == 'Official_Review'
        assert technical_assignment.content['reviewers_id']['value'] == 'XYZW.cc/2025/Conference/Technical_Reviewers'
        assert technical_assignment.content['reviewers_name']['value'] == 'Technical_Reviewers'
        assert technical_assignment.content['reviewers_anon_name']['value'] == 'Technical_Reviewer_'
        assert technical_assignment.content['committee_role']['value'] == 'reviewers'
        assert technical_assignment.content['submission_committee_name']['value'] == 'Technical_Reviewers'
        assert openreview_client.get_invitation('XYZW.cc/2025/Conference/Technical_Reviewers/-/Proposed_Assignment')
        assert openreview_client.get_invitation('XYZW.cc/2025/Conference/Technical_Reviewers/-/Assignment_Configuration')

        # AC Assignment invitations
        ac_assignment = openreview_client.get_invitation('XYZW.cc/2025/Conference/Area_Chairs/-/Assignment')
        assert ac_assignment.content['submission_committee_name']['value'] == 'Area_Chairs'
        technical_ac_assignment = openreview_client.get_invitation('XYZW.cc/2025/Conference/Technical_Area_Chairs/-/Assignment')
        assert technical_ac_assignment.content['submission_committee_name']['value'] == 'Technical_Area_Chairs'

        # Domain has both reviewer roles + submission_reviewer_roles configured per_role
        assert venue_group.content['reviewer_roles']['value'] == ['Expert_Reviewers', 'Technical_Reviewers']
        assert venue_group.content['submission_reviewer_roles']['value'] == ['Expert_Reviewers', 'Technical_Reviewers']

        # Second AC role auto-created as well
        assert openreview_client.get_group('XYZW.cc/2025/Conference/Technical_Area_Chairs')
        assert openreview_client.get_invitation('XYZW.cc/2025/Conference/Technical_Area_Chairs/-/Submission_Group')
        assert venue_group.content['area_chair_roles']['value'] == ['Area_Chairs', 'Technical_Area_Chairs']
        assert venue_group.content['submission_area_chair_roles']['value'] == ['Area_Chairs', 'Technical_Area_Chairs']

        # Populate committee groups
        openreview_client.post_group_edit(
            invitation='XYZW.cc/2025/Conference/Expert_Reviewers/-/Members',
            signatures=['XYZW.cc/2025/Conference'],
            group=openreview.api.Group(members={ 'append': ['~ExpertOne_XYZW1', '~ExpertTwo_XYZW1'] })
        )
        openreview_client.post_group_edit(
            invitation='XYZW.cc/2025/Conference/Technical_Reviewers/-/Members',
            signatures=['XYZW.cc/2025/Conference'],
            group=openreview.api.Group(members={ 'append': ['~TechnicalOne_XYZW1', '~TechnicalTwo_XYZW1'] })
        )
        openreview_client.post_group_edit(
            invitation='XYZW.cc/2025/Conference/Area_Chairs/-/Members',
            signatures=['XYZW.cc/2025/Conference'],
            group=openreview.api.Group(members={ 'append': ['~ExpertAC_XYZW1'] })
        )
        openreview_client.post_group_edit(
            invitation='XYZW.cc/2025/Conference/Technical_Area_Chairs/-/Members',
            signatures=['XYZW.cc/2025/Conference'],
            group=openreview.api.Group(members={ 'append': ['~TechnicalAC_XYZW1'] })
        )

    def test_post_submissions(self, openreview_client, test_client, helpers):

        test_client = openreview.api.OpenReviewClient(token=test_client.token)

        for i in range(1, 4):
            note = openreview.api.Note(
                license='CC BY 4.0',
                content={
                    'title': { 'value': f'XYZW Paper title {i}' },
                    'abstract': { 'value': f'XYZW abstract {i}' },
                    'authorids': { 'value': ['~SomeFirstName_User1'] },
                    'authors': { 'value': ['SomeFirstName User'] },
                    'keywords': { 'value': ['key'] },
                    'pdf': { 'value': '/pdf/' + 'p' * 40 + '.pdf' },
                    'email_sharing': { 'value': 'We authorize the sharing of all author emails with Program Chairs.' },
                    'data_release': { 'value': 'We authorize the release of our submission and author names to the public in the event of acceptance.' },
                }
            )
            test_client.post_note_edit(
                invitation='XYZW.cc/2025/Conference/-/Submission',
                signatures=['~SomeFirstName_User1'],
                note=note
            )

        helpers.await_queue_edit(openreview_client, invitation='XYZW.cc/2025/Conference/-/Submission', count=3)

        submissions = openreview_client.get_notes(invitation='XYZW.cc/2025/Conference/-/Submission', sort='number:asc')
        assert len(submissions) == 3

    def test_close_submissions_and_create_groups(self, openreview_client, helpers):
        """Close the submission deadline and verify both reviewer roles'
        Submission_Group invitations run and create per-submission groups."""

        pc_client = openreview.api.OpenReviewClient(username='programchair@xyzw.cc', password=helpers.strong_password)
        now = datetime.datetime.now()

        pc_client.post_invitation_edit(
            invitations='XYZW.cc/2025/Conference/Expert_Reviewers/-/Submission_Group/Dates',
            content={
                'activation_date': { 'value': openreview.tools.datetime_millis(now - datetime.timedelta(minutes=30)) }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id='XYZW.cc/2025/Conference/Expert_Reviewers/-/Submission_Group-0-1', count=2)

        pc_client.post_invitation_edit(
            invitations='XYZW.cc/2025/Conference/Technical_Reviewers/-/Submission_Group/Dates',
            content={
                'activation_date': { 'value': openreview.tools.datetime_millis(now - datetime.timedelta(minutes=30)) }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id='XYZW.cc/2025/Conference/Technical_Reviewers/-/Submission_Group-0-1', count=2)

        submissions = openreview_client.get_notes(invitation='XYZW.cc/2025/Conference/-/Submission', sort='number:asc')
        assert len(submissions) == 3

        for submission in submissions:
            assert openreview_client.get_group(f'XYZW.cc/2025/Conference/Submission{submission.number}/Expert_Reviewers')
            assert openreview_client.get_group(f'XYZW.cc/2025/Conference/Submission{submission.number}/Technical_Reviewers')

    def test_setup_matching_for_both_roles(self, openreview_client, helpers):
        """Post Assignment_Configuration notes and Proposed_Assignment edges for
        both reviewer roles."""

        submissions = openreview_client.get_notes(invitation='XYZW.cc/2025/Conference/-/Submission', sort='number:asc')

        for role, reviewers in [
            ('Expert_Reviewers', ['~ExpertOne_XYZW1', '~ExpertTwo_XYZW1']),
            ('Technical_Reviewers', ['~TechnicalOne_XYZW1', '~TechnicalTwo_XYZW1'])
        ]:
            label = f'{role.lower()}-matching-1'
            openreview_client.post_note_edit(
                invitation=f'XYZW.cc/2025/Conference/{role}/-/Assignment_Configuration',
                signatures=['XYZW.cc/2025/Conference'],
                note=openreview.api.Note(
                    content={
                        'title': { 'value': label },
                        'user_demand': { 'value': '1' },
                        'max_papers': { 'value': '5' },
                        'min_papers': { 'value': '0' },
                        'alternates': { 'value': '0' },
                        'paper_invitation': { 'value': 'XYZW.cc/2025/Conference/-/Submission&content.venueid=XYZW.cc/2025/Conference/Submission' },
                        'match_group': { 'value': f'XYZW.cc/2025/Conference/{role}' },
                        'aggregate_score_invitation': { 'value': f'XYZW.cc/2025/Conference/{role}/-/Aggregate_Score' },
                        'conflicts_invitation': { 'value': f'XYZW.cc/2025/Conference/{role}/-/Conflict' },
                        'solver': { 'value': 'FairFlow' },
                        'status': { 'value': 'Complete' }
                    }
                )
            )

            for index, submission in enumerate(submissions):
                openreview_client.post_edge(openreview.api.Edge(
                    invitation=f'XYZW.cc/2025/Conference/{role}/-/Proposed_Assignment',
                    head=submission.id,
                    tail=reviewers[index % len(reviewers)],
                    signatures=['XYZW.cc/2025/Conference/Program_Chairs'],
                    weight=1,
                    label=label
                ))

    def test_deploy_assignments_for_both_roles(self, openreview_client, helpers):
        """Deploy assignments for both reviewer roles and verify each role's
        per-submission group has only the reviewers from its own matching."""

        venue = openreview.venue.helpers.get_venue(openreview_client, 'XYZW.cc/2025/Conference', support_user='openreview.net/Support')

        venue.set_assignments(assignment_title='expert_reviewers-matching-1', committee_id='XYZW.cc/2025/Conference/Expert_Reviewers')
        venue.set_assignments(assignment_title='technical_reviewers-matching-1', committee_id='XYZW.cc/2025/Conference/Technical_Reviewers')

        submissions = openreview_client.get_notes(invitation='XYZW.cc/2025/Conference/-/Submission', sort='number:asc')

        expert_members = set()
        technical_members = set()
        for submission in submissions:
            expert_group = openreview_client.get_group(f'XYZW.cc/2025/Conference/Submission{submission.number}/Expert_Reviewers')
            technical_group = openreview_client.get_group(f'XYZW.cc/2025/Conference/Submission{submission.number}/Technical_Reviewers')

            # The Expert_Reviewers per-submission group must only contain expert reviewers
            for member in expert_group.members:
                assert member in ['~ExpertOne_XYZW1', '~ExpertTwo_XYZW1']
                expert_members.add(member)

            # The Technical_Reviewers per-submission group must only contain technical reviewers
            for member in technical_group.members:
                assert member in ['~TechnicalOne_XYZW1', '~TechnicalTwo_XYZW1']
                technical_members.add(member)

        # Sanity: at least one of each role's reviewers was assigned somewhere
        assert expert_members
        assert technical_members

    def test_undeploy_assignments_for_both_roles(self, openreview_client, helpers):
        """Undeploy assignments for both reviewer roles and verify each role's
        per-submission group is emptied of its assigned members."""

        venue = openreview.venue.helpers.get_venue(openreview_client, 'XYZW.cc/2025/Conference', support_user='openreview.net/Support')

        venue.unset_assignments(assignment_title='expert_reviewers-matching-1', committee_id='XYZW.cc/2025/Conference/Expert_Reviewers')
        venue.unset_assignments(assignment_title='technical_reviewers-matching-1', committee_id='XYZW.cc/2025/Conference/Technical_Reviewers')

        submissions = openreview_client.get_notes(invitation='XYZW.cc/2025/Conference/-/Submission', sort='number:asc')

        for submission in submissions:
            expert_group = openreview_client.get_group(f'XYZW.cc/2025/Conference/Submission{submission.number}/Expert_Reviewers')
            technical_group = openreview_client.get_group(f'XYZW.cc/2025/Conference/Submission{submission.number}/Technical_Reviewers')
            assert expert_group.members == []
            assert technical_group.members == []

    def test_trigger_area_chair_submission_groups(self, openreview_client, helpers):
        """Trigger both Area_Chairs Submission_Group invitations to create
        per-paper AC groups. Matching + Assignment invitations for both AC
        roles were auto-created at deployment."""

        pc_client = openreview.api.OpenReviewClient(username='programchair@xyzw.cc', password=helpers.strong_password)
        now = datetime.datetime.now()
        for role in ['Area_Chairs', 'Technical_Area_Chairs']:
            pc_client.post_invitation_edit(
                invitations=f'XYZW.cc/2025/Conference/{role}/-/Submission_Group/Dates',
                content={
                    'activation_date': { 'value': openreview.tools.datetime_millis(now - datetime.timedelta(minutes=30)) }
                }
            )
            helpers.await_queue_edit(openreview_client, edit_id=f'XYZW.cc/2025/Conference/{role}/-/Submission_Group-0-1', count=2)

        submissions = openreview_client.get_notes(invitation='XYZW.cc/2025/Conference/-/Submission', sort='number:asc')
        for submission in submissions:
            assert openreview_client.get_group(f'XYZW.cc/2025/Conference/Submission{submission.number}/Area_Chairs')
            assert openreview_client.get_group(f'XYZW.cc/2025/Conference/Submission{submission.number}/Technical_Area_Chairs')

        assert openreview_client.get_invitation('XYZW.cc/2025/Conference/Area_Chairs/-/Assignment')
        assert openreview_client.get_invitation('XYZW.cc/2025/Conference/Technical_Area_Chairs/-/Assignment')
        assert openreview_client.get_invitation('XYZW.cc/2025/Conference/Area_Chairs/-/Proposed_Assignment')
        assert openreview_client.get_invitation('XYZW.cc/2025/Conference/Technical_Area_Chairs/-/Proposed_Assignment')

    def test_setup_ac_matching_for_both_roles(self, openreview_client, helpers):
        """Post Assignment_Configuration notes and Proposed_Assignment edges for
        both area chair roles."""

        submissions = openreview_client.get_notes(invitation='XYZW.cc/2025/Conference/-/Submission', sort='number:asc')

        for role, acs in [
            ('Area_Chairs', ['~ExpertAC_XYZW1']),
            ('Technical_Area_Chairs', ['~TechnicalAC_XYZW1'])
        ]:
            label = f'{role.lower()}-matching-1'
            openreview_client.post_note_edit(
                invitation=f'XYZW.cc/2025/Conference/{role}/-/Assignment_Configuration',
                signatures=['XYZW.cc/2025/Conference'],
                note=openreview.api.Note(
                    content={
                        'title': { 'value': label },
                        'user_demand': { 'value': '1' },
                        'max_papers': { 'value': '5' },
                        'min_papers': { 'value': '0' },
                        'alternates': { 'value': '0' },
                        'paper_invitation': { 'value': 'XYZW.cc/2025/Conference/-/Submission&content.venueid=XYZW.cc/2025/Conference/Submission' },
                        'match_group': { 'value': f'XYZW.cc/2025/Conference/{role}' },
                        'aggregate_score_invitation': { 'value': f'XYZW.cc/2025/Conference/{role}/-/Aggregate_Score' },
                        'conflicts_invitation': { 'value': f'XYZW.cc/2025/Conference/{role}/-/Conflict' },
                        'solver': { 'value': 'FairFlow' },
                        'status': { 'value': 'Complete' }
                    }
                )
            )

            for index, submission in enumerate(submissions):
                openreview_client.post_edge(openreview.api.Edge(
                    invitation=f'XYZW.cc/2025/Conference/{role}/-/Proposed_Assignment',
                    head=submission.id,
                    tail=acs[index % len(acs)],
                    signatures=['XYZW.cc/2025/Conference/Program_Chairs'],
                    weight=1,
                    label=label
                ))

    def test_deploy_ac_assignments_for_both_roles(self, openreview_client, helpers):
        """Deploy AC assignments for both area chair roles and verify each role's
        per-submission group has only its own AC."""

        venue = openreview.venue.helpers.get_venue(openreview_client, 'XYZW.cc/2025/Conference', support_user='openreview.net/Support')

        venue.set_assignments(assignment_title='area_chairs-matching-1', committee_id='XYZW.cc/2025/Conference/Area_Chairs')
        venue.set_assignments(assignment_title='technical_area_chairs-matching-1', committee_id='XYZW.cc/2025/Conference/Technical_Area_Chairs')

        submissions = openreview_client.get_notes(invitation='XYZW.cc/2025/Conference/-/Submission', sort='number:asc')

        for submission in submissions:
            ac_group = openreview_client.get_group(f'XYZW.cc/2025/Conference/Submission{submission.number}/Area_Chairs')
            technical_ac_group = openreview_client.get_group(f'XYZW.cc/2025/Conference/Submission{submission.number}/Technical_Area_Chairs')
            for member in ac_group.members:
                assert member == '~ExpertAC_XYZW1'
            for member in technical_ac_group.members:
                assert member == '~TechnicalAC_XYZW1'

    def test_setup_review_stage_for_both_roles(self, openreview_client, helpers):
        """Verify the default Official_Review only targets the primary reviewer
        role, then add a second review form for the second reviewer role and
        verify the per-paper child invitations for each form invite the right
        reviewer group."""

        pc_client = openreview.api.OpenReviewClient(username='programchair@xyzw.cc', password=helpers.strong_password)
        now = datetime.datetime.now()
        new_cdate = openreview.tools.datetime_millis(now)
        new_duedate = openreview.tools.datetime_millis(now + datetime.timedelta(days=3))

        # Trigger the default Official_Review invitation (wired to Expert_Reviewers)
        # to create per-paper child invitations.
        pc_client.post_invitation_edit(
            invitations='XYZW.cc/2025/Conference/-/Official_Review/Dates',
            content={
                'activation_date': { 'value': new_cdate },
                'due_date': { 'value': new_duedate },
                'expiration_date': { 'value': new_duedate }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id='XYZW.cc/2025/Conference/-/Official_Review-0-1', count=2)

        submissions = openreview_client.get_notes(invitation='XYZW.cc/2025/Conference/-/Submission', sort='number:asc')
        for submission in submissions:
            child = openreview_client.get_invitation(f'XYZW.cc/2025/Conference/Submission{submission.number}/-/Official_Review')
            assert f'XYZW.cc/2025/Conference/Submission{submission.number}/Expert_Reviewers' in child.invitees
            assert f'XYZW.cc/2025/Conference/Submission{submission.number}/Technical_Reviewers' not in child.invitees
            # Only Expert_Reviewer anon signatures are allowed
            signatures_items = child.edit['signatures']['param']['items']
            assert any('Expert_Reviewer_' in item.get('prefix', '') for item in signatures_items)
            assert not any('Technical_Reviewer_' in item.get('prefix', '') for item in signatures_items)

        # Create a second, distinct review form for the Technical_Reviewers role.
        venue = openreview.venue.helpers.get_venue(openreview_client, 'XYZW.cc/2025/Conference', support_user='openreview.net/Support')
        venue.review_stage = openreview.stages.ReviewStage(
            name='Technical_Review',
            child_invitations_name='Technical_Review',
            start_date=now,
            due_date=now + datetime.timedelta(days=7),
            submission_reviewer_roles=['Technical_Reviewers'],
            additional_fields={
                'technical_soundness': {
                    'order': 1,
                    'description': 'How technically sound is the paper?',
                    'value': {
                        'param': {
                            'type': 'integer',
                            'enum': [1, 2, 3, 4, 5],
                            'input': 'radio'
                        }
                    }
                }
            }
        )
        venue.invitation_builder.set_review_invitation()

        helpers.await_queue_edit(openreview_client, edit_id='XYZW.cc/2025/Conference/-/Technical_Review-0-1', count=1)

        for submission in submissions:
            child = openreview_client.get_invitation(f'XYZW.cc/2025/Conference/Submission{submission.number}/-/Technical_Review')
            assert f'XYZW.cc/2025/Conference/Submission{submission.number}/Technical_Reviewers' in child.invitees
            assert f'XYZW.cc/2025/Conference/Submission{submission.number}/Expert_Reviewers' not in child.invitees
            assert 'technical_soundness' in child.edit['note']['content']
            signatures_items = child.edit['signatures']['param']['items']
            assert any('Technical_Reviewer_' in item.get('prefix', '') for item in signatures_items)
            assert not any('Expert_Reviewer_' in item.get('prefix', '') for item in signatures_items)

        # Reviewer assignments were undeployed earlier; redeploy them so reviewers
        # can actually post reviews for submission 1.
        venue.set_assignments(assignment_title='expert_reviewers-matching-1', committee_id='XYZW.cc/2025/Conference/Expert_Reviewers')
        venue.set_assignments(assignment_title='technical_reviewers-matching-1', committee_id='XYZW.cc/2025/Conference/Technical_Reviewers')

        # Run Submission_Change_Before_Reviewing so that submissions become
        # readable by both per-paper reviewer groups.
        pc_client.post_invitation_edit(
            invitations='XYZW.cc/2025/Conference/-/Submission_Change_Before_Reviewing/Dates',
            content={
                'activation_date': { 'value': openreview.tools.datetime_millis(now - datetime.timedelta(minutes=30)) }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id='XYZW.cc/2025/Conference/-/Submission_Change_Before_Reviewing-0-1', count=2)

        submission1 = openreview_client.get_note(submissions[0].id)
        assert f'XYZW.cc/2025/Conference/Submission{submission1.number}/Expert_Reviewers' in submission1.readers
        assert f'XYZW.cc/2025/Conference/Submission{submission1.number}/Technical_Reviewers' in submission1.readers

        # Post one Official_Review as an assigned Expert reviewer for submission 1
        expert_client = openreview.api.OpenReviewClient(username='expert_one@xyzw.cc', password=helpers.strong_password)
        expert_anon_groups = expert_client.get_groups(prefix=f'XYZW.cc/2025/Conference/Submission{submission1.number}/Expert_Reviewer_.*', signatory='~ExpertOne_XYZW1')
        if not expert_anon_groups:
            expert_client = openreview.api.OpenReviewClient(username='expert_two@xyzw.cc', password=helpers.strong_password)
            expert_anon_groups = expert_client.get_groups(prefix=f'XYZW.cc/2025/Conference/Submission{submission1.number}/Expert_Reviewer_.*', signatory='~ExpertTwo_XYZW1')
        assert len(expert_anon_groups) == 1

        expert_review = expert_client.post_note_edit(
            invitation=f'XYZW.cc/2025/Conference/Submission{submission1.number}/-/Official_Review',
            signatures=[expert_anon_groups[0].id],
            note=openreview.api.Note(
                content={
                    'title': { 'value': 'Expert review' },
                    'review': { 'value': 'Solid contribution from an expert perspective.' },
                    'rating': { 'value': 8 },
                    'confidence': { 'value': 4 }
                }
            )
        )
        helpers.await_queue_edit(openreview_client, edit_id=expert_review['id'])

        # Post one Technical_Review as an assigned Technical reviewer for submission 1
        technical_client = openreview.api.OpenReviewClient(username='technical_one@xyzw.cc', password=helpers.strong_password)
        technical_anon_groups = technical_client.get_groups(prefix=f'XYZW.cc/2025/Conference/Submission{submission1.number}/Technical_Reviewer_.*', signatory='~TechnicalOne_XYZW1')
        if not technical_anon_groups:
            technical_client = openreview.api.OpenReviewClient(username='technical_two@xyzw.cc', password=helpers.strong_password)
            technical_anon_groups = technical_client.get_groups(prefix=f'XYZW.cc/2025/Conference/Submission{submission1.number}/Technical_Reviewer_.*', signatory='~TechnicalTwo_XYZW1')
        assert len(technical_anon_groups) == 1

        technical_review_note = technical_client.post_note_edit(
            invitation=f'XYZW.cc/2025/Conference/Submission{submission1.number}/-/Technical_Review',
            signatures=[technical_anon_groups[0].id],
            note=openreview.api.Note(
                content={
                    'title': { 'value': 'Technical review' },
                    'review': { 'value': 'Technically sound implementation.' },
                    'rating': { 'value': 7 },
                    'confidence': { 'value': 4 },
                    'technical_soundness': { 'value': 4 }
                }
            )
        )
        helpers.await_queue_edit(openreview_client, edit_id=technical_review_note['id'])

        official_reviews = openreview_client.get_notes(invitation=f'XYZW.cc/2025/Conference/Submission{submission1.number}/-/Official_Review')
        assert len(official_reviews) == 1
        technical_reviews = openreview_client.get_notes(invitation=f'XYZW.cc/2025/Conference/Submission{submission1.number}/-/Technical_Review')
        assert len(technical_reviews) == 1

    def test_undeploy_ac_assignments_for_both_roles(self, openreview_client, helpers):
        """Undeploy AC assignments for both area chair roles and verify each
        role's per-submission group is emptied."""

        venue = openreview.venue.helpers.get_venue(openreview_client, 'XYZW.cc/2025/Conference', support_user='openreview.net/Support')

        venue.unset_assignments(assignment_title='area_chairs-matching-1', committee_id='XYZW.cc/2025/Conference/Area_Chairs')
        venue.unset_assignments(assignment_title='technical_area_chairs-matching-1', committee_id='XYZW.cc/2025/Conference/Technical_Area_Chairs')

        submissions = openreview_client.get_notes(invitation='XYZW.cc/2025/Conference/-/Submission', sort='number:asc')

        for submission in submissions:
            ac_group = openreview_client.get_group(f'XYZW.cc/2025/Conference/Submission{submission.number}/Area_Chairs')
            technical_ac_group = openreview_client.get_group(f'XYZW.cc/2025/Conference/Submission{submission.number}/Technical_Area_Chairs')
            assert ac_group.members == []
            assert technical_ac_group.members == []
