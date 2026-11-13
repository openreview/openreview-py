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

        # the PCs can manage the publication chairs group from the workflow timeline
        assert openreview_client.get_invitation(f'{venue_id}/Publication_Chairs/-/Members')
        assert openreview_client.get_invitation(f'{venue_id}/Publication_Chairs/-/Homepage')
        assert openreview_client.get_invitation(f'{venue_id}/Publication_Chairs/-/Message')
        # the message invitation is hidden from the workflow timeline like the other committee message invitations
        assert f'{venue_id}/Publication_Chairs/-/Message' in domain_group.content['exclusion_workflow_invitations']['value']

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

    def test_add_and_remove_publication_chairs(self, openreview_client, helpers):

        venue_id = 'PUBC.cc/2026/Conference'
        pc_client = openreview.api.OpenReviewClient(username='programchair@pubc.cc', password=helpers.strong_password)

        # add a publication chair
        pc_client.post_group_edit(
            invitation=f'{venue_id}/Publication_Chairs/-/Members',
            signatures=[venue_id],
            group=openreview.api.Group(
                members={
                    'append': ['new_publicationchair@pubc.cc']
                }
            )
        )

        publication_chairs_group = openreview_client.get_group(f'{venue_id}/Publication_Chairs')
        assert publication_chairs_group.members == ['publicationchair@pubc.cc', 'new_publicationchair@pubc.cc']

        # remove the publication chair that was just added
        pc_client.post_group_edit(
            invitation=f'{venue_id}/Publication_Chairs/-/Members',
            signatures=[venue_id],
            group=openreview.api.Group(
                members={
                    'remove': ['new_publicationchair@pubc.cc']
                }
            )
        )

        publication_chairs_group = openreview_client.get_group(f'{venue_id}/Publication_Chairs')
        assert publication_chairs_group.members == ['publicationchair@pubc.cc']

    def test_publication_chairs_message_accepted_authors(self, openreview_client, helpers):

        venue_id = 'PUBC.cc/2026/Conference'
        authors_accepted_id = f'{venue_id}/Authors/Accepted'

        # only the accepted authors message invitation lets the publication chairs message its members
        invitation = openreview_client.get_invitation(f'{authors_accepted_id}/-/Message')
        assert invitation.invitees == [venue_id, f'{venue_id}/Publication_Chairs']
        assert invitation.readers == [venue_id, f'{venue_id}/Publication_Chairs']
        assert invitation.message['signature'] == { 'param': { 'enum': [venue_id, f'{venue_id}/Publication_Chairs'] } }

        invitation = openreview_client.get_invitation(f'{venue_id}/Authors/-/Message')
        assert invitation.invitees == [venue_id]
        assert invitation.readers == [venue_id]
        assert invitation.message['signature'] == venue_id

        # the accepted authors group is filled by the decision process, add an author directly to have someone to message
        helpers.create_user('author@pubc.cc', 'Author', 'PUBC')
        openreview_client.add_members_to_group(authors_accepted_id, ['~Author_PUBC1'])

        publication_chair_client = openreview.api.OpenReviewClient(username='publicationchair@pubc.cc', password=helpers.strong_password)
        publication_chair_client.post_message(
            subject='[PUBC 2026] Camera ready instructions',
            recipients=['~Author_PUBC1'],
            message='Please submit your camera ready version.',
            invitation=f'{authors_accepted_id}/-/Message',
            signature=f'{venue_id}/Publication_Chairs',
            parentGroup=authors_accepted_id
        )

        messages = openreview_client.get_messages(to='author@pubc.cc', subject='[PUBC 2026] Camera ready instructions')
        assert len(messages) == 1
        assert messages[0]['content']['text'].startswith('Please submit your camera ready version.')

    def test_publication_chairs_submission_readers_option(self, openreview_client, helpers):

        venue_id = 'PUBC.cc/2026/Conference'

        # the /Readers invitations are created by the release template processes, wait for both of them
        helpers.await_queue_edit(openreview_client, invitation='openreview.net/Template/-/Accept_Submission_Release')
        helpers.await_queue_edit(openreview_client, invitation='openreview.net/Template/-/Reject_Submission_Release')

        # the PCs can make accepted submissions readable by the publication chairs, as the legacy Post Decision stage did
        readers_invitation = openreview_client.get_invitation(f'{venue_id}/-/Accept_Submission_Change_After_Decision/Readers')
        readers_items = readers_invitation.edit['content']['readers']['value']['param']['items']
        assert { 'value': f'{venue_id}/Publication_Chairs', 'optional': True, 'description': 'Publication Chairs' } in readers_items
        # the option sits between the committee options and the submission authors
        descriptions = [item['description'] for item in readers_items]
        assert descriptions.index('Publication Chairs') == descriptions.index('Submission Authors') - 1

        # publication chairs only work with accepted submissions, so rejected submissions don't offer the option
        readers_invitation = openreview_client.get_invitation(f'{venue_id}/-/Reject_Submission_Change_After_Decision/Readers')
        readers_items = readers_invitation.edit['content']['readers']['value']['param']['items']
        assert f'{venue_id}/Publication_Chairs' not in [item['value'] for item in readers_items]

        # the PCs keep accepted submissions private to the program chairs, publication chairs and authors
        pc_client = openreview.api.OpenReviewClient(username='programchair@pubc.cc', password=helpers.strong_password)
        submission_authors_id = f'{venue_id}/Submission' + '${{2/id}/number}' + '/Authors'
        # the /Readers edit has only a preprocess, so the release invitation is updated as soon as the edit is posted
        pc_client.post_invitation_edit(
            invitations=f'{venue_id}/-/Accept_Submission_Change_After_Decision/Readers',
            content={
                'readers': {
                    'value': [venue_id, f'{venue_id}/Publication_Chairs', submission_authors_id]
                }
            }
        )

        # the selected readers are copied as they are, the submission number is filled in when the release runs on each note
        release_invitation = openreview_client.get_invitation(f'{venue_id}/-/Accept_Submission_Change_After_Decision')
        assert release_invitation.edit['note']['readers'] == [venue_id, f'{venue_id}/Publication_Chairs', submission_authors_id]
