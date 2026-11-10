import pytest
import datetime
import openreview
from openreview.api import Note
from openreview.api import Payment

class TestNeurIPS2027Conference():

    venue_id = 'NeurIPS.cc/2027/Conference'

    def test_setup(self, openreview_client, helpers):

        venue_id = self.venue_id
        support_group_id = 'openreview.net/Support'

        helpers.create_user('programchair@neurips2027.cc', 'ProgramChair', 'NeurIPSTwentySeven')
        pc_client = openreview.api.OpenReviewClient(username='programchair@neurips2027.cc', password=helpers.strong_password)

        now = datetime.datetime.now()
        abstract_due_date = now + datetime.timedelta(days=2)
        full_submission_due_date = abstract_due_date + datetime.timedelta(days=4)

        request = pc_client.post_note_edit(invitation='openreview.net/Support/Venue_Request/-/Conference_Review_Workflow',
            signatures=['~ProgramChair_NeurIPSTwentySeven1'],
            note=openreview.api.Note(
                content={
                    'official_venue_name': { 'value': 'Forty-First Annual Conference on Neural Information Processing Systems' },
                    'abbreviated_venue_name': { 'value': 'NeurIPS 2027' },
                    'venue_website_url': { 'value': 'https://neurips.cc/Conferences/2027' },
                    'location': { 'value': 'Vancouver, Canada' },
                    'venue_start_date': { 'value': openreview.tools.datetime_millis(now + datetime.timedelta(weeks=52)) },
                    'program_chair_emails': { 'value': ['programchair@neurips2027.cc'] },
                    'contact_email': { 'value': 'neurips2027.programchairs@gmail.com' },
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

        assert openreview.tools.get_invitation(openreview_client, f'{venue_id}/-/Submission_Fee_Payment') is None
        assert openreview.tools.get_invitation(openreview_client, f'{venue_id}/-/Fee_Waiver_Request') is None
        assert openreview.tools.get_invitation(openreview_client, f'{venue_id}/-/Fee_Waiver_Decision') is None

    def test_submit_abstracts(self, openreview_client, helpers):

        venue_id = self.venue_id

        author_one_client = helpers.create_user('authorone@icml2027.cc', 'AuthorOne', 'ICMLTwentySeven')
        author_two_client = helpers.create_user('authortwo@icml2027.cc', 'AuthorTwo', 'ICMLTwentySeven')
        author_three_client = helpers.create_user('authorthree@icml2027.cc', 'AuthorThree', 'ICMLTwentySeven')

        author_one_client.post_note_edit(
            invitation=f'{venue_id}/-/Submission',
            signatures=['~AuthorOne_ICMLTwentySeven1'],
            note=openreview.api.Note(
                license='CC BY 4.0',
                content={
                    'title': { 'value': 'NeurIPS paper title 1' },
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
                    'title': { 'value': 'NeurIPS paper title 2' },
                    'abstract': { 'value': 'This is the abstract of submission 2' },
                    'authors': {
                        'value': [
                            { 'fullname': 'AuthorTwo ICMLTwentySeven', 'username': '~AuthorTwo_ICMLTwentySeven1', 'institutions': [{ 'domain': 'icml2027.cc', 'country': 'US' }] },
                            { 'fullname': 'AuthorThree ICMLTwentySeven', 'username': '~AuthorThree_ICMLTwentySeven1', 'institutions': [{ 'domain': 'icml2027.cc', 'country': 'US' }] }
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
                    'title': { 'value': 'NeurIPS paper title 3' },
                    'abstract': { 'value': 'This is the abstract of submission 3' },
                    'authors': {
                        'value': [
                            { 'fullname': 'AuthorThree ICMLTwentySeven', 'username': '~AuthorThree_ICMLTwentySeven1', 'institutions': [{ 'domain': 'icml2027.cc', 'country': 'US' }] }
                        ]
                    },
                    'keywords': { 'value': ['machine learning'] },
                    'email_sharing': { 'value': 'We authorize the sharing of all author emails with Program Chairs.' },
                    'data_release': { 'value': 'We authorize the release of our submission and author names to the public in the event of acceptance.' }
                }
            )
        )

        author_one_client.post_note_edit(
            invitation=f'{venue_id}/-/Submission',
            signatures=['~AuthorOne_ICMLTwentySeven1'],
            note=openreview.api.Note(
                license='CC BY 4.0',
                content={
                    'title': { 'value': 'NeurIPS paper title 4' },
                    'abstract': { 'value': 'This is the abstract of submission 4' },
                    'authors': {
                        'value': [
                            { 'fullname': 'AuthorOne ICMLTwentySeven', 'username': '~AuthorOne_ICMLTwentySeven1', 'institutions': [{ 'domain': 'icml2027.cc', 'country': 'US' }] },
                            { 'fullname': 'AuthorThree ICMLTwentySeven', 'username': '~AuthorThree_ICMLTwentySeven1', 'institutions': [{ 'domain': 'icml2027.cc', 'country': 'US' }] }
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
                    'title': { 'value': 'NeurIPS paper title 5' },
                    'abstract': { 'value': 'This is the abstract of submission 5' },
                    'authors': {
                        'value': [
                            { 'fullname': 'AuthorThree ICMLTwentySeven', 'username': '~AuthorThree_ICMLTwentySeven1', 'institutions': [{ 'domain': 'icml2027.cc', 'country': 'US' }] },
                            { 'fullname': 'AuthorTwo ICMLTwentySeven', 'username': '~AuthorTwo_ICMLTwentySeven1', 'institutions': [{ 'domain': 'icml2027.cc', 'country': 'US' }] }
                        ]
                    },
                    'keywords': { 'value': ['machine learning'] },
                    'email_sharing': { 'value': 'We authorize the sharing of all author emails with Program Chairs.' },
                    'data_release': { 'value': 'We authorize the release of our submission and author names to the public in the event of acceptance.' }
                }
            )
        )

        helpers.await_queue_edit(openreview_client, invitation=f'{venue_id}/-/Submission', count=5)

        submissions = openreview_client.get_notes(invitation=f'{venue_id}/-/Submission', sort='number:asc')
        assert [submission.content['title']['value'] for submission in submissions] == [
            'NeurIPS paper title 1',
            'NeurIPS paper title 2',
            'NeurIPS paper title 3',
            'NeurIPS paper title 4',
            'NeurIPS paper title 5'
        ]

        pc_client = openreview.api.OpenReviewClient(username='programchair@neurips2027.cc', password=helpers.strong_password)
        submission_invitation = pc_client.get_invitation(f'{venue_id}/-/Submission')
        abstract_due_date = openreview.tools.datetime_millis(datetime.datetime.now() - datetime.timedelta(minutes=30))

        edit = pc_client.post_invitation_edit(
            invitations=f'{venue_id}/-/Submission/Dates',
            content={
                'activation_date': { 'value': submission_invitation.cdate },
                'due_date': { 'value': abstract_due_date }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        submission_invitation = pc_client.get_invitation(f'{venue_id}/-/Submission')
        assert submission_invitation.expdate < openreview.tools.datetime_millis(datetime.datetime.now())

    def test_enable_submission_fee(self, openreview_client, helpers):

        venue_id = self.venue_id
        support_group_id = openreview_client.get_group('openreview.net/Support').id

        now = datetime.datetime.now()
        payment_due_date = openreview.tools.datetime_millis(now + datetime.timedelta(weeks=1))
        payment_expiration_date = openreview.tools.datetime_millis(now + datetime.timedelta(weeks=1, days=1))

        edit = openreview_client.post_invitation_edit(
            invitations='openreview.net/Template/-/Submission_Fee_Payment',
            signatures=[support_group_id],
            content={
                'venue_id': { 'value': venue_id },
                'name': { 'value': 'Submission_Fee_Payment' },
                'activation_date': { 'value': openreview.tools.datetime_millis(now) },
                'due_date': { 'value': payment_due_date },
                'expiration_date': { 'value': payment_expiration_date },
                'amount': { 'value': 3000 },
                'currency': { 'value': 'USD' },
                'submission_name': { 'value': 'Submission' }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])
        helpers.await_queue_edit(openreview_client, edit_id=f'{venue_id}/-/Submission_Fee_Payment-0-1', count=1)

        payment_invitations = openreview_client.get_all_invitations(invitation=f'{venue_id}/-/Submission_Fee_Payment')
        assert len(payment_invitations) == 5
        for payment_invitation in payment_invitations:
            assert payment_invitation.signatures == [venue_id]
            assert payment_invitation.duedate == payment_due_date
            assert payment_invitation.expdate == payment_expiration_date
            assert payment_invitation.description == 'Submission fees are non-refundable.'
            assert payment_invitation.content['amount']['value'] == 3000

        amount_invitation = openreview_client.get_invitation(f'{venue_id}/-/Submission_Fee_Payment/Amount')
        assert amount_invitation.edit['signatures'] == [f'{venue_id}/Program_Chairs']
        assert list(amount_invitation.edit['content'].keys()) == ['amount']

        openreview_client.post_invitation_edit(
            invitations='openreview.net/Template/-/Fee_Waiver_Decision',
            signatures=[support_group_id],
            content={
                'venue_id': { 'value': venue_id },
                'name': { 'value': 'Fee_Waiver_Decision' },
                'payment_name': { 'value': 'Submission_Fee_Payment' },
                'request_name': { 'value': 'Fee_Waiver_Request' }
            }
        )

        decision_invitation = openreview_client.get_invitation(f'{venue_id}/-/Fee_Waiver_Decision')
        assert decision_invitation.signatures == [support_group_id]

        edit = openreview_client.post_invitation_edit(
            invitations='openreview.net/Template/-/Fee_Waiver_Request',
            signatures=[support_group_id],
            content={
                'venue_id': { 'value': venue_id },
                'name': { 'value': 'Fee_Waiver_Request' },
                'activation_date': { 'value': openreview.tools.datetime_millis(now) },
                'due_date': { 'value': payment_due_date },
                'expiration_date': { 'value': payment_expiration_date },
                'payment_name': { 'value': 'Submission_Fee_Payment' },
                'decision_name': { 'value': 'Fee_Waiver_Decision' },
                'auto_grant_waivers': { 'value': False },
                'submission_name': { 'value': 'Submission' }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])
        helpers.await_queue_edit(openreview_client, edit_id=f'{venue_id}/-/Fee_Waiver_Request-0-1', count=1)

        waiver_invitation = openreview_client.get_invitation(f'{venue_id}/-/Fee_Waiver_Request')
        assert waiver_invitation.signatures == [venue_id]
        assert waiver_invitation.content['auto_grant_waivers']['value'] == False

        waiver_invitations = openreview_client.get_all_invitations(invitation=f'{venue_id}/-/Fee_Waiver_Request')
        assert len(waiver_invitations) == 5
        for waiver_invitation in waiver_invitations:
            assert waiver_invitation.signatures == [venue_id]
            assert waiver_invitation.expdate == payment_expiration_date

    def test_pay_submission_fees(self, openreview_client, helpers):

        venue_id = self.venue_id
        support_group_id = openreview_client.get_group('openreview.net/Support').id

        author_one_client = openreview.api.OpenReviewClient(username='authorone@icml2027.cc', password=helpers.strong_password)
        author_two_client = openreview.api.OpenReviewClient(username='authortwo@icml2027.cc', password=helpers.strong_password)
        pc_client = openreview.api.OpenReviewClient(username='programchair@neurips2027.cc', password=helpers.strong_password)

        submissions = openreview_client.get_notes(invitation=f'{venue_id}/-/Submission', sort='number:asc')

        checkout = author_one_client.checkout_payment(invitation=f'{venue_id}/Submission1/-/Submission_Fee_Payment', payment=Payment(note=submissions[0].id))
        assert 'fake-gateway.test' in checkout['url']

        checkout_in_progress = author_two_client.get_payments(id=checkout['paymentId'])[0]
        assert checkout_in_progress.status == 'pending'
        assert checkout_in_progress.amount == 3000
        assert checkout_in_progress.signature == '~AuthorOne_ICMLTwentySeven1'

        gateway_confirmation = openreview_client.post_payment_edit(
            invitation=f'{venue_id}/-/Edit',
            signature=support_group_id,
            readers=checkout_in_progress.readers,
            payment=Payment(id=checkout_in_progress.id, status='paid')
        )
        assert gateway_confirmation['payment']['status'] == 'paid'
        helpers.await_queue_edit(openreview_client, edit_id=checkout_in_progress.id, count=2)

        payments = author_two_client.get_payments(note=submissions[0].id)
        assert len(payments) == 1
        assert payments[0].status == 'paid'
        assert payments[0].signature == '~AuthorOne_ICMLTwentySeven1'

        messages = openreview_client.get_messages(to='authorone@icml2027.cc', subject='[NeurIPS 2027] The submission fee has been paid for submission number 1')
        assert len(messages) == 1
        assert 'Amount: 30.00 USD' in messages[0]['content']['text']
        assert 'Paid by: AuthorOne ICMLTwentySeven' in messages[0]['content']['text']

        messages = openreview_client.get_messages(to='authortwo@icml2027.cc', subject='[NeurIPS 2027] The submission fee has been paid for submission number 1')
        assert len(messages) == 1

        with pytest.raises(openreview.OpenReviewException, match=r'already settled'):
            author_two_client.checkout_payment(invitation=f'{venue_id}/Submission1/-/Submission_Fee_Payment', payment=Payment(note=submissions[0].id))

        checkout = author_two_client.checkout_payment(invitation=f'{venue_id}/Submission2/-/Submission_Fee_Payment', payment=Payment(note=submissions[1].id))
        helpers.await_queue_edit(openreview_client, edit_id=checkout['paymentId'], count=1)

        payments = pc_client.get_payments(note=submissions[1].id)
        assert len(payments) == 1
        assert payments[0].status == 'pending'
        assert payments[0].signature == '~AuthorTwo_ICMLTwentySeven1'
        assert not openreview_client.get_messages(subject='[NeurIPS 2027] The submission fee has been paid for submission number 2')

    def test_change_fee_amount(self, openreview_client, helpers):

        venue_id = self.venue_id

        author_one_client = openreview.api.OpenReviewClient(username='authorone@icml2027.cc', password=helpers.strong_password)
        author_three_client = openreview.api.OpenReviewClient(username='authorthree@icml2027.cc', password=helpers.strong_password)
        pc_client = openreview.api.OpenReviewClient(username='programchair@neurips2027.cc', password=helpers.strong_password)

        submissions = openreview_client.get_notes(invitation=f'{venue_id}/-/Submission', sort='number:asc')

        with pytest.raises(openreview.OpenReviewException, match=r'does not have permission to see Invitation NeurIPS.cc/2027/Conference/-/Submission_Fee_Payment/Amount'):
            author_one_client.post_invitation_edit(
                invitations=f'{venue_id}/-/Submission_Fee_Payment/Amount',
                signatures=['~AuthorOne_ICMLTwentySeven1'],
                content={
                    'amount': { 'value': 1 }
                }
            )

        with pytest.raises(openreview.OpenReviewException, match=r'must be >= 1'):
            pc_client.post_invitation_edit(
                invitations=f'{venue_id}/-/Submission_Fee_Payment/Amount',
                content={
                    'amount': { 'value': 0 }
                }
            )

        pc_client.post_invitation_edit(
            invitations=f'{venue_id}/-/Submission_Fee_Payment/Amount',
            content={
                'amount': { 'value': 2500 }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id=f'{venue_id}/-/Submission_Fee_Payment-0-1', count=2)

        invitation = openreview_client.get_invitation(f'{venue_id}/-/Submission_Fee_Payment')
        assert invitation.content['amount']['value'] == 2500
        assert invitation.edit['invitation']['content']['amount']['value'] == 2500

        payment_invitations = openreview_client.get_all_invitations(invitation=f'{venue_id}/-/Submission_Fee_Payment')
        assert len(payment_invitations) == 5
        for payment_invitation in payment_invitations:
            assert payment_invitation.content['amount']['value'] == 2500
            assert payment_invitation.content['currency']['value'] == 'USD'
            assert payment_invitation.description == 'Submission fees are non-refundable.'
            assert payment_invitation.edit['payment']['amount'] == { 'param': { 'minimum': 0 } }

        assert [(p.status, p.amount) for p in pc_client.get_payments(note=submissions[0].id)] == [('paid', 3000)]
        assert [(p.status, p.amount) for p in pc_client.get_payments(note=submissions[1].id)] == [('pending', 3000)]

        checkout = author_three_client.checkout_payment(invitation=f'{venue_id}/Submission3/-/Submission_Fee_Payment', payment=Payment(note=submissions[2].id))
        payment = author_three_client.get_payments(id=checkout['paymentId'])[0]
        assert payment.status == 'pending'
        assert payment.amount == 2500
        assert payment.currency == 'USD'

        cancelled = author_three_client.cancel_payment(checkout['paymentId'])
        assert cancelled['status'] == 'expired'

    def test_decide_fee_waivers(self, openreview_client, helpers):

        venue_id = self.venue_id
        support_group_id = openreview_client.get_group('openreview.net/Support').id

        author_one_client = openreview.api.OpenReviewClient(username='authorone@icml2027.cc', password=helpers.strong_password)
        author_three_client = openreview.api.OpenReviewClient(username='authorthree@icml2027.cc', password=helpers.strong_password)
        pc_client = openreview.api.OpenReviewClient(username='programchair@neurips2027.cc', password=helpers.strong_password)

        submissions = openreview_client.get_notes(invitation=f'{venue_id}/-/Submission', sort='number:asc')

        edit = author_one_client.post_note_edit(
            invitation=f'{venue_id}/Submission4/-/Fee_Waiver_Request',
            signatures=['~AuthorOne_ICMLTwentySeven1'],
            note=Note(
                content={
                    'low_income_economy': { 'value': 'Yes' },
                    'students_or_unaffiliated': { 'value': 'Yes' },
                    'no_payment_method': { 'value': 'No' }
                }
            )
        )
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])
        accepted_request_id = edit['note']['id']

        edit = author_three_client.post_note_edit(
            invitation=f'{venue_id}/Submission5/-/Fee_Waiver_Request',
            signatures=['~AuthorThree_ICMLTwentySeven1'],
            note=Note(
                content={
                    'low_income_economy': { 'value': 'No' },
                    'students_or_unaffiliated': { 'value': 'No' },
                    'no_payment_method': { 'value': 'No' }
                }
            )
        )
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])
        rejected_request_id = edit['note']['id']

        assert author_one_client.get_note(accepted_request_id).content['status']['value'] == 'Pending'
        assert author_three_client.get_note(rejected_request_id).content['status']['value'] == 'Pending'
        assert pc_client.get_payments(note=submissions[3].id) == []
        assert pc_client.get_payments(note=submissions[4].id) == []

        with pytest.raises(openreview.OpenReviewException, match=r'does not have permission to see Invitation NeurIPS.cc/2027/Conference/-/Fee_Waiver_Decision'):
            author_one_client.post_note_edit(
                invitation=f'{venue_id}/-/Fee_Waiver_Decision',
                signatures=[venue_id],
                note=Note(
                    id=accepted_request_id,
                    content={
                        'status': { 'value': 'Accepted' }
                    }
                )
            )

        edit = pc_client.post_note_edit(
            invitation=f'{venue_id}/-/Fee_Waiver_Decision',
            signatures=[venue_id],
            note=Note(
                id=accepted_request_id,
                content={
                    'status': { 'value': 'Accepted' }
                }
            )
        )
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        assert author_one_client.get_note(accepted_request_id).content['status']['value'] == 'Accepted'

        payments = author_three_client.get_payments(note=submissions[3].id)
        assert len(payments) == 1
        assert payments[0].status == 'waived'
        assert payments[0].amount == 2500
        assert payments[0].signature == support_group_id
        assert payments[0].invitations == [f'{venue_id}/Submission4/-/Submission_Fee_Payment']

        messages = openreview_client.get_messages(to='authorone@icml2027.cc', subject='[NeurIPS 2027] Your fee waiver request has been granted for submission number 4')
        assert len(messages) == 1

        edit = pc_client.post_note_edit(
            invitation=f'{venue_id}/-/Fee_Waiver_Decision',
            signatures=[venue_id],
            note=Note(
                id=rejected_request_id,
                content={
                    'status': { 'value': 'Rejected' }
                }
            )
        )
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])

        assert author_three_client.get_note(rejected_request_id).content['status']['value'] == 'Rejected'
        assert pc_client.get_payments(note=submissions[4].id) == []

        messages = openreview_client.get_messages(to='authorthree@icml2027.cc', subject='[NeurIPS 2027] Your fee waiver request has been rejected for submission number 5')
        assert len(messages) == 1
        assert 'The submission fee remains due.' in messages[0]['content']['text']
        assert messages[0]['content']['text'].count('Please note that responding to this email will direct your reply to neurips2027.programchairs@gmail.com.') == 1

    def test_payments_page(self, openreview_client, helpers):

        venue_id = self.venue_id

        author_one_client = openreview.api.OpenReviewClient(username='authorone@icml2027.cc', password=helpers.strong_password)
        author_three_client = openreview.api.OpenReviewClient(username='authorthree@icml2027.cc', password=helpers.strong_password)

        invitations = { i.id: i for i in author_three_client.get_invitations(invitee=True, type='payment', details='replytoNote,repliedPayments') if i.domain == venue_id }
        assert sorted(invitations.keys()) == [
            f'{venue_id}/Submission2/-/Submission_Fee_Payment',
            f'{venue_id}/Submission3/-/Submission_Fee_Payment',
            f'{venue_id}/Submission4/-/Submission_Fee_Payment',
            f'{venue_id}/Submission5/-/Submission_Fee_Payment'
        ]

        submission_two_fee = invitations[f'{venue_id}/Submission2/-/Submission_Fee_Payment']
        assert submission_two_fee.content['amount']['value'] == 2500
        assert submission_two_fee.details['replytoNote']['content']['title']['value'] == 'NeurIPS paper title 2'
        assert [(p['status'], p['amount'], p['signature']) for p in submission_two_fee.details['repliedPayments']] == [('pending', 3000, '~AuthorTwo_ICMLTwentySeven1')]

        assert [(p['status'], p['amount']) for p in invitations[f'{venue_id}/Submission3/-/Submission_Fee_Payment'].details['repliedPayments']] == [('expired', 2500)]
        assert [(p['status'], p['amount']) for p in invitations[f'{venue_id}/Submission4/-/Submission_Fee_Payment'].details['repliedPayments']] == [('waived', 2500)]
        assert invitations[f'{venue_id}/Submission5/-/Submission_Fee_Payment'].details['repliedPayments'] == []

        invitations = { i.id: i for i in author_one_client.get_invitations(invitee=True, type='payment', details='replytoNote,repliedPayments') if i.domain == venue_id }
        assert sorted(invitations.keys()) == [
            f'{venue_id}/Submission1/-/Submission_Fee_Payment',
            f'{venue_id}/Submission4/-/Submission_Fee_Payment'
        ]
        assert [(p['status'], p['amount'], p['signature']) for p in invitations[f'{venue_id}/Submission1/-/Submission_Fee_Payment'].details['repliedPayments']] == [('paid', 3000, '~AuthorOne_ICMLTwentySeven1')]
