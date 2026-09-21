import datetime
import openreview


class TestRedeployAddAreaChairs():
    """Regression test for redeploying a template-workflow venue after its configuration
    changes.

    A venue is first deployed as reviewers-only, then redeployed after the program chairs
    enable area chairs on the same venue request. The venue group's content must be updated
    to reflect the new area chair configuration on redeploy -- it must not be left stuck with
    only the reviewers-only content from the first deployment.
    """

    def test_redeploy_adds_area_chairs_to_group_content(self, openreview_client, helpers):
        super_id = 'openreview.net'
        support_group_id = super_id + '/Support'
        deployment_invitation_id = f'{support_group_id}/Venue_Request/Conference_Review_Workflow/-/Deployment'
        venue_id = 'QRST.cc/2026/Conference'

        helpers.create_user('programchair@qrst.cc', 'ProgramChair', 'QRST')
        pc_client = openreview.api.OpenReviewClient(username='programchair@qrst.cc', password=helpers.strong_password)

        now = datetime.datetime.now()
        due_date = now + datetime.timedelta(days=2)

        # Step 1: submit a venue request configured with reviewers only (no area chairs)
        request = pc_client.post_note_edit(invitation=f'{support_group_id}/Venue_Request/-/Conference_Review_Workflow',
            signatures=['~ProgramChair_QRST1'],
            note=openreview.api.Note(
                content={
                    'official_venue_name': { 'value': 'The QRST Conference' },
                    'abbreviated_venue_name': { 'value': 'QRST 2026' },
                    'venue_website_url': { 'value': 'https://qrst.cc/Conferences/2026' },
                    'location': { 'value': 'Boston, Massachusetts' },
                    'venue_start_date': { 'value': openreview.tools.datetime_millis(now + datetime.timedelta(weeks=52)) },
                    'program_chair_emails': { 'value': ['programchair@qrst.cc'] },
                    'contact_email': { 'value': 'qrst2026.programchairs@gmail.com' },
                    'submission_start_date': { 'value': openreview.tools.datetime_millis(now) },
                    'submission_deadline': { 'value': openreview.tools.datetime_millis(due_date) },
                    'reviewer_groups_names': { 'value': ['Program_Committee'] },
                    'colocated': { 'value': 'Independent' },
                    'previous_venue': { 'value': 'QRST.cc/2024/Conference' },
                    'expected_submissions': { 'value': 100 },
                    'how_did_you_hear_about_us': { 'value': 'We have used OpenReview for our previous conferences.' },
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
            ))

        helpers.await_queue_edit(openreview_client, edit_id=request['id'])

        request = openreview_client.get_note(request['note']['id'])

        # Step 2: deploy the venue with reviewers only
        edit = openreview_client.post_note_edit(invitation=deployment_invitation_id,
            signatures=[support_group_id],
            note=openreview.api.Note(
                id=request.id,
                content={
                    'venue_id': { 'value': venue_id }
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        venue_group = openreview.tools.get_group(openreview_client, venue_id)
        assert venue_group
        assert venue_group.content['reviewers_id']['value'] == f'{venue_id}/Program_Committee'
        # sanity check: no area chair configuration exists yet
        assert 'area_chairs_id' not in venue_group.content
        assert 'area_chairs_name' not in venue_group.content
        assert venue_group.content['preferred_emails_groups']['value'] == [f'{venue_id}/Program_Committee', f'{venue_id}/Authors']

        content_before_redeploy = venue_group.content

        # Step 3: the super user edits the request form itself to enable area chairs.
        request_form_edit = openreview_client.post_note_edit(
            invitation=f'{support_group_id}/Venue_Request/-/Conference_Review_Workflow',
            signatures=['~Super_User1'],
            note=openreview.api.Note(
                id=request.id,
                content={
                    'official_venue_name': { 'value': 'The QRST Conference' },
                    'abbreviated_venue_name': { 'value': 'QRST 2026' },
                    'venue_website_url': { 'value': 'https://qrst.cc/Conferences/2026' },
                    'location': { 'value': 'Boston, Massachusetts' },
                    'venue_start_date': { 'value': openreview.tools.datetime_millis(now + datetime.timedelta(weeks=52)) },
                    'program_chair_emails': { 'value': ['programchair@qrst.cc'] },
                    'contact_email': { 'value': 'qrst2026.programchairs@gmail.com' },
                    'submission_start_date': { 'value': openreview.tools.datetime_millis(now) },
                    'submission_deadline': { 'value': openreview.tools.datetime_millis(due_date) },
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
                    },
                    'area_chairs_support': { 'value': True },
                    'area_chair_groups_names': { 'value': ['Area_Chairs'] }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=request_form_edit['id'])

        # Step 4: redeploy the SAME venue -- the Deployment invitation only needs venue_id and redeployment flag
        redeploy_edit = openreview_client.post_note_edit(invitation=deployment_invitation_id,
            signatures=[support_group_id],
            note=openreview.api.Note(
                id=request.id,
                content={
                    'venue_id': { 'value': venue_id },
                    'redeployment': { 'value': True }
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=redeploy_edit['id'])

        venue_group = openreview.tools.get_group(openreview_client, venue_id)

        # The redeploy must actually overwrite/extend the group content: area chair
        # configuration should now be present, and the reviewers configuration from the
        # first deployment should be unaffected.
        assert venue_group.content != content_before_redeploy
        assert venue_group.content['area_chairs_id']['value'] == f'{venue_id}/Area_Chairs'
        assert venue_group.content['area_chairs_name']['value'] == 'Area_Chairs'
        assert venue_group.content['reviewers_id']['value'] == f'{venue_id}/Program_Committee'

        # preferred_emails_groups already existed after the first deployment, so this covers
        # the case of an existing key whose value changes, not just newly added keys
        assert venue_group.content['preferred_emails_groups']['value'] == [f'{venue_id}/Program_Committee', f'{venue_id}/Authors', f'{venue_id}/Area_Chairs']

        area_chairs_group = openreview.tools.get_group(openreview_client, f'{venue_id}/Area_Chairs')
        assert area_chairs_group