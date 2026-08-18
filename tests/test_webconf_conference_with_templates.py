import datetime
import openreview
import openreview.venue
from selenium.webdriver.common.by import By


VENUE_ID = 'ACM.org/TheWebConf/2026/Conference'

# (track value, track description). The short value is what a submission and a
# committee group store and what matching filters on; the long description is
# only shown to authors on the submission form.
TRACKS = [
    ('Econ', 'Economics, Online Markets, and Human Computation'),
    ('Graph', 'Graph Algorithms and Learning for the Web'),
    ('RespWeb', 'Responsible Web'),
    ('Search', 'Search'),
    ('Security', 'Security'),
    ('Semantics', 'Semantics and Knowledge'),
    ('Social', 'Social Networks, Social Media, and Society'),
    ('Systems', 'Systems and Infrastructure for Web, Mobile, and WoT'),
    ('RecSys', 'User Modeling and Recommendation'),
    ('Mining', 'Web Mining and Content Analysis'),
    ('COI', 'Conflict of Interest')
]

TRACK_OPTIONS = [{ 'value': value, 'description': description } for value, description in TRACKS]

# The first role of each list is the venue-wide role; the rest are per-track.
REVIEWER_ROLES = ['Reviewers'] + [f'{value}_Reviewers' for value, _ in TRACKS]
AREA_CHAIR_ROLES = ['Area_Chairs'] + [f'{value}_Area_Chairs' for value, _ in TRACKS]
SENIOR_AREA_CHAIR_ROLES = ['Senior_Area_Chairs'] + [f'{value}_Senior_Area_Chairs' for value, _ in TRACKS]

# Tracks exercised through the expensive matching/deployment steps. The cheap
# invitation-level assertions run over every track.
SAMPLED_TRACKS = ['Econ', 'COI']


class TestWebConfTracks():

    def test_setup_venue(self, openreview_client, helpers):
        """Deploy a multi-track venue: one venue-wide role plus one role per
        track for reviewers, area chairs and senior area chairs."""

        support_group_id = 'openreview.net/Support'

        helpers.create_user('programchair@webconf.cc', 'ProgramChair', 'WebConf')
        for track in SAMPLED_TRACKS:
            helpers.create_user(f'{track.lower()}_reviewer@webconf.cc', f'{track}Reviewer', 'WebConf')
            helpers.create_user(f'{track.lower()}_ac@webconf.cc', f'{track}AC', 'WebConf')
            helpers.create_user(f'{track.lower()}_sac@webconf.cc', f'{track}SAC', 'WebConf')

        pc_client = openreview.api.OpenReviewClient(username='programchair@webconf.cc', password=helpers.strong_password)

        now = datetime.datetime.now()
        due_date = now + datetime.timedelta(days=2)

        request = pc_client.post_note_edit(
            invitation='openreview.net/Support/Venue_Request/-/Conference_Review_Workflow',
            signatures=['~ProgramChair_WebConf1'],
            note=openreview.api.Note(
                content={
                    'official_venue_name': { 'value': 'The Web Conference 2026' },
                    'abbreviated_venue_name': { 'value': 'TheWebConf 2026' },
                    'venue_website_url': { 'value': 'https://www2026.thewebconf.org' },
                    'location': { 'value': 'Dubai, United Arab Emirates' },
                    'venue_start_date': { 'value': openreview.tools.datetime_millis(now + datetime.timedelta(weeks=52)) },
                    'program_chair_emails': { 'value': ['programchair@webconf.cc'] },
                    'contact_email': { 'value': 'webconf2026.programchairs@gmail.com' },
                    'submission_start_date': { 'value': openreview.tools.datetime_millis(now) },
                    'submission_deadline': { 'value': openreview.tools.datetime_millis(due_date) },
                    'reviewer_groups_names': { 'value': REVIEWER_ROLES },
                    'area_chairs_support': { 'value': True },
                    'area_chair_groups_names': { 'value': AREA_CHAIR_ROLES },
                    'senior_area_chairs_support': { 'value': True },
                    'senior_area_chair_groups_names': { 'value': SENIOR_AREA_CHAIR_ROLES },
                    'expected_submissions': { 'value': 1000 },
                    'venue_organizer_agreement': {
                        'value': [
                            'OpenReview natively supports a wide variety of reviewing workflow configurations. However, if we want significant reviewing process customizations or experiments, we will detail these requests to the OpenReview staff at least three months in advance.',
                            'We will ask authors and reviewers to create an OpenReview Profile at least two weeks in advance of the paper submission deadlines.',
                            'When assembling our group of reviewers, we will only include email addresses or OpenReview Profile IDs of people we know to have authored publications relevant to our venue.  (We will not solicit new reviewers using an open web form, because unfortunately some malicious actors sometimes try to create "fake ids" aiming to be assigned to review their own paper submissions.)',
                            'We acknowledge that, if our venue\'s reviewing workflow is non-standard, or if our venue is expecting more than a few hundred submissions for any one deadline, we should designate our own Workflow Chair, who will read the OpenReview documentation and manage our workflow configurations throughout the reviewing process.',
                            'We acknowledge that OpenReview staff work Monday-Friday during standard business hours US Eastern time, and we cannot expect support responses outside those times.  For this reason, we recommend setting submission and reviewing deadlines Monday through Thursday.',
                            'We will treat the OpenReview staff with kindness and consideration.',
                            'We acknowledge that authors and reviewers will be required to share their preferred email.'
                        ]
                    }
                }
            )
        )
        helpers.await_queue_edit(openreview_client, edit_id=request['id'])

        request = openreview_client.get_note(request['note']['id'])

        edit = openreview_client.post_note_edit(
            invitation='openreview.net/Support/Venue_Request/Conference_Review_Workflow/-/Deployment',
            signatures=[support_group_id],
            note=openreview.api.Note(
                id=request.id,
                content={ 'venue_id': { 'value': VENUE_ID } }
            )
        )
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        venue_group = openreview_client.get_group(VENUE_ID)
        assert venue_group
        assert venue_group.content['reviewer_roles']['value'] == REVIEWER_ROLES
        assert venue_group.content['area_chair_roles']['value'] == AREA_CHAIR_ROLES
        assert venue_group.content['senior_area_chair_roles']['value'] == SENIOR_AREA_CHAIR_ROLES

        # every track role gets its own group and its own matching invitations
        for role in REVIEWER_ROLES + AREA_CHAIR_ROLES + SENIOR_AREA_CHAIR_ROLES:
            assert openreview_client.get_group(f'{VENUE_ID}/{role}')

        for role in REVIEWER_ROLES + AREA_CHAIR_ROLES:
            assert openreview_client.get_invitation(f'{VENUE_ID}/{role}/-/Assignment')
            assert openreview_client.get_invitation(f'{VENUE_ID}/{role}/-/Proposed_Assignment')
            assert openreview_client.get_invitation(f'{VENUE_ID}/{role}/-/Assignment_Configuration')

    def test_add_track_field_to_submission(self, openreview_client, helpers):
        """Add the 'track' field to the submission form. Authors pick a long
        description; the submission stores the short track value."""

        pc_client = openreview.api.OpenReviewClient(username='programchair@webconf.cc', password=helpers.strong_password)

        content_invitation = openreview_client.get_invitation(f'{VENUE_ID}/-/Submission/Form_Fields')
        assert content_invitation

        content_edit = pc_client.post_invitation_edit(
            invitations=content_invitation.id,
            content={
                'content': {
                    'value': {
                        'track': {
                            'order': 8,
                            'description': 'Select the track your submission belongs to.',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'enum': TRACK_OPTIONS,
                                    'input': 'select'
                                }
                            }
                        }
                    }
                },
                'license': {
                    'value': [{ 'value': 'CC BY 4.0', 'description': 'CC BY 4.0' }]
                }
            }
        )
        ## this edit runs a process that creates the Track invitations
        helpers.await_queue_edit(openreview_client, edit_id=content_edit['id'])

        submission_invitation = openreview_client.get_invitation(f'{VENUE_ID}/-/Submission')
        assert submission_invitation.edit['note']['content']['track']['value']['param']['enum'] == TRACK_OPTIONS

    def test_set_track_on_committee_groups(self, openreview_client, helpers):
        """Each per-track committee group stores its own track value. Matching
        reads the track from the group, so no track argument is threaded
        through the matching calls."""

        pc_client = openreview.api.OpenReviewClient(username='programchair@webconf.cc', password=helpers.strong_password)

        for track, _ in TRACKS:
            for role in [f'{track}_Reviewers', f'{track}_Area_Chairs', f'{track}_Senior_Area_Chairs']:
                group_id = f'{VENUE_ID}/{role}'

                track_invitation = openreview_client.get_invitation(f'{group_id}/-/Track')
                assert track_invitation.edit['content']['track']['value']['param']['enum'] == TRACK_OPTIONS

                track_edit = pc_client.post_group_edit(
                    invitation=f'{group_id}/-/Track',
                    content={ 'track': { 'value': track } }
                )
                ## the Track invitation runs a process that re-scopes this
                ## group's matching invitations
                helpers.await_queue_edit(openreview_client, edit_id=track_edit['id'])

                group = openreview_client.get_group(group_id)
                assert group.content['track']['value'] == track

        # the venue-wide roles stay untracked and keep seeing every submission
        for role in ['Reviewers', 'Area_Chairs', 'Senior_Area_Chairs']:
            group = openreview_client.get_group(f'{VENUE_ID}/{role}')
            assert 'track' not in group.content

    def test_post_submissions(self, openreview_client, test_client, helpers):
        """Post one submission per sampled track."""

        test_client = openreview.api.OpenReviewClient(token=test_client.token)

        for index, track in enumerate(SAMPLED_TRACKS):
            submission_edit = test_client.post_note_edit(
                invitation=f'{VENUE_ID}/-/Submission',
                signatures=['~SomeFirstName_User1'],
                note=openreview.api.Note(
                    license='CC BY 4.0',
                    content={
                        'title': { 'value': f'{track} submission {index + 1}' },
                        'abstract': { 'value': f'Abstract for the {track} track' },
                        'authors': {
                            'value': [
                                {
                                    'fullname': 'SomeFirstName User',
                                    'username': '~SomeFirstName_User1',
                                    'institutions': [{ 'domain': 'mail.com', 'country': 'US' }]
                                }
                            ]
                        },
                        'track': { 'value': track },
                        'keywords': { 'value': ['web', track.lower()] },
                        'pdf': { 'value': '/pdf/' + 'p' * 40 + '.pdf' },
                        'email_sharing': { 'value': 'We authorize the sharing of all author emails with Program Chairs.' },
                        'data_release': { 'value': 'We authorize the release of our submission and author names to the public in the event of acceptance.' }
                    }
                )
            )
            helpers.await_queue_edit(openreview_client, edit_id=submission_edit['id'])

        submissions = openreview_client.get_notes(invitation=f'{VENUE_ID}/-/Submission', sort='number:asc')
        assert len(submissions) == len(SAMPLED_TRACKS)
        for submission, track in zip(submissions, SAMPLED_TRACKS):
            assert submission.content['track']['value'] == track

    def test_matching_invitations_are_track_scoped(self, openreview_client, helpers):
        """Affinity_Score, Conflict, Proposed_Assignment and
        Assignment_Configuration must only consider submissions of the role's
        own track."""

        for track in SAMPLED_TRACKS:
            for role in [f'{track}_Reviewers', f'{track}_Area_Chairs']:
                role_id = f'{VENUE_ID}/{role}'

                affinity_score_invitation = openreview_client.get_invitation(f'{role_id}/-/Affinity_Score')
                assert affinity_score_invitation.edit['head']['param']['withContent'] == { 'track': track }

                conflict_invitation = openreview_client.get_invitation(f'{role_id}/-/Conflict')
                assert conflict_invitation.edit['head']['param']['withContent'] == { 'track': track }

                proposed_assignment_invitation = openreview_client.get_invitation(f'{role_id}/-/Proposed_Assignment')
                assert proposed_assignment_invitation.edit['head']['param']['withContent'] == { 'track': track }

                assignment_configuration_invitation = openreview_client.get_invitation(f'{role_id}/-/Assignment_Configuration')
                assert assignment_configuration_invitation.edit['note']['content']['paper_invitation']['value']['param']['default'] == \
                    f'{VENUE_ID}/-/Submission&content.venueid={VENUE_ID}/Submission&content.track={track}'

        # the venue-wide roles are not restricted to any track
        for role in ['Reviewers', 'Area_Chairs']:
            affinity_score_invitation = openreview_client.get_invitation(f'{VENUE_ID}/{role}/-/Affinity_Score')
            assert 'withContent' not in affinity_score_invitation.edit['head']['param']

            assignment_configuration_invitation = openreview_client.get_invitation(f'{VENUE_ID}/{role}/-/Assignment_Configuration')
            assert assignment_configuration_invitation.edit['note']['content']['paper_invitation']['value']['param']['default'] == \
                f'{VENUE_ID}/-/Submission&content.venueid={VENUE_ID}/Submission'

    def test_deploy_assignments_per_track(self, openreview_client, helpers):
        """Deploying a track's assignments only touches submissions of that
        track. All reviewer roles share a single per-submission group, so each
        submission's Reviewers group holds only the reviewers of its own
        track."""

        submissions = openreview_client.get_notes(invitation=f'{VENUE_ID}/-/Submission', sort='number:asc')
        submissions_by_track = { s.content['track']['value']: s for s in submissions }

        for track in SAMPLED_TRACKS:
            role = f'{track}_Reviewers'
            reviewer = f'~{track}Reviewer_WebConf1'
            label = f'{track.lower()}-matching-1'

            openreview_client.post_group_edit(
                invitation=f'{VENUE_ID}/{role}/-/Members',
                signatures=[VENUE_ID],
                group=openreview.api.Group(members={ 'append': [reviewer] })
            )

            openreview_client.post_note_edit(
                invitation=f'{VENUE_ID}/{role}/-/Assignment_Configuration',
                signatures=[VENUE_ID],
                note=openreview.api.Note(
                    content={
                        'title': { 'value': label },
                        'user_demand': { 'value': '1' },
                        'max_papers': { 'value': '5' },
                        'min_papers': { 'value': '0' },
                        'alternates': { 'value': '0' },
                        'paper_invitation': { 'value': f'{VENUE_ID}/-/Submission&content.venueid={VENUE_ID}/Submission&content.track={track}' },
                        'match_group': { 'value': f'{VENUE_ID}/{role}' },
                        'aggregate_score_invitation': { 'value': f'{VENUE_ID}/{role}/-/Aggregate_Score' },
                        'conflicts_invitation': { 'value': f'{VENUE_ID}/{role}/-/Conflict' },
                        'solver': { 'value': 'FairFlow' },
                        'status': { 'value': 'Complete' }
                    }
                )
            )

            openreview_client.post_edge(openreview.api.Edge(
                invitation=f'{VENUE_ID}/{role}/-/Proposed_Assignment',
                head=submissions_by_track[track].id,
                tail=reviewer,
                signatures=[f'{VENUE_ID}/Program_Chairs'],
                weight=1,
                label=label
            ))

            venue = openreview.venue.helpers.get_venue(openreview_client, VENUE_ID, support_user='openreview.net/Support')
            venue.set_assignments(assignment_title=label, committee_id=f'{VENUE_ID}/{role}')

        # all reviewer roles share one per-submission group, and only the
        # reviewers of the submission's own track are added to it
        for track in SAMPLED_TRACKS:
            submission = submissions_by_track[track]
            group = openreview_client.get_group(f'{VENUE_ID}/Submission{submission.number}/Reviewers')
            assert group.members == [f'~{track}Reviewer_WebConf1']

            for other_track in SAMPLED_TRACKS:
                if other_track != track:
                    assert f'~{other_track}Reviewer_WebConf1' not in group.members

    def test_area_chair_console_reassignment_urls(self, openreview_client, helpers, selenium, request_page):
        """Each track's area chair console links to the edge browser of the
        reviewer role it is paired with by index, never another track's."""

        pc_client = openreview.api.OpenReviewClient(username='programchair@webconf.cc', password=helpers.strong_password)

        for track in SAMPLED_TRACKS:
            ac_role = f'{track}_Area_Chairs'

            reassignment_invitation = openreview_client.get_invitation(f'{VENUE_ID}/{ac_role}/-/Reviewer_Reassignment')
            assert reassignment_invitation.edit['content']['enable_reviewers_reassignment']['description'] == f'Would you like to allow {track} Area Chairs to reassign {track} Reviewers to submissions? Make sure there are deployed or proposed assignments created before enabling this option.'

            openreview_client.post_group_edit(
                invitation=f'{VENUE_ID}/{ac_role}/-/Members',
                signatures=[VENUE_ID],
                group=openreview.api.Group(members={ 'append': [f'~{track}AC_WebConf1'] })
            )

            ## Reviewer_Reassignment has no process function, the edit writes the
            ## group content directly
            pc_client.post_group_edit(
                invitation=f'{VENUE_ID}/{ac_role}/-/Reviewer_Reassignment',
                content={ 'enable_reviewers_reassignment': { 'value': True } }
            )

            ac_client = openreview.api.OpenReviewClient(username=f'{track.lower()}_ac@webconf.cc', password=helpers.strong_password)
            request_page(selenium, f'http://localhost:3030/group?id={VENUE_ID}/{ac_role}', ac_client, wait_for_element='header')
            header = selenium.find_element(By.ID, 'header')
            assert 'Reviewer Assignment Browser:' in header.text

            href = header.find_element(By.ID, 'edge_browser_url').get_attribute('href')
            assert f'start={VENUE_ID}/{ac_role}/-/Assignment,tail:~{track}AC_WebConf1' in href
            assert f'traverse={VENUE_ID}/{track}_Reviewers/-/Assignment' in href

            # the console never points at another track's reviewers
            for other_track in SAMPLED_TRACKS:
                if other_track != track:
                    assert f'{VENUE_ID}/{other_track}_Reviewers' not in href
