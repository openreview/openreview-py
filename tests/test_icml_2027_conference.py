import pytest
import datetime
import openreview
from openreview.api import Note
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
        assert openreview.tools.get_invitation(openreview_client, f'{venue_id}/-/Fee_Waiver_Request') is None
        assert openreview.tools.get_invitation(openreview_client, f'{venue_id}/-/Fee_Waiver_Decision') is None
        assert openreview_client.get_invitation('openreview.net/Template/-/Submission_Fee_Payment')
        assert openreview_client.get_invitation('openreview.net/Template/-/Fee_Waiver_Request')
        assert openreview_client.get_invitation('openreview.net/Template/-/Fee_Waiver_Decision')

    def test_submit_abstracts(self, openreview_client, helpers):

        venue_id = self.venue_id

        author_one_client = helpers.create_user('authorone@icml2027.cc', 'AuthorOne', 'ICMLTwentySeven')
        author_two_client = helpers.create_user('authortwo@icml2027.cc', 'AuthorTwo', 'ICMLTwentySeven')
        author_three_client = helpers.create_user('authorthree@icml2027.cc', 'AuthorThree', 'ICMLTwentySeven')

        def post_submission(client, number, authors):
            return client.post_note_edit(
                invitation=f'{venue_id}/-/Submission',
                signatures=[authors[0]],
                note=openreview.api.Note(
                    license='CC BY 4.0',
                    content={
                        'title': { 'value': f'Paper title {number}' },
                        'abstract': { 'value': f'This is the abstract of submission {number}' },
                        'authors': {
                            'value': [
                                {
                                    'fullname': openreview.tools.pretty_id(author),
                                    'username': author,
                                    'institutions': [{ 'domain': 'icml2027.cc', 'country': 'US' }]
                                } for author in authors
                            ]
                        },
                        'keywords': { 'value': ['machine learning'] },
                        'email_sharing': { 'value': 'We authorize the sharing of all author emails with Program Chairs.' },
                        'data_release': { 'value': 'We authorize the release of our submission and author names to the public in the event of acceptance.' }
                    }
                )
            )

        ## abstracts only: the pdf is due at the full submission deadline
        post_submission(author_one_client, 1, ['~AuthorOne_ICMLTwentySeven1', '~AuthorTwo_ICMLTwentySeven1'])
        post_submission(author_two_client, 2, ['~AuthorTwo_ICMLTwentySeven1', '~AuthorThree_ICMLTwentySeven1'])
        post_submission(author_three_client, 3, ['~AuthorThree_ICMLTwentySeven1'])

        helpers.await_queue_edit(openreview_client, invitation=f'{venue_id}/-/Submission', count=3)

        submissions = openreview_client.get_notes(invitation=f'{venue_id}/-/Submission', sort='number:asc')
        assert len(submissions) == 3
        assert all('value' not in submission.content.get('pdf', {}) for submission in submissions)

        ## close the abstract deadline
        pc_client = openreview.api.OpenReviewClient(username='programchair@icml2027.cc', password=helpers.strong_password)
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
        assert submission_invitation.expdate == abstract_due_date + (30*60*1000)
        assert submission_invitation.expdate < openreview.tools.datetime_millis(datetime.datetime.now())

    def test_enable_submission_fee_payment(self, openreview_client, helpers):

        venue_id = self.venue_id
        support_group_id = openreview_client.get_group('openreview.net/Support').id

        now = datetime.datetime.now()
        payment_due_date = openreview.tools.datetime_millis(now + datetime.timedelta(weeks=2))
        payment_expiration_date = openreview.tools.datetime_millis(now + datetime.timedelta(weeks=2, minutes=30))

        ## support enables a fee of 20 USD per submission once the abstract deadline is over
        edit = openreview_client.post_invitation_edit(
            invitations='openreview.net/Template/-/Submission_Fee_Payment',
            signatures=[support_group_id],
            content={
                'venue_id': { 'value': venue_id },
                'name': { 'value': 'Submission_Fee_Payment' },
                'activation_date': { 'value': openreview.tools.datetime_millis(now) },
                'due_date': { 'value': payment_due_date },
                'expiration_date': { 'value': payment_expiration_date },
                'amount': { 'value': 2000 },
                'currency': { 'value': 'USD' },
                'submission_name': { 'value': 'Submission' }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])
        helpers.await_queue_edit(openreview_client, edit_id=f'{venue_id}/-/Submission_Fee_Payment-0-1', count=1)

        invitation = openreview_client.get_invitation(f'{venue_id}/-/Submission_Fee_Payment')
        assert invitation.domain == venue_id
        assert invitation.signatures == [venue_id]
        assert invitation.content['amount']['value'] == 2000
        assert invitation.content['currency']['value'] == 'USD'
        assert invitation.edit['invitation']['duedate'] == payment_due_date
        assert invitation.edit['invitation']['expdate'] == payment_expiration_date
        assert 'Submission fees are non-refundable.' in invitation.description
        assert 'do not desk reject the submissions with unpaid fees until 24 hours after the expiration date' in invitation.description

        dates_invitation = openreview_client.get_invitation(f'{venue_id}/-/Submission_Fee_Payment/Dates')
        assert list(dates_invitation.edit['content'].keys()) == ['activation_date', 'due_date', 'expiration_date']

        amount_invitation = openreview_client.get_invitation(f'{venue_id}/-/Submission_Fee_Payment/Amount')
        assert amount_invitation.signatures == [venue_id]
        assert amount_invitation.edit['signatures'] == [f'{venue_id}/Program_Chairs']
        assert list(amount_invitation.edit['content'].keys()) == ['amount']

        submissions = openreview_client.get_notes(invitation=f'{venue_id}/-/Submission', sort='number:asc')
        payment_invitations = openreview_client.get_all_invitations(invitation=f'{venue_id}/-/Submission_Fee_Payment')
        assert len(payment_invitations) == 3

        for submission in submissions:
            payment_invitation = openreview_client.get_invitation(f'{venue_id}/Submission{submission.number}/-/Submission_Fee_Payment')
            assert payment_invitation.signatures == [venue_id]
            assert payment_invitation.invitees == [f'{venue_id}/Submission{submission.number}/Authors', support_group_id]
            assert payment_invitation.duedate == payment_due_date
            assert payment_invitation.expdate == payment_expiration_date
            assert payment_invitation.description == 'Submission fees are non-refundable.'
            assert payment_invitation.content['amount']['value'] == 2000
            assert payment_invitation.content['currency']['value'] == 'USD'
            assert payment_invitation.edit['signature'] == { 'param': { 'const': support_group_id } }
            assert payment_invitation.edit['payment']['note'] == submission.id
            assert payment_invitation.edit['payment']['amount'] == { 'param': { 'minimum': 0 } }
            assert payment_invitation.edit['payment']['currency'] == 'USD'
            assert payment_invitation.edit['payment']['readers'] == [venue_id, f'{venue_id}/Submission{submission.number}/Authors', support_group_id]

        ## authors can see the fee of their submission only
        author_one_client = openreview.api.OpenReviewClient(username='authorone@icml2027.cc', password=helpers.strong_password)
        assert author_one_client.get_invitation(f'{venue_id}/Submission1/-/Submission_Fee_Payment').description == 'Submission fees are non-refundable.'
        with pytest.raises(openreview.OpenReviewException, match=r'Forbidden|NotFound|cannot read'):
            author_one_client.get_invitation(f'{venue_id}/Submission3/-/Submission_Fee_Payment')

        ## the forum page finds the fee of a submission in its forum
        forum_payment_invitations = author_one_client.get_invitations(replyForum=submissions[0].id, type='payment')
        assert [i.id for i in forum_payment_invitations] == [f'{venue_id}/Submission1/-/Submission_Fee_Payment']
        assert f'{venue_id}/Submission1/-/Submission_Fee_Payment' not in [i.id for i in author_one_client.get_invitations(replyForum=submissions[0].id, type='note')]

        ## and the payments page lists every fee an author is invited to pay
        author_two_client = openreview.api.OpenReviewClient(username='authortwo@icml2027.cc', password=helpers.strong_password)
        assert sorted([i.id for i in author_two_client.get_all_invitations(invitee=True, type='payment') if i.domain == venue_id]) == [
            f'{venue_id}/Submission1/-/Submission_Fee_Payment',
            f'{venue_id}/Submission2/-/Submission_Fee_Payment'
        ]

    def test_pay_submission_fee(self, openreview_client, helpers):

        venue_id = self.venue_id
        support_group_id = openreview_client.get_group('openreview.net/Support').id
        payment_invitation_id = f'{venue_id}/Submission1/-/Submission_Fee_Payment'

        author_one_client = openreview.api.OpenReviewClient(username='authorone@icml2027.cc', password=helpers.strong_password)
        author_two_client = openreview.api.OpenReviewClient(username='authortwo@icml2027.cc', password=helpers.strong_password)
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

    def test_enable_fee_waiver_request(self, openreview_client, helpers):

        venue_id = self.venue_id
        support_group_id = openreview_client.get_group('openreview.net/Support').id

        payment_invitation = openreview_client.get_invitation(f'{venue_id}/-/Submission_Fee_Payment')

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
        assert decision_invitation.domain == venue_id
        assert decision_invitation.signatures == [support_group_id]
        assert decision_invitation.writers == [support_group_id]
        assert decision_invitation.readers == [venue_id, support_group_id]
        assert decision_invitation.content['payment_name']['value'] == 'Submission_Fee_Payment'
        assert decision_invitation.content['request_name']['value'] == 'Fee_Waiver_Request'
        assert decision_invitation.edit['signatures'] == {
            'param': {
                'items': [
                    { 'value': venue_id, 'optional': True },
                    { 'value': support_group_id, 'optional': True }
                ]
            }
        }
        assert decision_invitation.edit['note']['id'] == { 'param': { 'withContent': { 'status': 'Pending' } } }
        assert decision_invitation.edit['note']['content']['status']['value']['param']['enum'] == ['Accepted', 'Rejected']

        edit = openreview_client.post_invitation_edit(
            invitations='openreview.net/Template/-/Fee_Waiver_Request',
            signatures=[support_group_id],
            content={
                'venue_id': { 'value': venue_id },
                'name': { 'value': 'Fee_Waiver_Request' },
                'activation_date': { 'value': openreview.tools.datetime_millis(datetime.datetime.now()) },
                'due_date': { 'value': payment_invitation.edit['invitation']['duedate'] },
                'expiration_date': { 'value': payment_invitation.edit['invitation']['expdate'] },
                'payment_name': { 'value': 'Submission_Fee_Payment' },
                'decision_name': { 'value': 'Fee_Waiver_Decision' },
                'auto_grant_waivers': { 'value': True },
                'submission_name': { 'value': 'Submission' }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])
        helpers.await_queue_edit(openreview_client, edit_id=f'{venue_id}/-/Fee_Waiver_Request-0-1', count=1)

        invitation = openreview_client.get_invitation(f'{venue_id}/-/Fee_Waiver_Request')
        assert invitation.signatures == [venue_id]
        assert invitation.content['auto_grant_waivers']['value'] == True
        assert invitation.content['payment_name']['value'] == 'Submission_Fee_Payment'
        assert invitation.content['decision_name']['value'] == 'Fee_Waiver_Decision'

        dates_invitation = openreview_client.get_invitation(f'{venue_id}/-/Fee_Waiver_Request/Dates')
        assert list(dates_invitation.edit['content'].keys()) == ['activation_date', 'due_date', 'expiration_date']

        waiver_invitations = openreview_client.get_all_invitations(invitation=f'{venue_id}/-/Fee_Waiver_Request')
        assert len(waiver_invitations) == 3

        waiver_invitation = openreview_client.get_invitation(f'{venue_id}/Submission2/-/Fee_Waiver_Request')
        assert waiver_invitation.signatures == [venue_id]
        assert waiver_invitation.invitees == [f'{venue_id}/Submission2/Authors']
        assert waiver_invitation.duedate == payment_invitation.edit['invitation']['duedate']
        assert waiver_invitation.expdate == payment_invitation.edit['invitation']['expdate']
        assert list(waiver_invitation.edit['note']['content'].keys()) == ['low_income_economy', 'students_or_unaffiliated', 'no_payment_method', 'status']
        assert waiver_invitation.edit['note']['content']['status'] == { 'value': 'Pending' }

        fee_invitations = [
            invitation,
            decision_invitation,
            payment_invitation,
            openreview_client.get_invitation(f'{venue_id}/-/Submission_Fee_Payment/Dates'),
            openreview_client.get_invitation(f'{venue_id}/-/Submission_Fee_Payment/Amount'),
            dates_invitation
        ] + waiver_invitations + openreview_client.get_all_invitations(invitation=f'{venue_id}/-/Submission_Fee_Payment')
        assert len(fee_invitations) == 12
        assert all('~Super_User1' not in fee_invitation.signatures for fee_invitation in fee_invitations)

    def test_request_fee_waiver(self, openreview_client, helpers):

        venue_id = self.venue_id
        support_group_id = openreview_client.get_group('openreview.net/Support').id

        author_two_client = openreview.api.OpenReviewClient(username='authortwo@icml2027.cc', password=helpers.strong_password)
        author_three_client = openreview.api.OpenReviewClient(username='authorthree@icml2027.cc', password=helpers.strong_password)
        pc_client = openreview.api.OpenReviewClient(username='programchair@icml2027.cc', password=helpers.strong_password)

        submission = openreview_client.get_notes(invitation=f'{venue_id}/-/Submission', number=2)[0]

        edit = author_two_client.post_note_edit(
            invitation=f'{venue_id}/Submission2/-/Fee_Waiver_Request',
            signatures=['~AuthorTwo_ICMLTwentySeven1'],
            note=Note(
                content={
                    'low_income_economy': { 'value': 'Yes' },
                    'students_or_unaffiliated': { 'value': 'No' },
                    'no_payment_method': { 'value': 'No' }
                }
            )
        )
        helpers.await_queue_edit(openreview_client, edit_id=edit['id'])
        helpers.await_queue_edit(openreview_client, invitation=f'{venue_id}/-/Fee_Waiver_Decision', count=1)

        ## the requesting author, the venue and support read the request, co-authors do not
        request = author_two_client.get_note(edit['note']['id'])
        assert request.forum == submission.id
        assert request.readers == [venue_id, support_group_id, '~AuthorTwo_ICMLTwentySeven1']
        assert request.content['status']['value'] == 'Accepted'
        assert request.invitations == [f'{venue_id}/Submission2/-/Fee_Waiver_Request', f'{venue_id}/-/Fee_Waiver_Decision']
        assert pc_client.get_note(request.id)
        with pytest.raises(openreview.OpenReviewException, match=r'Forbidden|NotFound|cannot read'):
            author_three_client.get_note(request.id)

        decision_edits = openreview_client.get_note_edits(note_id=request.id, invitation=f'{venue_id}/-/Fee_Waiver_Decision')
        assert len(decision_edits) == 1
        assert decision_edits[0].signatures == [venue_id]

        with pytest.raises(openreview.OpenReviewException, match=r'does not contain .*Pending.* in the status field'):
            pc_client.post_note_edit(
                invitation=f'{venue_id}/-/Fee_Waiver_Decision',
                signatures=[venue_id],
                note=Note(
                    id=request.id,
                    content={
                        'status': { 'value': 'Rejected' }
                    }
                )
            )

        other_pending_note_edit = pc_client.post_note_edit(
            invitation=f'{venue_id}/-/Edit',
            signatures=[venue_id],
            note=Note(
                forum=submission.id,
                replyto=submission.id,
                readers=[venue_id, support_group_id],
                writers=[venue_id],
                signatures=[venue_id],
                content={
                    'status': { 'value': 'Pending' }
                }
            )
        )

        with pytest.raises(openreview.OpenReviewException, match=r'is not a fee waiver request'):
            pc_client.post_note_edit(
                invitation=f'{venue_id}/-/Fee_Waiver_Decision',
                signatures=[venue_id],
                note=Note(
                    id=other_pending_note_edit['note']['id'],
                    content={
                        'status': { 'value': 'Accepted' }
                    }
                )
            )

        pc_client.post_note_edit(
            invitation=f'{venue_id}/-/Edit',
            signatures=[venue_id],
            note=Note(
                id=other_pending_note_edit['note']['id'],
                ddate=openreview.tools.datetime_millis(datetime.datetime.now())
            )
        )

        ## the pilot grants every request: the fee is settled with a waived payment of the fee
        payments = author_three_client.get_payments(note=submission.id)
        assert len(payments) == 1
        assert payments[0].status == 'waived'
        assert payments[0].amount == 2000
        assert payments[0].currency == 'USD'
        assert payments[0].signature == support_group_id
        assert payments[0].invitations[0] == f'{venue_id}/Submission2/-/Submission_Fee_Payment'
        assert not payments[0].transaction_id
        assert len(pc_client.get_payments(note=submission.id, status='waived')) == 1

        messages = openreview_client.get_messages(to='authortwo@icml2027.cc', subject='[ICML 2027] Your fee waiver request has been granted for submission number 2')
        assert len(messages) == 1
        assert 'Your request to waive the submission fee of your submission to ICML 2027 has been granted. No payment is due for this submission.' in messages[0]['content']['text']
        assert f'To view your submission, click here: https://openreview.net/forum?id={submission.id}' in messages[0]['content']['text']
        assert messages[0]['content']['text'].count('Please note that responding to this email will direct your reply to icml2027.programchairs@gmail.com.') == 1

        ## a waived fee can not be paid
        with pytest.raises(openreview.OpenReviewException, match=r'already settled'):
            author_three_client.checkout_payment(invitation=f'{venue_id}/Submission2/-/Submission_Fee_Payment', payment=Payment(note=submission.id))

        ## and needs no further waiver
        with pytest.raises(openreview.OpenReviewException, match=r'already waived, no waiver is needed'):
            author_three_client.post_note_edit(
                invitation=f'{venue_id}/Submission2/-/Fee_Waiver_Request',
                signatures=['~AuthorThree_ICMLTwentySeven1'],
                note=Note(
                    content={
                        'low_income_economy': { 'value': 'No' },
                        'students_or_unaffiliated': { 'value': 'No' },
                        'no_payment_method': { 'value': 'Yes' }
                    }
                )
            )

    def test_close_payments(self, openreview_client, helpers):

        venue_id = self.venue_id
        support_group_id = openreview_client.get_group('openreview.net/Support').id

        pc_client = openreview.api.OpenReviewClient(username='programchair@icml2027.cc', password=helpers.strong_password)
        author_one_client = openreview.api.OpenReviewClient(username='authorone@icml2027.cc', password=helpers.strong_password)
        author_three_client = openreview.api.OpenReviewClient(username='authorthree@icml2027.cc', password=helpers.strong_password)

        submissions = openreview_client.get_notes(invitation=f'{venue_id}/-/Submission', sort='number:asc')

        now = datetime.datetime.now()
        expiration_date = openreview.tools.datetime_millis(now - datetime.timedelta(minutes=30))

        pc_client.post_invitation_edit(
            invitations=f'{venue_id}/-/Submission_Fee_Payment/Dates',
            content={
                'activation_date': { 'value': openreview.tools.datetime_millis(now - datetime.timedelta(hours=2)) },
                'due_date': { 'value': openreview.tools.datetime_millis(now - datetime.timedelta(hours=1)) },
                'expiration_date': { 'value': expiration_date }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id=f'{venue_id}/-/Submission_Fee_Payment-0-1', count=2)

        assert openreview_client.get_invitation(f'{venue_id}/Submission3/-/Submission_Fee_Payment').expdate == expiration_date

        with pytest.raises(openreview.OpenReviewException, match=r'The Invitation ICML.cc/2027/Conference/Submission3/-/Submission_Fee_Payment has expired'):
            author_three_client.checkout_payment(invitation=f'{venue_id}/Submission3/-/Submission_Fee_Payment', payment=Payment(note=submissions[2].id))

        with pytest.raises(openreview.OpenReviewException, match=r'The payments of the submission fee are closed, a waiver can no longer be requested'):
            author_three_client.post_note_edit(
                invitation=f'{venue_id}/Submission3/-/Fee_Waiver_Request',
                signatures=['~AuthorThree_ICMLTwentySeven1'],
                note=Note(
                    content={
                        'low_income_economy': { 'value': 'No' },
                        'students_or_unaffiliated': { 'value': 'Yes' },
                        'no_payment_method': { 'value': 'No' }
                    }
                )
            )

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

        waiver_invitation = pc_client.get_invitation(f'{venue_id}/-/Fee_Waiver_Request')
        pc_client.post_invitation_edit(
            invitations=f'{venue_id}/-/Fee_Waiver_Request/Dates',
            content={
                'activation_date': { 'value': waiver_invitation.cdate },
                'due_date': { 'value': new_due_date },
                'expiration_date': { 'value': new_expiration_date }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id=f'{venue_id}/-/Fee_Waiver_Request-0-1', count=2)

        waiver_invitations = openreview_client.get_all_invitations(invitation=f'{venue_id}/-/Fee_Waiver_Request')
        assert len(waiver_invitations) == 3
        for waiver_invitation in waiver_invitations:
            assert waiver_invitation.signatures == [venue_id]
            assert waiver_invitation.duedate == new_due_date
            assert waiver_invitation.expdate == new_expiration_date

        with pytest.raises(openreview.OpenReviewException, match=r'already settled'):
            author_one_client.checkout_payment(invitation=f'{venue_id}/Submission1/-/Submission_Fee_Payment', payment=Payment(note=submission.id))

        with pytest.raises(openreview.OpenReviewException, match=r'already paid, no waiver is needed'):
            author_one_client.post_note_edit(
                invitation=f'{venue_id}/Submission1/-/Fee_Waiver_Request',
                signatures=['~AuthorOne_ICMLTwentySeven1'],
                note=Note(
                    content={
                        'low_income_economy': { 'value': 'No' },
                        'students_or_unaffiliated': { 'value': 'Yes' },
                        'no_payment_method': { 'value': 'No' }
                    }
                )
            )

    def test_unsettled_submissions(self, openreview_client, helpers):

        venue_id = self.venue_id

        pc_client = openreview.api.OpenReviewClient(username='programchair@icml2027.cc', password=helpers.strong_password)

        ## the venue sees every payment of its domain, which is all a payment report needs
        submissions = pc_client.get_all_notes(invitation=f'{venue_id}/-/Submission', sort='number:asc')
        payments = pc_client.get_all_payments(domain=venue_id)
        assert sorted([(p.note, p.status) for p in payments], key=lambda p: p[1]) == sorted([
            (submissions[0].id, 'expired'),
            (submissions[0].id, 'paid'),
            (submissions[1].id, 'waived')
        ], key=lambda p: p[1])

        settled = { p.note for p in payments if p.status in ['paid', 'waived'] }
        assert [s.number for s in submissions if s.id not in settled] == [3]

    def test_payments_page(self, openreview_client, helpers):

        venue_id = self.venue_id

        author_one_client = openreview.api.OpenReviewClient(username='authorone@icml2027.cc', password=helpers.strong_password)
        author_two_client = openreview.api.OpenReviewClient(username='authortwo@icml2027.cc', password=helpers.strong_password)

        ## one call gives the payments page every fee the author is invited to pay, its submission and its payments
        invitations = { i.id: i for i in author_two_client.get_invitations(invitee=True, type='payment', details='replytoNote,repliedPayments') if i.domain == venue_id }
        assert sorted(invitations.keys()) == [f'{venue_id}/Submission1/-/Submission_Fee_Payment', f'{venue_id}/Submission2/-/Submission_Fee_Payment']

        submission_one_fee = invitations[f'{venue_id}/Submission1/-/Submission_Fee_Payment']
        assert submission_one_fee.description == 'Submission fees are non-refundable.'
        assert submission_one_fee.details['replytoNote']['content']['title']['value'] == 'Paper title 1'
        assert sorted([p['status'] for p in submission_one_fee.details['repliedPayments']]) == ['expired', 'paid']

        submission_two_fee = invitations[f'{venue_id}/Submission2/-/Submission_Fee_Payment']
        assert submission_two_fee.details['replytoNote']['content']['title']['value'] == 'Paper title 2'
        assert [(p['status'], p['amount']) for p in submission_two_fee.details['repliedPayments']] == [('waived', 2000)]

        ## each author only gets the fees of their own submissions
        invitations = [i for i in author_one_client.get_invitations(invitee=True, type='payment', details='replytoNote,repliedPayments') if i.domain == venue_id]
        assert [i.id for i in invitations] == [f'{venue_id}/Submission1/-/Submission_Fee_Payment']
        assert len(invitations[0].details['repliedPayments']) == 2
