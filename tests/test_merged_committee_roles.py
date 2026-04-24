import datetime
import openreview
import openreview.venue


class TestMergedCommitteeRoles():

    def test_setup_venue(self, openreview_client, helpers):
        """Setup a venue with two reviewer roles and two area chair roles
        configured in the 'shared' (merged) layout. With this layout, all
        roles share a single per-submission group named after the primary
        role."""

        support_group_id = 'openreview.net/Support'

        helpers.create_user('programchair@mrg.cc', 'ProgramChair', 'MRG')
        helpers.create_user('expert_one@mrg.cc', 'ExpertOne', 'MRG')
        helpers.create_user('expert_two@mrg.cc', 'ExpertTwo', 'MRG')
        helpers.create_user('technical_one@mrg.cc', 'TechnicalOne', 'MRG')
        helpers.create_user('technical_two@mrg.cc', 'TechnicalTwo', 'MRG')
        helpers.create_user('expert_ac@mrg.cc', 'ExpertAC', 'MRG')
        helpers.create_user('technical_ac@mrg.cc', 'TechnicalAC', 'MRG')

        pc_client = openreview.api.OpenReviewClient(username='programchair@mrg.cc', password=helpers.strong_password)

        now = datetime.datetime.now()
        due_date = now + datetime.timedelta(days=2)

        request = pc_client.post_note_edit(
            invitation='openreview.net/Support/Venue_Request/-/Conference_Review_Workflow',
            signatures=['~ProgramChair_MRG1'],
            note=openreview.api.Note(
                content={
                    'official_venue_name': { 'value': 'The MRG Conference' },
                    'abbreviated_venue_name': { 'value': 'MRG 2025' },
                    'venue_website_url': { 'value': 'https://mrg.cc/Conferences/2025' },
                    'location': { 'value': 'Amherst, Massachusetts' },
                    'venue_start_date': { 'value': openreview.tools.datetime_millis(now + datetime.timedelta(weeks=52)) },
                    'program_chair_emails': { 'value': ['programchair@mrg.cc'] },
                    'contact_email': { 'value': 'mrg2025.programchairs@gmail.com' },
                    'submission_start_date': { 'value': openreview.tools.datetime_millis(now) },
                    'submission_deadline': { 'value': openreview.tools.datetime_millis(due_date) },
                    'reviewer_groups_names': { 'value': ['Expert_Reviewers', 'Technical_Reviewers'] },
                    'reviewer_group_layout': { 'value': 'shared' },
                    'area_chairs_support': { 'value': True },
                    'area_chair_groups_names': { 'value': ['Area_Chairs', 'Technical_Area_Chairs'] },
                    'area_chair_group_layout': { 'value': 'shared' },
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
                content={ 'venue_id': { 'value': 'MRG.cc/2025/Conference' } }
            )
        )
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        venue_group = openreview_client.get_group('MRG.cc/2025/Conference')
        assert venue_group
        assert venue_group.content['reviewers_name']['value'] == 'Expert_Reviewers'

        # Both reviewer role top-level groups exist so each role can have its
        # own matching, but the shared layout means both assignment invitations
        # point to the same per-submission group name (the primary).
        assert openreview_client.get_group('MRG.cc/2025/Conference/Expert_Reviewers')
        assert openreview_client.get_group('MRG.cc/2025/Conference/Technical_Reviewers')

        expert_assignment = openreview_client.get_invitation('MRG.cc/2025/Conference/Expert_Reviewers/-/Assignment')
        assert expert_assignment.content['reviewers_name']['value'] == 'Expert_Reviewers'
        assert expert_assignment.content['submission_committee_name']['value'] == 'Expert_Reviewers'

        technical_assignment = openreview_client.get_invitation('MRG.cc/2025/Conference/Technical_Reviewers/-/Assignment')
        # Shared layout: technical role reuses the primary submission group name
        assert technical_assignment.content['reviewers_name']['value'] == 'Expert_Reviewers'
        assert technical_assignment.content['submission_committee_name']['value'] == 'Expert_Reviewers'

        # AC Assignment invitations - also share the primary AC submission name
        ac_assignment = openreview_client.get_invitation('MRG.cc/2025/Conference/Area_Chairs/-/Assignment')
        assert ac_assignment.content['submission_committee_name']['value'] == 'Area_Chairs'
        technical_ac_assignment = openreview_client.get_invitation('MRG.cc/2025/Conference/Technical_Area_Chairs/-/Assignment')
        assert technical_ac_assignment.content['submission_committee_name']['value'] == 'Area_Chairs'

        # Domain has both reviewer roles but a single shared submission role
        assert venue_group.content['reviewer_roles']['value'] == ['Expert_Reviewers', 'Technical_Reviewers']
        assert venue_group.content['submission_reviewer_roles']['value'] == ['Expert_Reviewers']
        assert venue_group.content['area_chair_roles']['value'] == ['Area_Chairs', 'Technical_Area_Chairs']
        assert venue_group.content['submission_area_chair_roles']['value'] == ['Area_Chairs']

        # Only the primary Official_Review invitation is auto-created for shared layout
        assert venue_group.content['review_names']['value'] == ['Official_Review']
        assert openreview_client.get_invitation('MRG.cc/2025/Conference/-/Official_Review')

        # Populate committee groups
        openreview_client.post_group_edit(
            invitation='MRG.cc/2025/Conference/Expert_Reviewers/-/Members',
            signatures=['MRG.cc/2025/Conference'],
            group=openreview.api.Group(members={ 'append': ['~ExpertOne_MRG1', '~ExpertTwo_MRG1'] })
        )
        openreview_client.post_group_edit(
            invitation='MRG.cc/2025/Conference/Technical_Reviewers/-/Members',
            signatures=['MRG.cc/2025/Conference'],
            group=openreview.api.Group(members={ 'append': ['~TechnicalOne_MRG1', '~TechnicalTwo_MRG1'] })
        )
        openreview_client.post_group_edit(
            invitation='MRG.cc/2025/Conference/Area_Chairs/-/Members',
            signatures=['MRG.cc/2025/Conference'],
            group=openreview.api.Group(members={ 'append': ['~ExpertAC_MRG1'] })
        )
        openreview_client.post_group_edit(
            invitation='MRG.cc/2025/Conference/Technical_Area_Chairs/-/Members',
            signatures=['MRG.cc/2025/Conference'],
            group=openreview.api.Group(members={ 'append': ['~TechnicalAC_MRG1'] })
        )

    def test_post_submissions(self, openreview_client, test_client, helpers):

        test_client = openreview.api.OpenReviewClient(token=test_client.token)

        for i in range(1, 4):
            note = openreview.api.Note(
                license='CC BY 4.0',
                content={
                    'title': { 'value': f'MRG Paper title {i}' },
                    'abstract': { 'value': f'MRG abstract {i}' },
                    'authorids': { 'value': ['~SomeFirstName_User1'] },
                    'authors': { 'value': ['SomeFirstName User'] },
                    'keywords': { 'value': ['key'] },
                    'pdf': { 'value': '/pdf/' + 'p' * 40 + '.pdf' },
                    'email_sharing': { 'value': 'We authorize the sharing of all author emails with Program Chairs.' },
                    'data_release': { 'value': 'We authorize the release of our submission and author names to the public in the event of acceptance.' },
                }
            )
            test_client.post_note_edit(
                invitation='MRG.cc/2025/Conference/-/Submission',
                signatures=['~SomeFirstName_User1'],
                note=note
            )

        helpers.await_queue_edit(openreview_client, invitation='MRG.cc/2025/Conference/-/Submission', count=3)

        submissions = openreview_client.get_notes(invitation='MRG.cc/2025/Conference/-/Submission', sort='number:asc')
        assert len(submissions) == 3

    def test_close_submissions_and_create_groups(self, openreview_client, helpers):
        """Close the submission deadline and verify that only the primary
        reviewer role's Submission_Group invitation creates per-submission
        groups (the secondary role shares the primary's group in this layout)."""

        pc_client = openreview.api.OpenReviewClient(username='programchair@mrg.cc', password=helpers.strong_password)
        now = datetime.datetime.now()

        pc_client.post_invitation_edit(
            invitations='MRG.cc/2025/Conference/Expert_Reviewers/-/Submission_Group/Dates',
            content={
                'activation_date': { 'value': openreview.tools.datetime_millis(now - datetime.timedelta(minutes=30)) }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id='MRG.cc/2025/Conference/Expert_Reviewers/-/Submission_Group-0-1', count=2)

        submissions = openreview_client.get_notes(invitation='MRG.cc/2025/Conference/-/Submission', sort='number:asc')
        assert len(submissions) == 3

        for submission in submissions:
            # Only the primary per-submission reviewers group exists
            assert openreview_client.get_group(f'MRG.cc/2025/Conference/Submission{submission.number}/Expert_Reviewers')
            technical_group = openreview.tools.get_group(openreview_client, f'MRG.cc/2025/Conference/Submission{submission.number}/Technical_Reviewers')
            assert technical_group is None

    def test_setup_matching_for_both_roles(self, openreview_client, helpers):
        """Each reviewer role runs its own matching (distinct match_group) but
        both assignment invitations write into the shared per-submission group."""

        submissions = openreview_client.get_notes(invitation='MRG.cc/2025/Conference/-/Submission', sort='number:asc')

        for role, reviewers in [
            ('Expert_Reviewers', ['~ExpertOne_MRG1', '~ExpertTwo_MRG1']),
            ('Technical_Reviewers', ['~TechnicalOne_MRG1', '~TechnicalTwo_MRG1'])
        ]:
            label = f'{role.lower()}-matching-1'
            openreview_client.post_note_edit(
                invitation=f'MRG.cc/2025/Conference/{role}/-/Assignment_Configuration',
                signatures=['MRG.cc/2025/Conference'],
                note=openreview.api.Note(
                    content={
                        'title': { 'value': label },
                        'user_demand': { 'value': '1' },
                        'max_papers': { 'value': '5' },
                        'min_papers': { 'value': '0' },
                        'alternates': { 'value': '0' },
                        'paper_invitation': { 'value': 'MRG.cc/2025/Conference/-/Submission&content.venueid=MRG.cc/2025/Conference/Submission' },
                        'match_group': { 'value': f'MRG.cc/2025/Conference/{role}' },
                        'aggregate_score_invitation': { 'value': f'MRG.cc/2025/Conference/{role}/-/Aggregate_Score' },
                        'conflicts_invitation': { 'value': f'MRG.cc/2025/Conference/{role}/-/Conflict' },
                        'solver': { 'value': 'FairFlow' },
                        'status': { 'value': 'Complete' }
                    }
                )
            )

            for index, submission in enumerate(submissions):
                openreview_client.post_edge(openreview.api.Edge(
                    invitation=f'MRG.cc/2025/Conference/{role}/-/Proposed_Assignment',
                    head=submission.id,
                    tail=reviewers[index % len(reviewers)],
                    signatures=['MRG.cc/2025/Conference/Program_Chairs'],
                    weight=1,
                    label=label
                ))

    def test_deploy_assignments_share_one_group(self, openreview_client, helpers):
        """Deploy assignments for both reviewer roles and verify that reviewers
        from both roles end up in the same per-submission reviewers group."""

        venue = openreview.venue.helpers.get_venue(openreview_client, 'MRG.cc/2025/Conference', support_user='openreview.net/Support')

        venue.set_assignments(assignment_title='expert_reviewers-matching-1', committee_id='MRG.cc/2025/Conference/Expert_Reviewers')
        venue.set_assignments(assignment_title='technical_reviewers-matching-1', committee_id='MRG.cc/2025/Conference/Technical_Reviewers')

        submissions = openreview_client.get_notes(invitation='MRG.cc/2025/Conference/-/Submission', sort='number:asc')

        all_expert_members = {'~ExpertOne_MRG1', '~ExpertTwo_MRG1'}
        all_technical_members = {'~TechnicalOne_MRG1', '~TechnicalTwo_MRG1'}

        merged_members = set()
        for submission in submissions:
            reviewers_group = openreview_client.get_group(f'MRG.cc/2025/Conference/Submission{submission.number}/Expert_Reviewers')

            # The shared per-submission group holds reviewers from BOTH roles
            expert_from_group = set(reviewers_group.members) & all_expert_members
            technical_from_group = set(reviewers_group.members) & all_technical_members
            assert expert_from_group, f'Submission {submission.number} missing an Expert reviewer'
            assert technical_from_group, f'Submission {submission.number} missing a Technical reviewer'

            # Only reviewers from the two configured role groups should be present
            for member in reviewers_group.members:
                assert member in all_expert_members | all_technical_members
            merged_members |= set(reviewers_group.members)

            # No separate Technical_Reviewers per-submission group is created
            assert openreview.tools.get_group(openreview_client, f'MRG.cc/2025/Conference/Submission{submission.number}/Technical_Reviewers') is None

        # Sanity: at least one member from each role was assigned somewhere
        assert merged_members & all_expert_members
        assert merged_members & all_technical_members
