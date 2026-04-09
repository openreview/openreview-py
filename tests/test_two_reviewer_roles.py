import datetime
import openreview
import openreview.venue


class TestTwoReviewerRoles():

    def test_setup_venue(self, openreview_client, helpers):
        """Setup a venue using the new workflow configuration with the primary
        reviewer role being 'Expert_Reviewers'."""

        support_group_id = 'openreview.net/Support'

        helpers.create_user('programchair@xyzw.cc', 'ProgramChair', 'XYZW')
        helpers.create_user('expert_one@xyzw.cc', 'ExpertOne', 'XYZW')
        helpers.create_user('expert_two@xyzw.cc', 'ExpertTwo', 'XYZW')
        helpers.create_user('technical_one@xyzw.cc', 'TechnicalOne', 'XYZW')
        helpers.create_user('technical_two@xyzw.cc', 'TechnicalTwo', 'XYZW')

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
                    'reviewers_name': { 'value': 'Expert_Reviewers' },
                    'area_chairs_name': { 'value': 'Area_Chairs' },
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
        assert venue_group.content['reviewers_name']['value'] == 'Expert_Reviewers'
        assert openreview_client.get_group('XYZW.cc/2025/Conference/Expert_Reviewers')
        assert openreview_client.get_invitation('XYZW.cc/2025/Conference/Expert_Reviewers/-/Submission_Group')
        assert openreview_client.get_invitation('XYZW.cc/2025/Conference/Expert_Reviewers/-/Assignment')
        assert openreview_client.get_invitation('XYZW.cc/2025/Conference/Expert_Reviewers/-/Proposed_Assignment')
        assert openreview_client.get_invitation('XYZW.cc/2025/Conference/Expert_Reviewers/-/Assignment_Configuration')

        # add expert reviewers to the Expert_Reviewers group
        openreview_client.post_group_edit(
            invitation='XYZW.cc/2025/Conference/Expert_Reviewers/-/Members',
            signatures=['XYZW.cc/2025/Conference'],
            group=openreview.api.Group(
                members={ 'append': ['~ExpertOne_XYZW1', '~ExpertTwo_XYZW1'] }
            )
        )

    def test_setup_second_reviewer_role(self, openreview_client, helpers):
        """Manually add a second reviewer role 'Technical_Reviewers' to the
        domain group and create the additional invitations needed for matching
        and deployment to use that role."""

        # 1. Create the Technical_Reviewers group and all related invitations
        #    via the Committee_Group template invitation.
        openreview_client.post_group_edit(
            invitation='openreview.net/Template/-/Committee_Group',
            signatures=['openreview.net/Template'],
            content={
                'venue_id': { 'value': 'XYZW.cc/2025/Conference' },
                'committee_name': { 'value': 'Technical_Reviewers' },
                'committee_role': { 'value': 'reviewers' },
                'committee_pretty_name': { 'value': 'Technical Reviewers' },
                'committee_anon_name': { 'value': 'Technical_Reviewer_' },
                'committee_submitted_name': { 'value': 'Submitted' },
                'additional_readers': { 'value': [] }
            },
            await_process=True
        )

        assert openreview_client.get_group('XYZW.cc/2025/Conference/Technical_Reviewers')
        assert openreview_client.get_invitation('XYZW.cc/2025/Conference/Technical_Reviewers/-/Message')
        assert openreview_client.get_invitation('XYZW.cc/2025/Conference/Technical_Reviewers/-/Members')        
        assert openreview_client.get_invitation('XYZW.cc/2025/Conference/Technical_Reviewers/-/Recruitment_Request')        

        # 2. Add the technical reviewers to the new group
        openreview_client.post_group_edit(
            invitation='XYZW.cc/2025/Conference/Technical_Reviewers/-/Members',
            signatures=['XYZW.cc/2025/Conference'],
            group=openreview.api.Group(
                members={ 'append': ['~TechnicalOne_XYZW1', '~TechnicalTwo_XYZW1'] }
            )
        )

        # 3. Update the venue domain content to include both reviewer roles
        openreview_client.post_group_edit(
            invitation='XYZW.cc/2025/Conference/-/Edit',
            signatures=['XYZW.cc/2025/Conference'],
            group=openreview.api.Group(
                id='XYZW.cc/2025/Conference',
                content={
                    'reviewer_roles': { 'value': ['Expert_Reviewers', 'Technical_Reviewers'] }
                }
            )
        )

        domain = openreview_client.get_group('XYZW.cc/2025/Conference')
        assert domain.content['reviewer_roles']['value'] == ['Expert_Reviewers', 'Technical_Reviewers']

        # 4. Build a Venue object from the venue domain group so all config is
        #    read from the deployed venue. We use this object only to invoke
        #    invitation_builder methods that create the matching and deployment
        #    invitations needed for the second role.
        venue = openreview.venue.helpers.get_venue(openreview_client, 'XYZW.cc/2025/Conference', support_user='openreview.net/Support')
        assert venue.reviewer_roles == ['Expert_Reviewers', 'Technical_Reviewers']
        assert venue.is_template_related_workflow() 

        venue.invitation_builder.set_submission_reviewer_group_invitation(reviewers_name='Technical_Reviewers')
        assert openreview_client.get_invitation('XYZW.cc/2025/Conference/Technical_Reviewers/-/Submission_Group')

        venue.setup_committee_matching(committee_id=f'XYZW.cc/2025/Conference/Technical_Reviewers')

        venue.invitation_builder.set_assignment_invitation('XYZW.cc/2025/Conference/Technical_Reviewers')

        assert openreview_client.get_invitation('XYZW.cc/2025/Conference/Technical_Reviewers/-/Assignment')
        assert openreview_client.get_invitation(f'XYZW.cc/2025/Conference/Technical_Reviewers/-/Proposed_Assignment')
        assert openreview_client.get_invitation(f'XYZW.cc/2025/Conference/Technical_Reviewers/-/Assignment_Configuration')

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

        venue = openreview.helpers.get_venue(openreview_client, 'XYZW.cc/2025/Conference', support_user='openreview.net/Support')

        # deploy Expert_Reviewers
        venue.reviewers_name = 'Expert_Reviewers'
        venue.set_assignments(assignment_title='expert_reviewers-matching-1', committee_id='XYZW.cc/2025/Conference/Expert_Reviewers')

        # deploy Technical_Reviewers
        venue.reviewers_name = 'Technical_Reviewers'
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
