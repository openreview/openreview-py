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
        assert openreview_client.get_invitation('openreview.net/Template/-/Submission_Fee_Payment')
        assert openreview_client.get_invitation('openreview.net/Template/-/Fee_Waiver_Request')

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

        ## support enables a fee of 20 USD per submission once the abstract deadline is over
        edit = openreview_client.post_invitation_edit(
            invitations='openreview.net/Template/-/Submission_Fee_Payment',
            signatures=[support_group_id],
            content={
                'venue_id': { 'value': venue_id },
                'name': { 'value': 'Submission_Fee_Payment' },
                'activation_date': { 'value': openreview.tools.datetime_millis(now) },
                'due_date': { 'value': payment_due_date },
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
        assert openreview_client.get_invitation(f'{venue_id}/-/Submission_Fee_Payment/Dates')

        submissions = openreview_client.get_notes(invitation=f'{venue_id}/-/Submission', sort='number:asc')
        payment_invitations = openreview_client.get_all_invitations(invitation=f'{venue_id}/-/Submission_Fee_Payment')
        assert len(payment_invitations) == 3

        for submission in submissions:
            payment_invitation = openreview_client.get_invitation(f'{venue_id}/Submission{submission.number}/-/Submission_Fee_Payment')
            assert payment_invitation.signatures == [venue_id]
            assert payment_invitation.invitees == [f'{venue_id}/Submission{submission.number}/Authors', support_group_id]
            assert payment_invitation.duedate == payment_due_date
            assert payment_invitation.content['amount']['value'] == 2000
            assert payment_invitation.content['currency']['value'] == 'USD'
            assert payment_invitation.edit['signature'] == { 'param': { 'const': support_group_id } }
            assert payment_invitation.edit['payment']['note'] == submission.id
            assert payment_invitation.edit['payment']['amount'] == 2000
            assert payment_invitation.edit['payment']['currency'] == 'USD'
            assert payment_invitation.edit['payment']['readers'] == [venue_id, f'{venue_id}/Submission{submission.number}/Authors', support_group_id]

        ## authors can see the fee of their submission only
        author_one_client = openreview.api.OpenReviewClient(username='authorone@icml2027.cc', password=helpers.strong_password)
        assert author_one_client.get_invitation(f'{venue_id}/Submission1/-/Submission_Fee_Payment')
        with pytest.raises(openreview.OpenReviewException, match=r'Forbidden|NotFound|cannot read'):
            author_one_client.get_invitation(f'{venue_id}/Submission3/-/Submission_Fee_Payment')

        ## the forum page finds the fee of a submission in its forum
        forum_payment_invitations = author_one_client.get_invitations(replyForum=submissions[0].id, type='payment')
        assert [i.id for i in forum_payment_invitations] == [f'{venue_id}/Submission1/-/Submission_Fee_Payment']
        assert f'{venue_id}/Submission1/-/Submission_Fee_Payment' not in [i.id for i in author_one_client.get_invitations(replyForum=submissions[0].id, type='note')]

        ## and the payments page lists every fee an author is invited to pay
        author_two_client = openreview.api.OpenReviewClient(username='authortwo@icml2027.cc', password=helpers.strong_password)
        assert sorted([i.id for i in author_two_client.get_all_invitations(invitee=True, type='payment')]) == [
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
                payment=Payment(note=submission.id, amount=2000, currency='USD', status='paid', signatures=['~AuthorOne_ICMLTwentySeven1'])
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
        assert payments[0].signatures == ['~AuthorOne_ICMLTwentySeven1']
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
        assert payment.signatures == ['~AuthorTwo_ICMLTwentySeven1']

        assert sorted([p.status for p in pc_client.get_payments(note=submission.id)]) == ['expired', 'pending']

    def test_enable_fee_waiver_request(self, openreview_client, helpers):

        venue_id = self.venue_id
        support_group_id = openreview_client.get_group('openreview.net/Support').id

        payment_invitation = openreview_client.get_invitation(f'{venue_id}/-/Submission_Fee_Payment')

        edit = openreview_client.post_invitation_edit(
            invitations='openreview.net/Template/-/Fee_Waiver_Request',
            signatures=[support_group_id],
            content={
                'venue_id': { 'value': venue_id },
                'name': { 'value': 'Fee_Waiver_Request' },
                'activation_date': { 'value': openreview.tools.datetime_millis(datetime.datetime.now()) },
                'due_date': { 'value': payment_invitation.edit['invitation']['duedate'] },
                'payment_name': { 'value': 'Submission_Fee_Payment' },
                'auto_grant_waivers': { 'value': True },
                'submission_name': { 'value': 'Submission' }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id=f'{venue_id}/-/Fee_Waiver_Request-0-1', count=1)

        ## signed by the super user: the waiver process reads the submissions and posts waived payments
        invitation = openreview_client.get_invitation(f'{venue_id}/-/Fee_Waiver_Request')
        assert invitation.signatures == ['~Super_User1']
        assert invitation.content['auto_grant_waivers']['value'] == True
        assert invitation.content['payment_name']['value'] == 'Submission_Fee_Payment'

        waiver_invitations = openreview_client.get_all_invitations(invitation=f'{venue_id}/-/Fee_Waiver_Request')
        assert len(waiver_invitations) == 3

        waiver_invitation = openreview_client.get_invitation(f'{venue_id}/Submission2/-/Fee_Waiver_Request')
        assert waiver_invitation.signatures == ['~Super_User1']
        assert waiver_invitation.invitees == [f'{venue_id}/Submission2/Authors']
        assert waiver_invitation.duedate == payment_invitation.edit['invitation']['duedate']
        assert list(waiver_invitation.edit['note']['content'].keys()) == ['low_income_economy', 'students_or_unaffiliated', 'no_payment_method']

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

        ## the requesting author, the venue and support read the request, co-authors do not
        request = author_two_client.get_note(edit['note']['id'])
        assert request.forum == submission.id
        assert request.readers == [venue_id, support_group_id, '~AuthorTwo_ICMLTwentySeven1']
        assert pc_client.get_note(request.id)
        with pytest.raises(openreview.OpenReviewException, match=r'Forbidden|NotFound|cannot read'):
            author_three_client.get_note(request.id)

        ## the pilot grants every request: the fee is settled with a waived payment of the fee
        payments = author_three_client.get_payments(note=submission.id)
        assert len(payments) == 1
        assert payments[0].status == 'waived'
        assert payments[0].amount == 2000
        assert payments[0].currency == 'USD'
        assert payments[0].signatures == [support_group_id]
        assert payments[0].invitations[0] == f'{venue_id}/Submission2/-/Submission_Fee_Payment'
        assert not payments[0].transaction_id
        assert len(pc_client.get_payments(note=submission.id, status='waived')) == 1

        messages = openreview_client.get_messages(to='authortwo@icml2027.cc', subject='[ICML 2027] Your fee waiver request has been granted for submission number 2')
        assert len(messages) == 1

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

    def test_extend_payment_due_date(self, openreview_client, helpers):

        venue_id = self.venue_id
        support_group_id = openreview_client.get_group('openreview.net/Support').id

        pc_client = openreview.api.OpenReviewClient(username='programchair@icml2027.cc', password=helpers.strong_password)

        invitation = pc_client.get_invitation(f'{venue_id}/-/Submission_Fee_Payment')
        new_due_date = invitation.edit['invitation']['duedate'] + (7*24*60*60*1000)

        edit = pc_client.post_invitation_edit(
            invitations=f'{venue_id}/-/Submission_Fee_Payment/Dates',
            content={
                'activation_date': { 'value': invitation.cdate },
                'due_date': { 'value': new_due_date }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id=f'{venue_id}/-/Submission_Fee_Payment-0-1', count=2)

        invitation = openreview_client.get_invitation(f'{venue_id}/-/Submission_Fee_Payment')
        assert invitation.edit['invitation']['duedate'] == new_due_date

        ## payments are still posted by support only, whoever signs the invitations
        for payment_invitation in openreview_client.get_all_invitations(invitation=f'{venue_id}/-/Submission_Fee_Payment'):
            assert payment_invitation.duedate == new_due_date
            assert payment_invitation.edit['signature'] == { 'param': { 'const': support_group_id } }

    def test_unsettled_submissions(self, openreview_client, helpers):

        venue_id = self.venue_id

        pc_client = openreview.api.OpenReviewClient(username='programchair@icml2027.cc', password=helpers.strong_password)

        ## the venue sees every payment of its domain, which is all a payment report needs
        submissions = pc_client.get_all_notes(invitation=f'{venue_id}/-/Submission', sort='number:asc')
        payments = pc_client.get_all_payments(domain=venue_id)
        assert sorted([(p.note, p.status) for p in payments], key=lambda p: p[1]) == sorted([
            (submissions[0].id, 'expired'),
            (submissions[0].id, 'pending'),
            (submissions[1].id, 'waived')
        ], key=lambda p: p[1])

        settled = { p.note for p in payments if p.status in ['paid', 'waived'] }
        assert [s.number for s in submissions if s.id not in settled] == [1, 3]
