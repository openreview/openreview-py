import datetime
import openreview

class TestPublicationChairs():

    def test_setup(self, openreview_client, helpers):

        super_id = 'openreview.net'
        support_group_id = super_id + '/Support'
        venue_id = 'PUBC.cc/2026/Conference'

        helpers.create_user('programchair@pubc.cc', 'ProgramChair', 'PUBC')
        helpers.create_user('publicationchair@pubc.cc', 'PublicationChair', 'PUBC')
        pc_client = openreview.api.OpenReviewClient(username='programchair@pubc.cc', password=helpers.strong_password)

        now = datetime.datetime.now()
        due_date = now + datetime.timedelta(days=2)

        request = pc_client.post_note_edit(invitation=f'{support_group_id}/Venue_Request/-/Conference_Review_Workflow',
            signatures=['~ProgramChair_PUBC1'],
            note=openreview.api.Note(
                content={
                    'official_venue_name': { 'value': 'The Publication Chairs Conference' },
                    'abbreviated_venue_name': { 'value': 'PUBC 2026' },
                    'venue_website_url': { 'value': 'https://pubc.cc/Conferences/2026' },
                    'location': { 'value': 'Amherst, Massachusetts' },
                    'venue_start_date': { 'value': openreview.tools.datetime_millis(now + datetime.timedelta(weeks=52)) },
                    'program_chair_emails': { 'value': ['programchair@pubc.cc'] },
                    'contact_email': { 'value': 'pubc2026.programchairs@gmail.com' },
                    'submission_start_date': { 'value': openreview.tools.datetime_millis(now - datetime.timedelta(days=1)) },
                    'submission_deadline': { 'value': openreview.tools.datetime_millis(due_date) },
                    'publication_chairs_support': { 'value': True },
                    'publication_chairs_emails': { 'value': ['publicationchair@pubc.cc'] },
                    'expected_submissions': { 'value': 20 },
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

        # deploy the venue
        edit = openreview_client.post_note_edit(invitation=f'{support_group_id}/Venue_Request/Conference_Review_Workflow/-/Deployment',
            signatures=[support_group_id],
            note=openreview.api.Note(
                id=request['note']['id'],
                content={
                    'venue_id': { 'value': venue_id }
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        # the publication chairs group is created with the emails from the request form
        publication_chairs_group = openreview_client.get_group(f'{venue_id}/Publication_Chairs')
        assert publication_chairs_group.members == ['publicationchair@pubc.cc']
        assert publication_chairs_group.domain == venue_id

        # the domain exposes the publication chairs group so later processes know the venue has them
        domain_group = openreview_client.get_group(venue_id)
        assert domain_group.content['publication_chairs_id']['value'] == f'{venue_id}/Publication_Chairs'
        assert f'{venue_id}/Publication_Chairs' in domain_group.content['preferred_emails_groups']['value']

        # publication chairs can read the preferred emails of the committee
        preferred_emails_readers_group = openreview_client.get_group(f'{venue_id}/Preferred_Emails_Readers')
        assert f'{venue_id}/Publication_Chairs' in preferred_emails_readers_group.members

        # publication chairs can read and write the accepted authors group in order to contact them
        authors_accepted_group = openreview_client.get_group(f'{venue_id}/Authors/Accepted')
        assert authors_accepted_group.readers == [venue_id, f'{venue_id}/Publication_Chairs']
        assert authors_accepted_group.writers == [venue_id, f'{venue_id}/Publication_Chairs']

        # role participation is released by default, so the publication chairs get a role invitation
        assert openreview_client.get_invitation(f'{venue_id}/-/Publication_Chair')

        # the publication chairs fields are hidden from the PCs once the venue is deployed
        request_note = openreview_client.get_note(request['note']['id'])
        assert request_note.content['publication_chairs_support']['readers'] == [support_group_id]
        assert request_note.content['publication_chairs_emails']['readers'] == [support_group_id]
