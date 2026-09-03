import pytest
import datetime
import openreview
from openreview.api import Note, Invitation, OpenReviewClient
from openreview.venue import Venue
from openreview.stages import SubmissionStage


class TestARRCommitmentWorkflow():

    def test_setup(self, openreview_client, helpers):

        assert openreview_client.get_invitation('openreview.net/Support/Venue_Request/-/ARR_Commitment_Workflow')
        assert openreview_client.get_invitation('openreview.net/Support/Venue_Request/ARR_Commitment_Workflow/-/Comment')
        assert openreview_client.get_invitation('openreview.net/Support/Venue_Request/ARR_Commitment_Workflow/-/Deployment')
        assert openreview_client.get_invitation('openreview.net/Support/Venue_Request/ARR_Commitment_Workflow/-/Status')
        assert openreview_client.get_invitation('openreview.net/Support/Venue_Request/ARR_Commitment_Workflow/-/Internal_Status')
        assert openreview_client.get_invitation('openreview.net/Support/Venue_Request/ARR_Commitment_Workflow/-/Cancel_Request')
        assert openreview_client.get_invitation('openreview.net/Support/Venue_Request/ARR_Commitment_Workflow/-/Feedback')
        assert openreview_client.get_invitation('openreview.net/Support/Venue_Request/ARR_Commitment_Workflow/-/ARR_Release')

        # conference workflow untouched
        assert openreview_client.get_invitation('openreview.net/Support/Venue_Request/-/Conference_Review_Workflow')
        assert openreview_client.get_invitation('openreview.net/Support/Venue_Request/Conference_Review_Workflow/-/Deployment')

    def test_setup_arr_venue(self, openreview_client, helpers):
        # minimal ARR-style venue: one submission with a review and a meta review
        helpers.create_user('author_one@arrtest.cc', 'ARRAuthor', 'One')

        domain = 'aclweb.org/ACL/ARR/2025/January'
        venue = Venue(openreview_client, domain, support_user='openreview.net/Support')
        venue.name = 'ACL Rolling Review 2025 January'
        venue.short_name = 'ARR Jan 2025'
        venue.website = 'https://aclrollingreview.org'
        venue.contact = 'support@aclrollingreview.org'
        venue.invitation_builder.update_wait_time = 2000
        venue.invitation_builder.update_date_string = "#{4/mdate} + 2000"

        now = datetime.datetime.now()
        venue.submission_stage = SubmissionStage(
            double_blind=True,
            due_date=now + datetime.timedelta(minutes=30),
            readers=[SubmissionStage.Readers.REVIEWERS_ASSIGNED],
            force_profiles=True,
            additional_fields={
                'paper_type': openreview.stages.arr_content.arr_submission_content['paper_type']
            }
        )
        venue.setup(program_chair_ids=['pc@aclrollingreview.org'])
        venue.create_submission_stage()

        author_client = OpenReviewClient(username='author_one@arrtest.cc', password=helpers.strong_password)
        submission = author_client.post_note_edit(
            invitation=f'{domain}/-/Submission',
            signatures=['~ARRAuthor_One1'],
            note=Note(content={
                'title': { 'value': 'ARR Paper Title' },
                'abstract': { 'value': 'This is an abstract' },
                'authors': { 'value': ['ARRAuthor One'] },
                'authorids': { 'value': ['~ARRAuthor_One1'] },
                'keywords': { 'value': ['commitment'] },
                'paper_type': { 'value': 'Long' },
                'pdf': { 'value': '/pdf/' + 'p' * 40 + '.pdf' }
            })
        )
        helpers.await_queue_edit(openreview_client, edit_id=submission['id'])

        arr_submission = openreview_client.get_note(submission['note']['id'])
        assert 'everyone' not in arr_submission.readers

        # per-submission review and meta review invitations posted directly (fixture, not the full ARR workflow)
        for stage in ['Official_Review', 'Meta_Review']:
            openreview_client.post_invitation_edit(
                invitations=f'{domain}/-/Edit',
                signatures=[domain],
                invitation=Invitation(
                    id=f'{domain}/Submission1/-/{stage}',
                    invitees=[domain],
                    readers=[domain],
                    writers=[domain],
                    signatures=[domain],
                    edit={
                        'signatures': [domain],
                        'readers': [domain],
                        'writers': [domain],
                        'note': {
                            'forum': arr_submission.id,
                            'replyto': arr_submission.id,
                            'signatures': [domain],
                            'readers': [domain],
                            'writers': [domain],
                            'content': {
                                'recommendation': {
                                    'value': { 'param': { 'type': 'string', 'maxLength': 500 } }
                                }
                            }
                        }
                    }
                )
            )
            openreview_client.post_note_edit(
                invitation=f'{domain}/Submission1/-/{stage}',
                signatures=[domain],
                note=Note(content={ 'recommendation': { 'value': f'{stage} content' } })
            )

    def test_post_request_with_acs(self, openreview_client, helpers):

        helpers.create_user('commitment_pc@abcd.cc', 'CommitmentPC', 'ABCD')
        pc_client = OpenReviewClient(username='commitment_pc@abcd.cc', password=helpers.strong_password)

        now = datetime.datetime.now()
        start_date = now - datetime.timedelta(days=1)
        due_date = now + datetime.timedelta(days=2)

        request = pc_client.post_note_edit(invitation='openreview.net/Support/Venue_Request/-/ARR_Commitment_Workflow',
            signatures=['~CommitmentPC_ABCD1'],
            note=Note(
                content={
                    'official_venue_name': { 'value': 'The ABCD Commitment Venue' },
                    'abbreviated_venue_name': { 'value': 'ABCD Commitment 2026' },
                    'venue_website_url': { 'value': 'https://abcd.cc/2026' },
                    'location': { 'value': 'Virtual' },
                    'venue_start_date': { 'value': openreview.tools.datetime_millis(now + datetime.timedelta(weeks=10)) },
                    'program_chair_emails': { 'value': ['commitment_pc@abcd.cc'] },
                    'contact_email': { 'value': 'commitment_pc@abcd.cc' },
                    'submission_start_date': { 'value': openreview.tools.datetime_millis(start_date) },
                    'submission_deadline': { 'value': openreview.tools.datetime_millis(due_date) },
                    'area_chairs_support': { 'value': True },
                    'expected_submissions': { 'value': 100 },
                    'venue_organizer_agreement': { 'value': [
                        'OpenReview natively supports a wide variety of reviewing workflow configurations. However, if we want significant reviewing process customizations or experiments, we will detail these requests to the OpenReview staff at least three months in advance.',
                        'We will ask authors and reviewers to create an OpenReview Profile at least two weeks in advance of the paper submission deadlines.',
                        'When assembling our group of reviewers, we will only include email addresses or OpenReview Profile IDs of people we know to have authored publications relevant to our venue.  (We will not solicit new reviewers using an open web form, because unfortunately some malicious actors sometimes try to create "fake ids" aiming to be assigned to review their own paper submissions.)',
                        'We acknowledge that, if our venue\'s reviewing workflow is non-standard, or if our venue is expecting more than a few hundred submissions for any one deadline, we should designate our own Workflow Chair, who will read the OpenReview documentation and manage our workflow configurations throughout the reviewing process.',
                        'We acknowledge that OpenReview staff work Monday-Friday during standard business hours US Eastern time, and we cannot expect support responses outside those times.  For this reason, we recommend setting submission and reviewing deadlines Monday through Thursday.',
                        'We will treat the OpenReview staff with kindness and consideration.',
                        'We acknowledge that authors and reviewers will be required to share their preferred email.'
                    ]}
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=request['id'])

        request_note = openreview_client.get_note(request['note']['id'])
        assert openreview_client.get_invitation(f'openreview.net/Support/Venue_Request/ARR_Commitment_Workflow{request_note.number}/-/Comment')

        messages = openreview_client.get_messages(to='commitment_pc@abcd.cc', subject='Your request for OpenReview service has been received.')
        assert len(messages) == 1

    def test_deploy(self, openreview_client, helpers):

        request = openreview_client.get_notes(invitation='openreview.net/Support/Venue_Request/-/ARR_Commitment_Workflow', sort='number:asc')[0]

        edit = openreview_client.post_note_edit(
            invitation='openreview.net/Support/Venue_Request/ARR_Commitment_Workflow/-/Deployment',
            signatures=['openreview.net/Support'],
            note=Note(
                id=request.id,
                content={ 'venue_id': { 'value': 'ABCD.cc/2026/Commitment' } }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        venue_id = 'ABCD.cc/2026/Commitment'
        venue_group = openreview_client.get_group(venue_id)
        assert venue_group
        assert venue_group.content['commitments_venue']['value'] == True

        # committee: PCs + ACs + Authors, no Reviewers
        assert openreview_client.get_group(f'{venue_id}/Program_Chairs')
        assert openreview_client.get_group(f'{venue_id}/Area_Chairs')
        assert openreview_client.get_group(f'{venue_id}/Authors')
        assert openreview.tools.get_group(openreview_client, f'{venue_id}/Reviewers') is None

        # submission form has paper_link accepting a url or a note id, and paper_type
        submission_invitation = openreview_client.get_invitation(f'{venue_id}/-/Submission')
        assert 'paper_link' in submission_invitation.edit['note']['content']
        assert 'paper_type' in submission_invitation.edit['note']['content']
        assert submission_invitation.edit['note']['content']['paper_type']['value']['param']['enum'] == openreview.stages.arr_content.arr_submission_content['paper_type']['value']['param']['enum']
        assert submission_invitation.signatures == ['~Super_User1']

        # excluded stages do not exist
        assert openreview.tools.get_invitation(openreview_client, f'{venue_id}/-/Official_Review') is None
        assert openreview.tools.get_invitation(openreview_client, f'{venue_id}/-/Official_Comment') is None
        assert openreview.tools.get_invitation(openreview_client, f'{venue_id}/-/Author_Rebuttal') is None
        assert openreview.tools.get_invitation(openreview_client, f'{venue_id}/Reviewers/-/Bid') is None
        assert openreview.tools.get_invitation(openreview_client, f'{venue_id}/Area_Chairs/-/Bid') is None
        assert openreview.tools.get_invitation(openreview_client, f'{venue_id}/Reviewers/-/Submission_Group') is None

        # no reviewer role participation tag invitation and no reviewer stats
        assert openreview.tools.get_invitation(openreview_client, f'{venue_id}/-/Reviewer') is None
        assert openreview.tools.get_invitation(openreview_client, f'{venue_id}/Reviewers/-/Review_Count') is None

        # included stages exist
        assert openreview_client.get_invitation(f'{venue_id}/-/Meta_Review')
        assert openreview_client.get_invitation(f'{venue_id}/-/Decision')
        assert openreview_client.get_invitation(f'{venue_id}/-/Decision_Upload')
        assert openreview_client.get_invitation(f'{venue_id}/-/Decision_Release')
        assert openreview_client.get_invitation(f'{venue_id}/-/Submission_Change_After_Deadline')
        assert openreview_client.get_invitation(f'{venue_id}/Area_Chairs/-/Assignment')
        assert openreview_client.get_invitation(f'{venue_id}/Area_Chairs/-/Submission_Group')

        # the manual ARR release step is available to the support team on the request form
        release_invitation = openreview_client.get_invitation('openreview.net/Support/Venue_Request/ARR_Commitment_Workflow/-/ARR_Release')
        assert release_invitation.invitees == ['openreview.net/Support']

    def test_submit_commitments(self, openreview_client, helpers):

        venue_id = 'ABCD.cc/2026/Commitment'
        author_client = OpenReviewClient(username='author_one@arrtest.cc', password=helpers.strong_password)
        arr_submission = openreview_client.get_notes(invitation='aclweb.org/ACL/ARR/2025/January/-/Submission')[0]

        def post_commitment(paper_link, paper_type='Long'):
            return author_client.post_note_edit(
                invitation=f'{venue_id}/-/Submission',
                signatures=['~ARRAuthor_One1'],
                note=Note(
                    license='CC BY 4.0',
                    content={
                    'title': { 'value': 'Commitment Paper' },
                    'abstract': { 'value': 'Committing our ARR paper' },
                    'authors': {
                        'value': [
                            {
                                'fullname': 'ARRAuthor One',
                                'username': '~ARRAuthor_One1',
                                'institutions': [{ 'domain': 'arrtest.cc', 'country': 'US' }]
                            }
                        ]
                    },
                    'keywords': { 'value': ['commitment'] },
                    'pdf': { 'value': '/pdf/' + 'p' * 40 + '.pdf' },
                    'paper_link': { 'value': paper_link },
                    'paper_type': { 'value': paper_type },
                    'email_sharing': { 'value': 'We authorize the sharing of all author emails with Program Chairs.' },
                    'data_release': { 'value': 'We authorize the release of our submission and author names to the public in the event of acceptance.' }
                })
            )

        # invalid: extra parameters after the id are rejected by the field regex
        with pytest.raises(openreview.OpenReviewException):
            post_commitment(f'https://openreview.net/forum?id={arr_submission.id}&replyto=4567')

        # invalid: id that does not exist
        with pytest.raises(openreview.OpenReviewException, match=r'.*does not correspond to a submission in OpenReview.*'):
            post_commitment('nonExistentNoteId123')

        # invalid: paper type does not match the ARR submission paper type
        with pytest.raises(openreview.OpenReviewException, match=r'.*does not match the paper type of the ARR submission.*'):
            post_commitment(f'https://openreview.net/forum?id={arr_submission.id}', paper_type='Short')

        # valid: full URL
        edit = post_commitment(f'https://openreview.net/forum?id={arr_submission.id}')
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        # valid: bare note id
        edit = post_commitment(arr_submission.id)
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        assert len(openreview_client.get_notes(invitation=f'{venue_id}/-/Submission')) == 2

    def test_arr_release(self, openreview_client, helpers):

        venue_id = 'ABCD.cc/2026/Commitment'
        arr_domain = 'aclweb.org/ACL/ARR/2025/January'

        request = openreview_client.get_notes(invitation='openreview.net/Support/Venue_Request/-/ARR_Commitment_Workflow', sort='number:asc')[0]

        # create the per-submission Area_Chairs groups first, as in production:
        # the Submission_Group step activates at the submission expiration date,
        # before the ARR release runs
        now_ms = openreview.tools.datetime_millis(datetime.datetime.now())
        openreview_client.post_invitation_edit(
            invitations=f'{venue_id}/-/Edit',
            signatures=[venue_id],
            invitation=Invitation(id=f'{venue_id}/Area_Chairs/-/Submission_Group', cdate=now_ms, signatures=[venue_id])
        )
        helpers.await_queue_edit(openreview_client, edit_id=f'{venue_id}/Area_Chairs/-/Submission_Group-0-1', count=2)
        assert openreview_client.get_group(f'{venue_id}/Submission1/Area_Chairs')
        assert openreview_client.get_group(f'{venue_id}/Submission2/Area_Chairs')

        # the support team runs the release step manually from the request form,
        # confirming which replies to release and which committee roles get access
        edit = openreview_client.post_note_edit(
            invitation='openreview.net/Support/Venue_Request/ARR_Commitment_Workflow/-/ARR_Release',
            signatures=['openreview.net/Support'],
            note=Note(
                id=request.id,
                content={
                    'arr_reply_invitation_names': { 'value': ['Official_Review', 'Meta_Review'] },
                    'arr_additional_readers': { 'value': ['Area_Chairs'] }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        readers_group = openreview_client.get_group(f'{arr_domain}/Submission1/Commitment_Readers')
        assert venue_id in readers_group.members
        assert f'{venue_id}/Submission1/Area_Chairs' in readers_group.members
        assert f'{venue_id}/Submission2/Area_Chairs' in readers_group.members

        arr_submission = openreview_client.get_notes(invitation=f'{arr_domain}/-/Submission')[0]
        assert f'{arr_domain}/Submission1/Commitment_Readers' in arr_submission.readers

        replies = openreview_client.get_notes(forum=arr_submission.id)
        review_replies = [r for r in replies if 'Official_Review' in r.invitations[0] or 'Meta_Review' in r.invitations[0]]
        assert len(review_replies) == 2
        for reply in review_replies:
            assert f'{arr_domain}/Submission1/Commitment_Readers' in reply.readers

        # a confirmation comment is posted to the request form
        comments = openreview_client.get_notes(invitation=f'openreview.net/Support/Venue_Request/ARR_Commitment_Workflow{request.number}/-/Comment')
        assert any(c.content.get('title', {}).get('value') == 'ARR submissions released' for c in comments)

        # the request form records the release parameters
        request = openreview_client.get_note(request.id)
        assert request.content['arr_reply_invitation_names']['value'] == ['Official_Review', 'Meta_Review']
        assert request.content['arr_additional_readers']['value'] == ['Area_Chairs']

    def test_meta_review_and_decision(self, openreview_client, helpers):

        venue_id = 'ABCD.cc/2026/Commitment'
        helpers.create_user('ac_one@abcd.cc', 'ACOne', 'ABCD')

        # activate the post-deadline steps
        # (the Area_Chairs Submission_Group step was already activated in test_arr_release)
        now_ms = openreview.tools.datetime_millis(datetime.datetime.now())
        due_ms = openreview.tools.datetime_millis(datetime.datetime.now() + datetime.timedelta(days=1))

        openreview_client.post_invitation_edit(
            invitations=f'{venue_id}/-/Edit',
            signatures=[venue_id],
            invitation=Invitation(id=f'{venue_id}/-/Submission_Change_After_Deadline', cdate=now_ms, signatures=[venue_id])
        )
        helpers.await_queue_edit(openreview_client, edit_id=f'{venue_id}/-/Submission_Change_After_Deadline-0-1', count=2)

        # meta review and decision stages are activated through their Dates edit invitations,
        # which update the child invitation cdate the date process reads
        pc_client = OpenReviewClient(username='commitment_pc@abcd.cc', password=helpers.strong_password)
        for stage_name in ['Meta_Review', 'Decision']:
            pc_client.post_invitation_edit(
                invitations=f'{venue_id}/-/{stage_name}/Dates',
                content={
                    'activation_date': { 'value': now_ms },
                    'due_date': { 'value': due_ms },
                    'expiration_date': { 'value': due_ms }
                }
            )
            helpers.await_queue_edit(openreview_client, edit_id=f'{venue_id}/-/{stage_name}-0-1', count=2)

        assert openreview_client.get_invitation(f'{venue_id}/Submission1/-/Meta_Review')
        assert openreview_client.get_invitation(f'{venue_id}/Submission1/-/Decision')

        # assign the AC to submission 1 and post a meta review
        openreview_client.add_members_to_group(f'{venue_id}/Area_Chairs', '~ACOne_ABCD1')
        openreview_client.add_members_to_group(f'{venue_id}/Submission1/Area_Chairs', '~ACOne_ABCD1')

        ac_client = OpenReviewClient(username='ac_one@abcd.cc', password=helpers.strong_password)
        ac_anon_groups = ac_client.get_groups(prefix=f'{venue_id}/Submission1/Area_Chair_', signatory='~ACOne_ABCD1')
        assert ac_anon_groups

        meta_review = ac_client.post_note_edit(
            invitation=f'{venue_id}/Submission1/-/Meta_Review',
            signatures=[ac_anon_groups[0].id],
            note=Note(content={
                'metareview': { 'value': 'Good paper, accept.' },
                'recommendation': { 'value': 'Accept (Oral)' },
                'confidence': { 'value': 5 }
            })
        )
        helpers.await_queue_edit(openreview_client, edit_id=meta_review['id'])

        pc_client = OpenReviewClient(username='commitment_pc@abcd.cc', password=helpers.strong_password)
        decision = pc_client.post_note_edit(
            invitation=f'{venue_id}/Submission1/-/Decision',
            signatures=[f'{venue_id}/Program_Chairs'],
            note=Note(content={
                'decision': { 'value': 'Accept' },
                'comment': { 'value': 'Congratulations' }
            })
        )
        helpers.await_queue_edit(openreview_client, edit_id=decision['id'])

    def test_request_without_acs(self, openreview_client, helpers):

        helpers.create_user('commitment_pc2@efgh.cc', 'CommitmentPCTwo', 'EFGH')
        pc_client = OpenReviewClient(username='commitment_pc2@efgh.cc', password=helpers.strong_password)

        now = datetime.datetime.now()
        request = pc_client.post_note_edit(invitation='openreview.net/Support/Venue_Request/-/ARR_Commitment_Workflow',
            signatures=['~CommitmentPCTwo_EFGH1'],
            note=Note(
                content={
                    'official_venue_name': { 'value': 'The EFGH Commitment Venue' },
                    'abbreviated_venue_name': { 'value': 'EFGH Commitment 2026' },
                    'venue_website_url': { 'value': 'https://efgh.cc/2026' },
                    'location': { 'value': 'Virtual' },
                    'venue_start_date': { 'value': openreview.tools.datetime_millis(now + datetime.timedelta(weeks=10)) },
                    'program_chair_emails': { 'value': ['commitment_pc2@efgh.cc'] },
                    'contact_email': { 'value': 'commitment_pc2@efgh.cc' },
                    'submission_start_date': { 'value': openreview.tools.datetime_millis(now - datetime.timedelta(days=1)) },
                    'submission_deadline': { 'value': openreview.tools.datetime_millis(now + datetime.timedelta(days=2)) },
                    'expected_submissions': { 'value': 50 },
                    'venue_organizer_agreement': { 'value': [
                        'OpenReview natively supports a wide variety of reviewing workflow configurations. However, if we want significant reviewing process customizations or experiments, we will detail these requests to the OpenReview staff at least three months in advance.',
                        'We will ask authors and reviewers to create an OpenReview Profile at least two weeks in advance of the paper submission deadlines.',
                        'When assembling our group of reviewers, we will only include email addresses or OpenReview Profile IDs of people we know to have authored publications relevant to our venue.  (We will not solicit new reviewers using an open web form, because unfortunately some malicious actors sometimes try to create "fake ids" aiming to be assigned to review their own paper submissions.)',
                        'We acknowledge that, if our venue\'s reviewing workflow is non-standard, or if our venue is expecting more than a few hundred submissions for any one deadline, we should designate our own Workflow Chair, who will read the OpenReview documentation and manage our workflow configurations throughout the reviewing process.',
                        'We acknowledge that OpenReview staff work Monday-Friday during standard business hours US Eastern time, and we cannot expect support responses outside those times.  For this reason, we recommend setting submission and reviewing deadlines Monday through Thursday.',
                        'We will treat the OpenReview staff with kindness and consideration.',
                        'We acknowledge that authors and reviewers will be required to share their preferred email.'
                    ]}
                }
            ))
        helpers.await_queue_edit(openreview_client, edit_id=request['id'])

        edit = openreview_client.post_note_edit(
            invitation='openreview.net/Support/Venue_Request/ARR_Commitment_Workflow/-/Deployment',
            signatures=['openreview.net/Support'],
            note=Note(
                id=request['note']['id'],
                content={ 'venue_id': { 'value': 'EFGH.cc/2026/Commitment' } }
            ))
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        venue_id = 'EFGH.cc/2026/Commitment'
        assert openreview_client.get_group(f'{venue_id}/Program_Chairs')
        assert openreview.tools.get_group(openreview_client, f'{venue_id}/Area_Chairs') is None
        assert openreview.tools.get_group(openreview_client, f'{venue_id}/Reviewers') is None
        assert openreview.tools.get_invitation(openreview_client, f'{venue_id}/-/Meta_Review') is None
        assert openreview.tools.get_invitation(openreview_client, f'{venue_id}/Area_Chairs/-/Assignment') is None
        assert openreview_client.get_invitation(f'{venue_id}/-/Decision')
        assert openreview_client.get_invitation(f'{venue_id}/-/Decision_Release')
        assert 'paper_link' in openreview_client.get_invitation(f'{venue_id}/-/Submission').edit['note']['content']
        assert 'paper_type' in openreview_client.get_invitation(f'{venue_id}/-/Submission').edit['note']['content']
