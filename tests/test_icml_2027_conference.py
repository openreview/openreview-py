import pytest
import datetime
import openreview
from openreview.api import Payment

class TestICML2027Conference():

    venue_id = 'ICML.cc/2027/Conference'

    def test_setup(self, openreview_client, helpers):

        venue_id = self.venue_id
        support_group_id = 'openreview.net/Support'

        helpers.create_user('programchair@icml2027.cc', 'ProgramChair', 'ICMLTwentySeven')
        pc_client = openreview.api.OpenReviewClient(username='programchair@icml2027.cc', password=helpers.strong_password)

        now = datetime.datetime.now()
        abstract_due_date = now + datetime.timedelta(days=2)
        full_submission_due_date = abstract_due_date + datetime.timedelta(days=4)

        request = pc_client.post_note_edit(invitation='openreview.net/Support/Venue_Request/-/Conference_Review_Workflow',
            signatures=['~ProgramChair_ICMLTwentySeven1'],
            note=openreview.api.Note(
                content={
                    'official_venue_name': { 'value': 'Forty-Fourth International Conference on Machine Learning' },
                    'abbreviated_venue_name': { 'value': 'ICML 2027' },
                    'venue_website_url': { 'value': 'https://icml.cc/Conferences/2027' },
                    'location': { 'value': 'Seoul, South Korea' },
                    'venue_start_date': { 'value': openreview.tools.datetime_millis(now + datetime.timedelta(weeks=52)) },
                    'program_chair_emails': { 'value': ['programchair@icml2027.cc'] },
                    'contact_email': { 'value': 'icml2027.programchairs@gmail.com' },
                    'submission_start_date': { 'value': openreview.tools.datetime_millis(now - datetime.timedelta(days=1)) },
                    'submission_deadline': { 'value': openreview.tools.datetime_millis(abstract_due_date) },
                    'full_submission_deadline': { 'value': openreview.tools.datetime_millis(full_submission_due_date) },
                    'expected_submissions': { 'value': 10000 },
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

        edit = openreview_client.post_note_edit(invitation='openreview.net/Support/Venue_Request/Conference_Review_Workflow/-/Deployment',
            signatures=[support_group_id],
            note=openreview.api.Note(
                id=request['note']['id'],
                content={
                    'venue_id': { 'value': venue_id }
                }
            ))

        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])
        helpers.await_queue_edit(openreview_client, f'{venue_id}/-/Withdrawal-0-1', count=1)
        helpers.await_queue_edit(openreview_client, f'{venue_id}/-/Desk_Rejection-0-1', count=1)
        helpers.await_queue_edit(openreview_client, f'{venue_id}/-/Full_Submission-0-1', count=1)

        submission_invitation = openreview_client.get_invitation(f'{venue_id}/-/Submission')
        assert submission_invitation.duedate == openreview.tools.datetime_millis(abstract_due_date)

        full_submission_invitation = openreview_client.get_invitation(f'{venue_id}/-/Full_Submission')
        assert full_submission_invitation.edit['invitation']['duedate'] == openreview.tools.datetime_millis(full_submission_due_date)

        ## the submission fee steps are enabled by support, they are not part of the deployment
        assert openreview.tools.get_invitation(openreview_client, f'{venue_id}/-/Submission_Fee_Payment') is None
        assert openreview.tools.get_invitation(openreview_client, f'{venue_id}/-/Fee_Waiver') is None
        assert openreview_client.get_invitation('openreview.net/Template/-/Submission_Fee_Payment')
        assert openreview_client.get_invitation('openreview.net/Template/-/Fee_Waiver')

    def test_submit_abstracts(self, openreview_client, helpers):

        venue_id = self.venue_id

        author_one_client = helpers.create_user('authorone@icml2027.cc', 'AuthorOne', 'ICMLTwentySeven')
        author_two_client = helpers.create_user('authortwo@icml2027.cc', 'AuthorTwo', 'ICMLTwentySeven')
        author_three_client = helpers.create_user('authorthree@icml2027.cc', 'AuthorThree', 'ICMLTwentySeven')
        helpers.create_user('authorfour@aau.edu.et', 'AuthorFour', 'ICMLTwentySeven', country='ET')
        helpers.create_user('authorsix@aau.edu.et', 'AuthorSix', 'ICMLTwentySeven', country='ET')
        helpers.create_user('authorfive@iitb.ac.in', 'AuthorFive', 'ICMLTwentySeven', country='IN')

        ## abstracts only: the pdf is due at the full submission deadline
        author_one_client.post_note_edit(
            invitation=f'{venue_id}/-/Submission',
            signatures=['~AuthorOne_ICMLTwentySeven1'],
            note=openreview.api.Note(
                license='CC BY 4.0',
                content={
                    'title': { 'value': 'Paper title 1' },
                    'abstract': { 'value': 'This is the abstract of submission 1' },
                    'authors': {
                        'value': [
                            { 'fullname': 'AuthorOne ICMLTwentySeven', 'username': '~AuthorOne_ICMLTwentySeven1', 'institutions': [{ 'domain': 'icml2027.cc', 'country': 'US' }] },
                            { 'fullname': 'AuthorTwo ICMLTwentySeven', 'username': '~AuthorTwo_ICMLTwentySeven1', 'institutions': [{ 'domain': 'icml2027.cc', 'country': 'US' }] }
                        ]
                    },
                    'keywords': { 'value': ['machine learning'] },
                    'email_sharing': { 'value': 'We authorize the sharing of all author emails with Program Chairs.' },
                    'data_release': { 'value': 'We authorize the release of our submission and author names to the public in the event of acceptance.' }
                }
            )
        )

        author_two_client.post_note_edit(
            invitation=f'{venue_id}/-/Submission',
            signatures=['~AuthorTwo_ICMLTwentySeven1'],
            note=openreview.api.Note(
                license='CC BY 4.0',
                content={
                    'title': { 'value': 'Paper title 2' },
                    'abstract': { 'value': 'This is the abstract of submission 2' },
                    'authors': {
                        'value': [
                            { 'fullname': 'AuthorTwo ICMLTwentySeven', 'username': '~AuthorTwo_ICMLTwentySeven1', 'institutions': [{ 'domain': 'icml2027.cc', 'country': 'US' }] },
                            { 'fullname': 'AuthorThree ICMLTwentySeven', 'username': '~AuthorThree_ICMLTwentySeven1', 'institutions': [{ 'domain': 'icml2027.cc', 'country': 'US' }] },
                            { 'fullname': 'AuthorFour ICMLTwentySeven', 'username': '~AuthorFour_ICMLTwentySeven1', 'institutions': [{ 'domain': 'aau.edu.et', 'country': 'ET' }] },
                            { 'fullname': 'AuthorSix ICMLTwentySeven', 'username': '~AuthorSix_ICMLTwentySeven1', 'institutions': [{ 'domain': 'aau.edu.et', 'country': 'ET' }] }
                        ]
                    },
                    'keywords': { 'value': ['machine learning'] },
                    'email_sharing': { 'value': 'We authorize the sharing of all author emails with Program Chairs.' },
                    'data_release': { 'value': 'We authorize the release of our submission and author names to the public in the event of acceptance.' }
                }
            )
        )

        author_three_client.post_note_edit(
            invitation=f'{venue_id}/-/Submission',
            signatures=['~AuthorThree_ICMLTwentySeven1'],
            note=openreview.api.Note(
                license='CC BY 4.0',
                content={
                    'title': { 'value': 'Paper title 3' },
                    'abstract': { 'value': 'This is the abstract of submission 3' },
                    'authors': {
                        'value': [
                            { 'fullname': 'AuthorThree ICMLTwentySeven', 'username': '~AuthorThree_ICMLTwentySeven1', 'institutions': [{ 'domain': 'icml2027.cc', 'country': 'US' }] },
                            { 'fullname': 'AuthorFive ICMLTwentySeven', 'username': '~AuthorFive_ICMLTwentySeven1', 'institutions': [{ 'domain': 'iitb.ac.in', 'country': 'IN' }] }
                        ]
                    },
                    'keywords': { 'value': ['machine learning'] },
                    'email_sharing': { 'value': 'We authorize the sharing of all author emails with Program Chairs.' },
                    'data_release': { 'value': 'We authorize the release of our submission and author names to the public in the event of acceptance.' }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, invitation=f'{venue_id}/-/Submission', count=3)

        submissions = openreview_client.get_notes(invitation=f'{venue_id}/-/Submission', sort='number:asc')
        assert len(submissions) == 3
        assert all('value' not in submission.content.get('pdf', {}) for submission in submissions)

        ## close the abstract deadline
        pc_client = openreview.api.OpenReviewClient(username='programchair@icml2027.cc', password=helpers.strong_password)
        submission_invitation = pc_client.get_invitation(f'{venue_id}/-/Submission')
        abstract_due_date = openreview.tools.datetime_millis(datetime.datetime.now() - datetime.timedelta(hours=3))

        edit = pc_client.post_invitation_edit(
            invitations=f'{venue_id}/-/Submission/Dates',
            content={
                'activation_date': { 'value': submission_invitation.cdate },
                'due_date': { 'value': abstract_due_date }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        submission_invitation = pc_client.get_invitation(f'{venue_id}/-/Submission')
        assert submission_invitation.expdate == abstract_due_date + (30*60*1000)
        assert submission_invitation.expdate < openreview.tools.datetime_millis(datetime.datetime.now())

    def test_enable_submission_fee_payment(self, openreview_client, helpers):

        venue_id = self.venue_id
        support_group_id = openreview_client.get_group('openreview.net/Support').id

        pc_client = openreview.api.OpenReviewClient(username='programchair@icml2027.cc', password=helpers.strong_password)

        now = datetime.datetime.now()
        payment_due_date = openreview.tools.datetime_millis(now + datetime.timedelta(weeks=2))
        payment_expiration_date = openreview.tools.datetime_millis(now + datetime.timedelta(weeks=2, minutes=30))
        fee_content = {
            'venue_id': { 'value': venue_id },
            'name': { 'value': 'Submission_Fee_Payment' },
            'activation_date': { 'value': openreview.tools.datetime_millis(now) },
            'due_date': { 'value': payment_due_date },
            'expiration_date': { 'value': payment_expiration_date },
            'amount': { 'value': 2000 },
            'currency': { 'value': 'USD' },
            'country_fees': { 'value': { 'ET': 0, 'IN': 1000 } },
            'waiver_name': { 'value': 'Fee_Waiver' },
            'submission_name': { 'value': 'Submission' }
        }

        ## support enables a fee of 20 USD per submission once the full submission deadline is over
        with pytest.raises(openreview.OpenReviewException, match=r'The submission fee activation date must be later than or equal to the Full Submission deadline'):
            openreview_client.post_invitation_edit(
                invitations='openreview.net/Template/-/Submission_Fee_Payment',
                signatures=[support_group_id],
                content=fee_content
            )

        submission_invitation = pc_client.get_invitation(f'{venue_id}/-/Submission')
        edit = pc_client.post_invitation_edit(
            invitations=f'{venue_id}/-/Full_Submission/Dates',
            content={
                'activation_date': { 'value': submission_invitation.expdate },
                'due_date': { 'value': openreview.tools.datetime_millis(now - datetime.timedelta(hours=2)) },
                'expiration_date': { 'value': openreview.tools.datetime_millis(now - datetime.timedelta(hours=1, minutes=30)) }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])
        helpers.await_queue_edit(openreview_client, f'{venue_id}/-/Full_Submission-0-1', count=2)

        with pytest.raises(openreview.OpenReviewException, match=r'India is not an ISO 3166-1 alpha-2 country code'):
            openreview_client.post_invitation_edit(
                invitations='openreview.net/Template/-/Submission_Fee_Payment',
                signatures=[support_group_id],
                content={ **fee_content, 'country_fees': { 'value': { 'ET': 0, 'India': 1000 } } }
            )

        with pytest.raises(openreview.OpenReviewException, match=r'The fee of IN must be an integer from 0 to the full amount, 2000'):
            openreview_client.post_invitation_edit(
                invitations='openreview.net/Template/-/Submission_Fee_Payment',
                signatures=[support_group_id],
                content={ **fee_content, 'country_fees': { 'value': { 'ET': 0, 'IN': 3000 } } }
            )

        with pytest.raises(openreview.OpenReviewException, match=r'Enable the Fee_Waiver step first'):
            openreview_client.post_invitation_edit(
                invitations='openreview.net/Template/-/Submission_Fee_Payment',
                signatures=[support_group_id],
                content=fee_content
            )

        openreview_client.post_invitation_edit(
            invitations='openreview.net/Template/-/Fee_Waiver',
            signatures=[support_group_id],
            content={
                'venue_id': { 'value': venue_id },
                'name': { 'value': 'Fee_Waiver' },
                'payment_name': { 'value': 'Submission_Fee_Payment' },
                'submission_name': { 'value': 'Submission' }
            }
        )

        waiver_invitation = openreview_client.get_invitation(f'{venue_id}/-/Fee_Waiver')
        assert waiver_invitation.domain == venue_id
        assert waiver_invitation.signatures == [support_group_id]
        assert waiver_invitation.invitees == [venue_id]
        assert waiver_invitation.readers == [venue_id, support_group_id]
        assert waiver_invitation.type == 'Note'
        assert waiver_invitation.edit['signatures'] == [venue_id]
        assert waiver_invitation.edit['note']['forum'] == { 'param': { 'withInvitation': f'{venue_id}/-/Submission' } }
        assert waiver_invitation.edit['note']['replyto'] == { 'param': { 'withInvitation': f'{venue_id}/-/Submission' } }
        assert waiver_invitation.edit['note']['readers'] == [venue_id, support_group_id]
        assert waiver_invitation.edit['note']['writers'] == [support_group_id]
        assert list(waiver_invitation.edit['note']['content'].keys()) == ['qualifying_authors', 'country', 'comment']

        edit = openreview_client.post_invitation_edit(
            invitations='openreview.net/Template/-/Submission_Fee_Payment',
            signatures=[support_group_id],
            content=fee_content
        )
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])
        helpers.await_queue_edit(openreview_client, edit_id=f'{venue_id}/-/Submission_Fee_Payment-0-1', count=1)

        invitation = openreview_client.get_invitation(f'{venue_id}/-/Submission_Fee_Payment')
        assert invitation.domain == venue_id
        assert invitation.signatures == [venue_id]
        assert invitation.content['amount']['value'] == 2000
        assert invitation.content['currency']['value'] == 'USD'
        assert invitation.content['country_fees']['value'] == { 'ET': 0, 'IN': 1000 }
        assert invitation.edit['invitation']['duedate'] == payment_due_date
        assert invitation.edit['invitation']['expdate'] == payment_expiration_date
        assert 'Submission fees are non-refundable' in invitation.description
        assert 'the venue chooses whether to desk reject the submissions with unpaid fees' in invitation.description
        assert openreview_client.get_group(venue_id).content['submission_fee_payment_id']['value'] == f'{venue_id}/-/Submission_Fee_Payment'

        dates_invitation = openreview_client.get_invitation(f'{venue_id}/-/Submission_Fee_Payment/Dates')
        assert list(dates_invitation.edit['content'].keys()) == ['activation_date', 'due_date', 'expiration_date']

        amount_invitation = openreview_client.get_invitation(f'{venue_id}/-/Submission_Fee_Payment/Amount')
        assert amount_invitation.signatures == [venue_id]
        assert amount_invitation.edit['signatures'] == [f'{venue_id}/Program_Chairs']
        assert list(amount_invitation.edit['content'].keys()) == ['amount']

        country_fees_invitation = openreview_client.get_invitation(f'{venue_id}/-/Submission_Fee_Payment/Country_Fees')
        assert country_fees_invitation.signatures == [venue_id]
        assert country_fees_invitation.invitees == [venue_id, support_group_id]
        assert country_fees_invitation.edit['signatures'] == { 'param': { 'items': [{ 'value': f'{venue_id}/Program_Chairs', 'optional': True }, { 'value': support_group_id, 'optional': True }] } }
        assert list(country_fees_invitation.edit['content'].keys()) == ['country_fees']

        submissions = openreview_client.get_notes(invitation=f'{venue_id}/-/Submission', sort='number:asc')
        payment_invitations = openreview_client.get_all_invitations(invitation=f'{venue_id}/-/Submission_Fee_Payment')
        assert len(payment_invitations) == 3

        for submission in submissions:
            payment_invitation = openreview_client.get_invitation(f'{venue_id}/Submission{submission.number}/-/Submission_Fee_Payment')
            assert payment_invitation.signatures == [venue_id]
            assert payment_invitation.writers == [venue_id, support_group_id]
            assert payment_invitation.invitees == [venue_id, f'{venue_id}/Submission{submission.number}/Authors', support_group_id]
            assert payment_invitation.duedate == payment_due_date
            assert payment_invitation.expdate == payment_expiration_date
            assert payment_invitation.content['currency']['value'] == 'USD'
            assert payment_invitation.content['terms']['value'] == 'I agree to the [OpenReview Terms of Use](https://openreview.net/legal/terms) and understand that submission fees are non-refundable.'
            assert payment_invitation.edit['signature'] == { 'param': { 'const': support_group_id } }
            assert payment_invitation.edit['payment']['note'] == submission.id
            assert payment_invitation.edit['payment']['amount'] == { 'param': { 'minimum': 0 } }
            assert payment_invitation.edit['payment']['currency'] == 'USD'
            assert payment_invitation.edit['payment']['readers'] == [venue_id, f'{venue_id}/Submission{submission.number}/Authors', support_group_id]

        assert [openreview_client.get_invitation(f'{venue_id}/Submission{number}/-/Submission_Fee_Payment').content['amount']['value'] for number in [1, 2, 3]] == [2000, 0, 1000]

        fee_invitations = [invitation, dates_invitation, amount_invitation, country_fees_invitation, waiver_invitation] + payment_invitations
        assert len(fee_invitations) == 8
        assert all('~Super_User1' not in fee_invitation.signatures for fee_invitation in fee_invitations)

        ## authors can see the fee of their submission only
        author_one_client = openreview.api.OpenReviewClient(username='authorone@icml2027.cc', password=helpers.strong_password)
        assert author_one_client.get_invitation(f'{venue_id}/Submission1/-/Submission_Fee_Payment').content['amount']['value'] == 2000
        with pytest.raises(openreview.OpenReviewException, match=r'Forbidden|NotFound|cannot read'):
            author_one_client.get_invitation(f'{venue_id}/Submission3/-/Submission_Fee_Payment')

        ## the forum page finds the fee of a submission in its forum
        forum_payment_invitations = author_one_client.get_invitations(replyForum=submissions[0].id, type='payment')
        assert [i.id for i in forum_payment_invitations] == [f'{venue_id}/Submission1/-/Submission_Fee_Payment']
        assert f'{venue_id}/Submission1/-/Submission_Fee_Payment' not in [i.id for i in author_one_client.get_invitations(replyForum=submissions[0].id, type='note')]
        assert f'{venue_id}/Submission1/-/Submission_Fee_Payment' in [i.id for i in pc_client.get_invitations(replyForum=submissions[0].id, prefix=f'{venue_id}/Submission1')]

        ## and the payments page lists every fee an author is invited to pay
        author_two_client = openreview.api.OpenReviewClient(username='authortwo@icml2027.cc', password=helpers.strong_password)
        assert sorted([i.id for i in author_two_client.get_all_invitations(invitee=True, type='payment') if i.domain == venue_id]) == [
            f'{venue_id}/Submission1/-/Submission_Fee_Payment',
            f'{venue_id}/Submission2/-/Submission_Fee_Payment'
        ]

    def test_automatic_waivers(self, openreview_client, helpers):

        venue_id = self.venue_id
        support_group_id = openreview_client.get_group('openreview.net/Support').id

        author_two_client = openreview.api.OpenReviewClient(username='authortwo@icml2027.cc', password=helpers.strong_password)
        author_three_client = openreview.api.OpenReviewClient(username='authorthree@icml2027.cc', password=helpers.strong_password)
        pc_client = openreview.api.OpenReviewClient(username='programchair@icml2027.cc', password=helpers.strong_password)

        submissions = openreview_client.get_notes(invitation=f'{venue_id}/-/Submission', sort='number:asc')
        submission = submissions[1]

        helpers.await_queue_edit(openreview_client, invitation=f'{venue_id}/-/Fee_Waiver', count=1)
        helpers.await_queue_edit(openreview_client, invitation=f'{venue_id}/Submission2/-/Submission_Fee_Payment', count=1)

        waiver_notes = pc_client.get_all_notes(invitation=f'{venue_id}/-/Fee_Waiver')
        assert [(note.forum, note.replyto, note.signatures) for note in waiver_notes] == [(submission.id, submission.id, [venue_id])]
        assert waiver_notes[0].content['qualifying_authors']['value'] == ['~AuthorFour_ICMLTwentySeven1', '~AuthorSix_ICMLTwentySeven1']
        assert waiver_notes[0].content['country']['value'] == 'ET'
        assert 'comment' not in waiver_notes[0].content
        assert waiver_notes[0].readers == [venue_id, support_group_id]

        assert [note.id for note in pc_client.get_all_notes(forum=submission.id) if note.invitations[0] == f'{venue_id}/-/Fee_Waiver'] == [waiver_notes[0].id]
        assert [note for note in author_two_client.get_all_notes(forum=submission.id) if note.invitations[0] == f'{venue_id}/-/Fee_Waiver'] == []

        assert f'{venue_id}/-/Fee_Waiver' in [i.id for i in pc_client.get_invitations(replyForum=submissions[0].id, type='note')]
        assert f'{venue_id}/-/Fee_Waiver' not in [i.id for i in author_two_client.get_invitations(replyForum=submissions[0].id, type='note')]

        payments = author_three_client.get_payments(note=submission.id)
        assert len(payments) == 1
        assert payments[0].status == 'waived'
        assert payments[0].amount == 0
        assert payments[0].currency == 'USD'
        assert payments[0].signature == support_group_id
        assert payments[0].invitations[0] == f'{venue_id}/Submission2/-/Submission_Fee_Payment'
        assert not payments[0].transaction_id
        assert len(pc_client.get_payments(note=submission.id, status='waived')) == 1

        messages = openreview_client.get_messages(to='authorfour@aau.edu.et', subject='[ICML 2027] The submission fee has been waived for submission number 2')
        assert len(messages) == 1
        assert 'The submission fee of your submission to ICML 2027 has been waived. No payment is due for this submission.' in messages[0]['content']['text']
        assert messages[0]['content']['text'].count('Please note that responding to this email will direct your reply to icml2027.programchairs@gmail.com.') == 1
        assert len(openreview_client.get_messages(to='authortwo@icml2027.cc', subject='[ICML 2027] The submission fee has been waived for submission number 2')) == 1

        ## a waived fee can not be paid
        with pytest.raises(openreview.OpenReviewException, match=r'already settled'):
            author_three_client.checkout_payment(invitation=f'{venue_id}/Submission2/-/Submission_Fee_Payment', payment=Payment(note=submission.id))

        with pytest.raises(openreview.OpenReviewException, match=r'The submission fee of this submission is already waived'):
            pc_client.post_note_edit(
                invitation=f'{venue_id}/-/Fee_Waiver',
                signatures=[venue_id],
                note=openreview.api.Note(
                    forum=submission.id,
                    replyto=submission.id,
                    content={ 'comment': { 'value': 'Waived by the program chairs' } }
                )
            )

        assert pc_client.get_payments(note=submissions[0].id) == []
        assert pc_client.get_payments(note=submissions[2].id) == []

    def test_pay_submission_fee(self, openreview_client, helpers):

        venue_id = self.venue_id
        support_group_id = openreview_client.get_group('openreview.net/Support').id
        payment_invitation_id = f'{venue_id}/Submission1/-/Submission_Fee_Payment'

        author_one_client = openreview.api.OpenReviewClient(username='authorone@icml2027.cc', password=helpers.strong_password)
        author_two_client = openreview.api.OpenReviewClient(username='authortwo@icml2027.cc', password=helpers.strong_password)
        author_five_client = openreview.api.OpenReviewClient(username='authorfive@iitb.ac.in', password=helpers.strong_password)
        pc_client = openreview.api.OpenReviewClient(username='programchair@icml2027.cc', password=helpers.strong_password)
        outsider_client = helpers.create_user('outsider@icml2027.cc', 'Outsider', 'ICMLTwentySeven')

        submission = openreview_client.get_notes(invitation=f'{venue_id}/-/Submission', number=1)[0]

        ## only the authors of the submission can pay its fee, nobody else can even see it
        with pytest.raises(openreview.OpenReviewException, match=r'does not have permission to see Invitation'):
            outsider_client.checkout_payment(invitation=payment_invitation_id, payment=Payment(note=submission.id))

        ## authors never post a payment directly, they pay through checkout
        with pytest.raises(openreview.OpenReviewException, match=r'does not have permission'):
            author_one_client.post_payment_edit(
                invitation=payment_invitation_id,
                signature='~AuthorOne_ICMLTwentySeven1',
                payment=Payment(note=submission.id, amount=2000, currency='USD', status='paid', signature='~AuthorOne_ICMLTwentySeven1')
            )

        checkout = author_one_client.checkout_payment(invitation=payment_invitation_id, payment=Payment(note=submission.id))
        assert 'fake-gateway.test' in checkout['url']
        assert checkout['paymentId']

        payments = author_one_client.get_payments(note=submission.id)
        assert len(payments) == 1
        assert payments[0].id == checkout['paymentId']
        assert payments[0].status == 'pending'
        assert payments[0].amount == 2000
        assert payments[0].currency == 'USD'
        assert payments[0].signature == '~AuthorOne_ICMLTwentySeven1'
        assert payments[0].invitations[0] == payment_invitation_id
        assert payments[0].readers == [venue_id, f'{venue_id}/Submission1/Authors', support_group_id]

        ## co-authors and the program chairs see the payment, nobody else does
        assert len(author_two_client.get_payments(note=submission.id)) == 1
        assert len(pc_client.get_payments(note=submission.id)) == 1
        assert len(outsider_client.get_payments(note=submission.id)) == 0

        ## one checkout at a time per fee
        with pytest.raises(openreview.OpenReviewException, match=r'already in progress'):
            author_two_client.checkout_payment(invitation=payment_invitation_id, payment=Payment(note=submission.id))

        ## any author can clear an abandoned checkout and pay again
        cancelled = author_two_client.cancel_payment(checkout['paymentId'])
        assert cancelled['status'] == 'expired'

        ## the amount always comes from the invitation, never from the payer
        checkout = author_two_client.checkout_payment(invitation=payment_invitation_id, payment=Payment(note=submission.id, amount=1))
        payment = author_two_client.get_payments(id=checkout['paymentId'])[0]
        assert payment.status == 'pending'
        assert payment.amount == 2000
        assert payment.signature == '~AuthorTwo_ICMLTwentySeven1'

        assert sorted([p.status for p in pc_client.get_payments(note=submission.id)]) == ['expired', 'pending']

        helpers.await_queue_edit(openreview_client, edit_id=cancelled['paymentId'], count=2)
        helpers.await_queue_edit(openreview_client, edit_id=checkout['paymentId'], count=1)
        assert not openreview_client.get_messages(subject='[ICML 2027] The submission fee has been paid for submission number 1')

        submission_three = openreview_client.get_notes(invitation=f'{venue_id}/-/Submission', number=3)[0]
        reduced_checkout = author_five_client.checkout_payment(invitation=f'{venue_id}/Submission3/-/Submission_Fee_Payment', payment=Payment(note=submission_three.id))
        reduced_payment = author_five_client.get_payments(id=reduced_checkout['paymentId'])[0]
        assert reduced_payment.status == 'pending'
        assert reduced_payment.amount == 1000
        assert reduced_payment.signature == '~AuthorFive_ICMLTwentySeven1'
        helpers.await_queue_edit(openreview_client, edit_id=reduced_checkout['paymentId'], count=1)

    def test_close_payments(self, openreview_client, helpers):

        venue_id = self.venue_id
        support_group_id = openreview_client.get_group('openreview.net/Support').id

        pc_client = openreview.api.OpenReviewClient(username='programchair@icml2027.cc', password=helpers.strong_password)
        author_one_client = openreview.api.OpenReviewClient(username='authorone@icml2027.cc', password=helpers.strong_password)
        author_three_client = openreview.api.OpenReviewClient(username='authorthree@icml2027.cc', password=helpers.strong_password)

        submissions = openreview_client.get_notes(invitation=f'{venue_id}/-/Submission', sort='number:asc')
        full_submission_invitation = pc_client.get_invitation(f'{venue_id}/-/Full_Submission')

        now = datetime.datetime.now()
        expiration_date = openreview.tools.datetime_millis(now - datetime.timedelta(minutes=30))

        pc_client.post_invitation_edit(
            invitations=f'{venue_id}/-/Submission_Fee_Payment/Dates',
            content={
                'activation_date': { 'value': full_submission_invitation.edit['invitation']['expdate'] },
                'due_date': { 'value': openreview.tools.datetime_millis(now - datetime.timedelta(hours=1)) },
                'expiration_date': { 'value': expiration_date }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id=f'{venue_id}/-/Submission_Fee_Payment-0-1', count=2)

        assert openreview_client.get_invitation(f'{venue_id}/Submission3/-/Submission_Fee_Payment').expdate == expiration_date

        with pytest.raises(openreview.OpenReviewException, match=r'The Invitation ICML.cc/2027/Conference/Submission3/-/Submission_Fee_Payment has expired'):
            author_three_client.checkout_payment(invitation=f'{venue_id}/Submission3/-/Submission_Fee_Payment', payment=Payment(note=submissions[2].id))

        reduced_checkout_in_progress = openreview_client.get_payments(note=submissions[2].id, status='pending')[0]
        assert reduced_checkout_in_progress.signature == '~AuthorFive_ICMLTwentySeven1'

        checkout_in_progress = openreview_client.get_payments(note=submissions[0].id, status='pending')[0]
        assert checkout_in_progress.signature == '~AuthorTwo_ICMLTwentySeven1'

        gateway_confirmation = openreview_client.post_payment_edit(
            invitation=f'{venue_id}/-/Edit',
            signature=support_group_id,
            readers=checkout_in_progress.readers,
            payment=Payment(id=checkout_in_progress.id, status='paid')
        )
        assert gateway_confirmation['payment']['status'] == 'paid'
        helpers.await_queue_edit(openreview_client, edit_id=checkout_in_progress.id, count=2)

        payment = author_one_client.get_payments(id=checkout_in_progress.id)[0]
        assert payment.status == 'paid'
        assert payment.amount == 2000
        assert payment.signature == '~AuthorTwo_ICMLTwentySeven1'
        assert payment.invitations == [f'{venue_id}/Submission1/-/Submission_Fee_Payment', f'{venue_id}/-/Edit']

        messages = openreview_client.get_messages(to='authorone@icml2027.cc', subject='[ICML 2027] The submission fee has been paid for submission number 1')
        assert len(messages) == 1
        assert messages[0]['content']['text'] == f'''Hi AuthorOne ICMLTwentySeven,

The submission fee of your submission to ICML 2027 has been paid. No further payment is due for this submission.

Submission Number: 1

Title: Paper title 1

Amount: 20.00 USD

Paid by: AuthorTwo ICMLTwentySeven

Submission fees are non-refundable.

To view your submission, click here: https://openreview.net/forum?id={submissions[0].id}

Please note that responding to this email will direct your reply to icml2027.programchairs@gmail.com.
'''

        messages = openreview_client.get_messages(to='authortwo@icml2027.cc', subject='[ICML 2027] The submission fee has been paid for submission number 1')
        assert len(messages) == 1

    def test_unsettled_submissions(self, openreview_client, helpers):

        venue_id = self.venue_id

        pc_client = openreview.api.OpenReviewClient(username='programchair@icml2027.cc', password=helpers.strong_password)

        ## the venue sees every payment of its domain, which is all a payment report needs
        submissions = pc_client.get_all_notes(invitation=f'{venue_id}/-/Submission', sort='number:asc')
        payments = pc_client.get_all_payments(domain=venue_id)
        assert sorted([(p.note, p.status) for p in payments]) == sorted([
            (submissions[0].id, 'expired'),
            (submissions[0].id, 'paid'),
            (submissions[1].id, 'waived'),
            (submissions[2].id, 'pending')
        ])

        settled = { p.note for p in payments if p.status in ['paid', 'waived'] }
        assert [s.number for s in submissions if s.id not in settled] == [3]

    def test_waive_unpaid_fee(self, openreview_client, helpers):

        venue_id = self.venue_id
        support_group_id = openreview_client.get_group('openreview.net/Support').id

        pc_client = openreview.api.OpenReviewClient(username='programchair@icml2027.cc', password=helpers.strong_password)
        author_three_client = openreview.api.OpenReviewClient(username='authorthree@icml2027.cc', password=helpers.strong_password)
        author_five_client = openreview.api.OpenReviewClient(username='authorfive@iitb.ac.in', password=helpers.strong_password)

        submission = openreview_client.get_notes(invitation=f'{venue_id}/-/Submission', number=3)[0]

        with pytest.raises(openreview.OpenReviewException, match=r'does not have permission to see Invitation ICML.cc/2027/Conference/-/Fee_Waiver'):
            author_three_client.post_note_edit(
                invitation=f'{venue_id}/-/Fee_Waiver',
                signatures=['~AuthorThree_ICMLTwentySeven1'],
                note=openreview.api.Note(
                    forum=submission.id,
                    replyto=submission.id,
                    content={ 'comment': { 'value': 'Please waive our fee' } }
                )
            )

        with pytest.raises(openreview.OpenReviewException, match=r'Give the country or a comment that explains the waiver'):
            pc_client.post_note_edit(
                invitation=f'{venue_id}/-/Fee_Waiver',
                signatures=[venue_id],
                note=openreview.api.Note(
                    forum=submission.id,
                    replyto=submission.id,
                    content={ 'qualifying_authors': { 'value': ['~AuthorFive_ICMLTwentySeven1'] } }
                )
            )

        submission_one = openreview_client.get_notes(invitation=f'{venue_id}/-/Submission', number=1)[0]
        with pytest.raises(openreview.OpenReviewException, match=r'A fee waiver must reply to the submission itself'):
            pc_client.post_note_edit(
                invitation=f'{venue_id}/-/Fee_Waiver',
                signatures=[venue_id],
                note=openreview.api.Note(
                    forum=submission.id,
                    replyto=submission_one.id,
                    content={ 'comment': { 'value': 'The venue keeps this submission.' } }
                )
            )

        pc_client.post_note_edit(
            invitation=f'{venue_id}/-/Fee_Waiver',
            signatures=[venue_id],
            note=openreview.api.Note(
                forum=submission.id,
                replyto=submission.id,
                content={ 'comment': { 'value': 'The venue keeps this submission.' } }
            )
        )
        helpers.await_queue_edit(openreview_client, invitation=f'{venue_id}/-/Fee_Waiver', count=2)

        waiver_note = [note for note in pc_client.get_all_notes(invitation=f'{venue_id}/-/Fee_Waiver') if note.forum == submission.id][0]
        assert waiver_note.content['comment']['value'] == 'The venue keeps this submission.'
        assert 'country' not in waiver_note.content
        helpers.await_queue_edit(openreview_client, invitation=f'{venue_id}/Submission3/-/Submission_Fee_Payment', count=3)

        payments = author_five_client.get_payments(note=submission.id)
        assert sorted([(p.status, p.amount, p.signature) for p in payments]) == [
            ('expired', 1000, '~AuthorFive_ICMLTwentySeven1'),
            ('waived', 1000, support_group_id)
        ]
        waived_payment = [p for p in payments if p.status == 'waived'][0]
        assert not waived_payment.transaction_id

        messages = openreview_client.get_messages(to='authorfive@iitb.ac.in', subject='[ICML 2027] The submission fee has been waived for submission number 3')
        assert len(messages) == 1

    def test_reopen_payments(self, openreview_client, helpers):

        venue_id = self.venue_id
        support_group_id = openreview_client.get_group('openreview.net/Support').id

        pc_client = openreview.api.OpenReviewClient(username='programchair@icml2027.cc', password=helpers.strong_password)
        author_one_client = openreview.api.OpenReviewClient(username='authorone@icml2027.cc', password=helpers.strong_password)

        submission = openreview_client.get_notes(invitation=f'{venue_id}/-/Submission', number=1)[0]
        invitation = pc_client.get_invitation(f'{venue_id}/-/Submission_Fee_Payment')

        now = datetime.datetime.now()
        new_due_date = openreview.tools.datetime_millis(now + datetime.timedelta(weeks=3))
        new_expiration_date = openreview.tools.datetime_millis(now + datetime.timedelta(weeks=3, minutes=30))

        pc_client.post_invitation_edit(
            invitations=f'{venue_id}/-/Submission_Fee_Payment/Dates',
            content={
                'activation_date': { 'value': invitation.cdate },
                'due_date': { 'value': new_due_date },
                'expiration_date': { 'value': new_expiration_date }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id=f'{venue_id}/-/Submission_Fee_Payment-0-1', count=3)

        invitation = openreview_client.get_invitation(f'{venue_id}/-/Submission_Fee_Payment')
        assert invitation.edit['invitation']['duedate'] == new_due_date
        assert invitation.edit['invitation']['expdate'] == new_expiration_date

        ## payments are still posted by support only, whoever signs the invitations
        payment_invitations = openreview_client.get_all_invitations(invitation=f'{venue_id}/-/Submission_Fee_Payment')
        assert len(payment_invitations) == 3
        for payment_invitation in payment_invitations:
            assert payment_invitation.duedate == new_due_date
            assert payment_invitation.expdate == new_expiration_date
            assert payment_invitation.edit['signature'] == { 'param': { 'const': support_group_id } }

        assert [openreview_client.get_invitation(f'{venue_id}/Submission{number}/-/Submission_Fee_Payment').content['amount']['value'] for number in [1, 2, 3]] == [2000, 0, 1000]
        assert len(pc_client.get_all_notes(invitation=f'{venue_id}/-/Fee_Waiver')) == 2

        with pytest.raises(openreview.OpenReviewException, match=r'already settled'):
            author_one_client.checkout_payment(invitation=f'{venue_id}/Submission1/-/Submission_Fee_Payment', payment=Payment(note=submission.id))

    def test_payments_page(self, openreview_client, helpers):

        venue_id = self.venue_id

        author_one_client = openreview.api.OpenReviewClient(username='authorone@icml2027.cc', password=helpers.strong_password)
        author_two_client = openreview.api.OpenReviewClient(username='authortwo@icml2027.cc', password=helpers.strong_password)
        author_five_client = openreview.api.OpenReviewClient(username='authorfive@iitb.ac.in', password=helpers.strong_password)

        ## one call gives the payments page every fee the author is invited to pay, its submission and its payments
        invitations = { i.id: i for i in author_two_client.get_invitations(invitee=True, type='payment', details='replytoNote,repliedPayments') if i.domain == venue_id }
        assert sorted(invitations.keys()) == [f'{venue_id}/Submission1/-/Submission_Fee_Payment', f'{venue_id}/Submission2/-/Submission_Fee_Payment']

        submission_one_fee = invitations[f'{venue_id}/Submission1/-/Submission_Fee_Payment']
        assert submission_one_fee.content['terms']['value'] == 'I agree to the [OpenReview Terms of Use](https://openreview.net/legal/terms) and understand that submission fees are non-refundable.'
        assert submission_one_fee.details['replytoNote']['content']['title']['value'] == 'Paper title 1'
        assert sorted([p['status'] for p in submission_one_fee.details['repliedPayments']]) == ['expired', 'paid']

        submission_two_fee = invitations[f'{venue_id}/Submission2/-/Submission_Fee_Payment']
        assert submission_two_fee.details['replytoNote']['content']['title']['value'] == 'Paper title 2'
        assert [(p['status'], p['amount']) for p in submission_two_fee.details['repliedPayments']] == [('waived', 0)]

        ## each author only gets the fees of their own submissions
        invitations = [i for i in author_one_client.get_invitations(invitee=True, type='payment', details='replytoNote,repliedPayments') if i.domain == venue_id]
        assert [i.id for i in invitations] == [f'{venue_id}/Submission1/-/Submission_Fee_Payment']
        assert len(invitations[0].details['repliedPayments']) == 2

        invitations = [i for i in author_five_client.get_invitations(invitee=True, type='payment', details='replytoNote,repliedPayments') if i.domain == venue_id]
        assert [i.id for i in invitations] == [f'{venue_id}/Submission3/-/Submission_Fee_Payment']
        assert sorted([(p['status'], p['amount']) for p in invitations[0].details['repliedPayments']]) == [('expired', 1000), ('waived', 1000)]

    def test_change_country_fees(self, openreview_client, helpers):

        venue_id = self.venue_id
        support_group_id = openreview_client.get_group('openreview.net/Support').id
        country_fees_invitation_id = f'{venue_id}/-/Submission_Fee_Payment/Country_Fees'

        pc_client = openreview.api.OpenReviewClient(username='programchair@icml2027.cc', password=helpers.strong_password)
        author_five_client = openreview.api.OpenReviewClient(username='authorfive@iitb.ac.in', password=helpers.strong_password)

        submissions = openreview_client.get_notes(invitation=f'{venue_id}/-/Submission', sort='number:asc')

        with pytest.raises(openreview.OpenReviewException, match=r'does not have permission to see Invitation ICML.cc/2027/Conference/-/Submission_Fee_Payment/Country_Fees'):
            author_five_client.post_invitation_edit(
                invitations=country_fees_invitation_id,
                signatures=['~AuthorFive_ICMLTwentySeven1'],
                content={ 'country_fees': { 'value': { 'IN': 0 } } }
            )

        with pytest.raises(openreview.OpenReviewException, match=r'India is not an ISO 3166-1 alpha-2 country code'):
            pc_client.post_invitation_edit(
                invitations=country_fees_invitation_id,
                signatures=[f'{venue_id}/Program_Chairs'],
                content={ 'country_fees': { 'value': { 'ET': 0, 'India': 500 } } }
            )

        with pytest.raises(openreview.OpenReviewException, match=r'The fee of IN must be an integer from 0 to the full amount, 2000'):
            pc_client.post_invitation_edit(
                invitations=country_fees_invitation_id,
                signatures=[f'{venue_id}/Program_Chairs'],
                content={ 'country_fees': { 'value': { 'ET': 0, 'IN': 2500 } } }
            )

        pc_client.post_invitation_edit(
            invitations=country_fees_invitation_id,
            signatures=[f'{venue_id}/Program_Chairs'],
            content={ 'country_fees': { 'value': { 'ET': 0, 'IN': 500 } } }
        )
        helpers.await_queue_edit(openreview_client, edit_id=f'{venue_id}/-/Submission_Fee_Payment-0-1', count=4)

        assert openreview_client.get_invitation(f'{venue_id}/-/Submission_Fee_Payment').content['country_fees']['value'] == { 'ET': 0, 'IN': 500 }
        assert [openreview_client.get_invitation(f'{venue_id}/Submission{number}/-/Submission_Fee_Payment').content['amount']['value'] for number in [1, 2, 3]] == [2000, 0, 500]

        assert sorted([(p.status, p.amount) for p in pc_client.get_payments(note=submissions[2].id)]) == [('expired', 1000), ('waived', 1000)]
        assert len(pc_client.get_all_notes(invitation=f'{venue_id}/-/Fee_Waiver')) == 2

        with pytest.raises(openreview.OpenReviewException, match=r'Enter \{"delete": true\} to remove the fees by country'):
            pc_client.post_invitation_edit(
                invitations=country_fees_invitation_id,
                signatures=[f'{venue_id}/Program_Chairs'],
                content={ 'country_fees': { 'value': {} } }
            )

        openreview_client.post_invitation_edit(
            invitations=country_fees_invitation_id,
            signatures=[support_group_id],
            content={ 'country_fees': { 'value': { 'delete': True } } }
        )
        helpers.await_queue_edit(openreview_client, edit_id=f'{venue_id}/-/Submission_Fee_Payment-0-1', count=5)

        assert openreview_client.get_invitation(f'{venue_id}/-/Submission_Fee_Payment').get_content_value('country_fees') is None
        assert [openreview_client.get_invitation(f'{venue_id}/Submission{number}/-/Submission_Fee_Payment').content['amount']['value'] for number in [1, 2, 3]] == [2000, 2000, 2000]
        assert [(p.status, p.amount) for p in pc_client.get_payments(note=submissions[1].id)] == [('waived', 0)]
