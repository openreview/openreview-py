import time
import datetime
import pytest
import openreview


class TestProfileVouching():

    @pytest.fixture(scope='class')
    def support_client(self, openreview_client, helpers):
        support_client = helpers.create_user('nora.brennan@support.org', 'Nora', 'Brennan', alternates=[], institution='openreview.net')
        openreview_client.post_group_edit(
            invitation='openreview.net/-/Edit',
            signatures=['openreview.net'],
            group=openreview.api.Group(
                id='openreview.net/Support',
                members={ 'append': ['~Nora_Brennan1'] }
            )
        )
        return support_client

    def test_vouch_invitations(self, openreview_client):

        request_invitation = openreview_client.get_invitation('openreview.net/Support/-/Vouch_Request')
        assert request_invitation.guestPosting
        assert request_invitation.secret
        assert request_invitation.content['linkExpirationDays']['value'] == 30
        assert request_invitation.content['requestExpirationDays']['value'] == 30
        assert request_invitation.content['maxOpenRequests']['value'] == 3
        assert "component: 'VouchRequestForm'" in request_invitation.web

        assert list(request_invitation.edit['note']['content'].keys()) == ['voucher']
        assert request_invitation.edit['note']['content']['voucher']['value']['param']['regex'] == r'^~\S+\d+$'

        verification_invitation = openreview_client.get_invitation('openreview.net/Support/-/Vouch_Verification')
        assert verification_invitation.content['lifetimeLimit']['value'] == 20
        assert verification_invitation.content['monthLimit']['value'] == 5
        assert verification_invitation.edit['content']['homepage']['value']['param']['optional']
        assert verification_invitation.edit['content']['email']['value']['param']['type'] == 'string'
        assert verification_invitation.edit['invitation']['content']['email']['readers'] == ['openreview.net/Support', '${5/content/vouchee/value}']
        assert verification_invitation.edit['invitation']['assertion']['content']['confirmations']['value']['param']['enum'] == [
            'I know this person, and the information above is correct.',
            'This vouch will be public on my profile and on theirs.',
            'I cannot delete this vouch after I post it.'
        ]

    def test_request_vouch(self, openreview_client, support_client, helpers):

        config_note = openreview_client.get_notes(invitation='openreview.net/-/OpenReview_Config')[0]
        support_client.post_note_edit(
            invitation='openreview.net/-/OpenReview_Config',
            signatures=['openreview.net/Support'],
            note=openreview.api.Note(
                id=config_note.id,
                content={
                    'moderate': { 'value': 'Yes' },
                    'weekend_moderation': { 'value': 'Yes' }
                }
            )
        )

        helpers.create_user('elena.rossi@umass.edu', 'Elena', 'Rossi', institution='umass.edu')
        assert openreview_client.get_profile('~Elena_Rossi1').state == 'Active Institutional'

        guest_client = openreview.api.OpenReviewClient(baseurl='http://localhost:3001')

        guest_client.register_user(email='daniel.okafor@gmail.com', fullname='Daniel Okafor', password=helpers.strong_password, dob=helpers.default_dob())
        guest_client.activate_user('daniel.okafor@gmail.com', {
            'names': [{ 'fullname': 'Daniel Okafor', 'preferred': True }],
            'emails': ['daniel.okafor@gmail.com'],
            'preferredEmail': 'daniel.okafor@gmail.com',
            'homepage': f'https://danielokafor{int(time.time())}.openreview.net',
            'dob': helpers.default_dob(),
            'history': [{
                'position': 'Research Engineer',
                'start': 2021,
                'end': None,
                'institution': { 'country': 'US', 'domain': 'smalllab.org', 'name': 'Small Lab' }
            }]
        })
        assert openreview_client.get_profile('~Daniel_Okafor1').state == 'Needs Moderation'

        support_client.moderate_profile('~Daniel_Okafor1', 'reject', 'Please ask a colleague to vouch for you.', labels=['Request supervisor or coauthor to vouch'])
        assert openreview_client.get_profile('~Daniel_Okafor1').state == 'Rejected'

        guest_client.register_user(email='priya.raman@gmail.com', fullname='Priya Raman', password=helpers.strong_password, dob=helpers.default_dob())
        guest_client.activate_user('priya.raman@gmail.com', {
            'names': [{ 'fullname': 'Priya Raman', 'preferred': True }],
            'emails': ['priya.raman@gmail.com'],
            'preferredEmail': 'priya.raman@gmail.com',
            'homepage': f'https://priyaraman{int(time.time())}.openreview.net',
            'dob': helpers.default_dob(),
            'history': [{
                'position': 'Research Engineer',
                'start': 2021,
                'end': None,
                'institution': { 'country': 'US', 'domain': 'smalllab.org', 'name': 'Small Lab' }
            }]
        })
        assert openreview_client.get_profile('~Priya_Raman1').state == 'Needs Moderation'

        request_invitation = openreview_client.get_invitation('openreview.net/Support/-/Vouch_Request')
        token = openreview.tools.get_user_hash_key('~Daniel_Okafor1', request_invitation.secret, invitation='openreview.net/Support/-/Vouch_Request', expires_in=3600)
        expired_token = openreview.tools.get_user_hash_key('~Daniel_Okafor1', request_invitation.secret, invitation='openreview.net/Support/-/Vouch_Request', expires_in=-60)

        with pytest.raises(openreview.OpenReviewException):
            guest_client.post_note_edit_as_guest(expired_token, {
                'invitation': 'openreview.net/Support/-/Vouch_Request',
                'signatures': ['~Daniel_Okafor1'],
                'note': { 'content': { 'voucher': { 'value': '~Elena_Rossi1' } } }
            })

        with pytest.raises(openreview.OpenReviewException):
            guest_client.post_note_edit_as_guest(token, {
                'invitation': 'openreview.net/Support/-/Vouch_Request',
                'signatures': ['~Elena_Rossi1'],
                'note': { 'content': { 'voucher': { 'value': '~Elena_Rossi1' } } }
            })

        with pytest.raises(openreview.OpenReviewException):
            guest_client.post_note_edit_as_guest(token, {
                'invitation': 'openreview.net/Support/-/Vouch_Request',
                'signatures': ['~Daniel_Okafor1'],
                'note': { 'content': { 'voucher': { 'value': 'elena.rossi@umass.edu' } } }
            })

        with pytest.raises(openreview.OpenReviewException, match=r'cannot ask yourself'):
            guest_client.post_note_edit_as_guest(token, {
                'invitation': 'openreview.net/Support/-/Vouch_Request',
                'signatures': ['~Daniel_Okafor1'],
                'note': { 'content': { 'voucher': { 'value': '~Daniel_Okafor1' } } }
            })

        with pytest.raises(openreview.OpenReviewException):
            guest_client.post_note_edit_as_guest(token, {
                'invitation': 'openreview.net/Support/-/Profile_Merge',
                'signatures': ['~Daniel_Okafor1'],
                'note': { 'content': { 'left': { 'value': '~Daniel_Okafor1' }, 'right': { 'value': '~Priya_Raman1' } } }
            })

        assert openreview_client.get_notes(invitation='openreview.net/Support/-/Vouch_Request') == []

        request_edit = guest_client.post_note_edit_as_guest(token, {
            'invitation': 'openreview.net/Support/-/Vouch_Request',
            'signatures': ['~Daniel_Okafor1'],
            'note': { 'content': { 'voucher': { 'value': '~Elena_Rossi1' } } }
        })
        assert request_edit['note']['number'] == 1
        helpers.await_queue_edit(openreview_client, edit_id=request_edit['id'])

        requests = openreview_client.get_notes(invitation='openreview.net/Support/-/Vouch_Request')
        assert len(requests) == 1
        request = requests[0]
        assert request.number == 1
        assert request.signatures == ['~Daniel_Okafor1']
        assert request.readers == ['openreview.net/Support', '~Daniel_Okafor1', '~Elena_Rossi1']
        assert request.content['voucher']['value'] == '~Elena_Rossi1'

        vouch_invitation = openreview_client.get_invitation('openreview.net/Support/Vouch_Request1/-/Vouch_Verification')
        assert vouch_invitation.invitees == ['~Elena_Rossi1']
        assert vouch_invitation.readers == ['openreview.net/Support', '~Daniel_Okafor1', '~Elena_Rossi1']
        assert vouch_invitation.expdate == request.cdate + 30 * 24 * 60 * 60 * 1000
        assert vouch_invitation.assertion['profile']['id'] == '~Daniel_Okafor1'
        assert vouch_invitation.assertion['signatures'] == ['~Elena_Rossi1']
        assert "component: 'VouchVerificationForm'" in vouch_invitation.web
        assert vouch_invitation.assertion['profile']['content']['names']['value']['const']['add'] == [{ 'fullname': 'Daniel Okafor', 'username': '~Daniel_Okafor1' }]
        assert len(vouch_invitation.assertion['profile']['content']['history']['value']['const']['add']) == 1
        assert vouch_invitation.assertion['profile']['content']['history']['value']['const']['add'][0]['position'] == 'Research Engineer'
        assert vouch_invitation.assertion['profile']['content']['history']['value']['const']['add'][0]['institution']['domain'] == 'smalllab.org'
        assert vouch_invitation.assertion['profile']['content']['homepage']['value'] == openreview_client.get_profile('~Daniel_Okafor1').content['homepage']
        assert len(vouch_invitation.assertion['content']['confirmations']['value']['param']['enum']) == 3
        assert vouch_invitation.content['email'] == { 'value': 'daniel.okafor@gmail.com', 'readers': ['openreview.net/Support', '~Daniel_Okafor1'] }
        assert vouch_invitation.assertion['profile']['content']['emails']['value']['param']['change'] == 'add'

        assert openreview_client.get_messages(to='daniel.okafor@gmail.com', subject='Your vouch request link') == []

        voucher_client = helpers.get_user('elena.rossi@umass.edu')
        voucher_requests = voucher_client.get_notes(invitation='openreview.net/Support/-/Vouch_Request')
        assert len(voucher_requests) == 1
        voucher_invitation = voucher_client.get_invitation('openreview.net/Support/Vouch_Request1/-/Vouch_Verification')
        assert 'email' not in (voucher_invitation.content or {})
        assert 'daniel.okafor@gmail.com' not in str(voucher_invitation.to_json())

        bystander_client = helpers.create_user('tomas.varga@umass.edu', 'Tomas', 'Varga', institution='umass.edu')
        assert bystander_client.get_notes(invitation='openreview.net/Support/-/Vouch_Request') == []
        with pytest.raises(openreview.OpenReviewException):
            bystander_client.get_invitation('openreview.net/Support/Vouch_Request1/-/Vouch_Verification')

        request_edit = guest_client.post_note_edit_as_guest(token, {
            'invitation': 'openreview.net/Support/-/Vouch_Request',
            'signatures': ['~Daniel_Okafor1'],
            'note': { 'content': { 'voucher': { 'value': '~Nobody_Here1' } } }
        })
        assert request_edit['note']['number'] == 2
        helpers.await_queue_edit(openreview_client, edit_id=request_edit['id'])
        assert openreview.tools.get_invitation(openreview_client, 'openreview.net/Support/Vouch_Request2/-/Vouch_Verification') is None

    def test_vouch_for_rejected_profile(self, openreview_client, support_client, helpers):

        voucher_client = helpers.get_user('elena.rossi@umass.edu')
        bystander_client = helpers.get_user('tomas.varga@umass.edu')
        guest_client = openreview.api.OpenReviewClient(baseurl='http://localhost:3001')
        statements = openreview_client.get_invitation('openreview.net/Support/Vouch_Request1/-/Vouch_Verification').assertion['content']['confirmations']['value']['param']['enum']

        with pytest.raises(openreview.OpenReviewException):
            bystander_client.post_profile_assertion(
                invitation='openreview.net/Support/Vouch_Request1/-/Vouch_Verification',
                signatures=['~Tomas_Varga1'],
                content={ 'confirmations': { 'value': statements } },
                profile={
                    'id': '~Daniel_Okafor1',
                    'content': { 'emails': { 'value': { 'add': ['daniel.okafor@gmail.com'] } } }
                }
            )

        with pytest.raises(openreview.OpenReviewException, match=r'Check every statement to confirm the vouch'):
            voucher_client.post_profile_assertion(
                invitation='openreview.net/Support/Vouch_Request1/-/Vouch_Verification',
                signatures=['~Elena_Rossi1'],
                content={ 'confirmations': { 'value': statements[:2] } },
                profile={
                    'id': '~Daniel_Okafor1',
                    'content': { 'emails': { 'value': { 'add': ['daniel.okafor@gmail.com'] } } }
                }
            )

        with pytest.raises(openreview.OpenReviewException, match=r'This email address does not match their OpenReview profile'):
            voucher_client.post_profile_assertion(
                invitation='openreview.net/Support/Vouch_Request1/-/Vouch_Verification',
                signatures=['~Elena_Rossi1'],
                content={ 'confirmations': { 'value': statements } },
                profile={
                    'id': '~Daniel_Okafor1',
                    'content': { 'emails': { 'value': { 'add': ['dan.okafor@gmail.com'] } } }
                }
            )

        with pytest.raises(openreview.OpenReviewException, match=r'This email address does not match their OpenReview profile'):
            voucher_client.post_profile_assertion(
                invitation='openreview.net/Support/Vouch_Request1/-/Vouch_Verification',
                signatures=['~Elena_Rossi1'],
                content={ 'confirmations': { 'value': statements } },
                profile={
                    'id': '~Daniel_Okafor1',
                    'content': { 'emails': { 'value': { 'add': ['dan.okafor@gmail.com', 'daniel.okafor@gmail.com'] } } }
                }
            )

        daniel = openreview_client.get_profile('~Daniel_Okafor1')
        new_homepage = f'https://danielokafor-lab{int(time.time())}.openreview.net'
        guest_client.activate_user('daniel.okafor@gmail.com', {
            'names': [{ 'fullname': 'Daniel Okafor', 'username': '~Daniel_Okafor1', 'preferred': True }],
            'emails': ['daniel.okafor@gmail.com'],
            'preferredEmail': 'daniel.okafor@gmail.com',
            'homepage': new_homepage,
            'history': daniel.content['history']
        })
        assert openreview_client.get_profile('~Daniel_Okafor1').content['homepage'] == new_homepage
        assert openreview_client.get_profile('~Daniel_Okafor1').state == 'Needs Moderation'

        with pytest.raises(openreview.OpenReviewException, match=r'The profile changed since this vouch was requested'):
            voucher_client.post_profile_assertion(
                invitation='openreview.net/Support/Vouch_Request1/-/Vouch_Verification',
                signatures=['~Elena_Rossi1'],
                content={ 'confirmations': { 'value': statements } },
                profile={
                    'id': '~Daniel_Okafor1',
                    'content': { 'emails': { 'value': { 'add': ['daniel.okafor@gmail.com'] } } }
                }
            )

        request_invitation = openreview_client.get_invitation('openreview.net/Support/-/Vouch_Request')
        token = openreview.tools.get_user_hash_key('~Daniel_Okafor1', request_invitation.secret, invitation='openreview.net/Support/-/Vouch_Request', expires_in=3600)

        request_edit = guest_client.post_note_edit_as_guest(token, {
            'invitation': 'openreview.net/Support/-/Vouch_Request',
            'signatures': ['~Daniel_Okafor1'],
            'note': { 'content': { 'voucher': { 'value': '~Elena_Rossi1' } } }
        })
        assert request_edit['note']['number'] == 3
        helpers.await_queue_edit(openreview_client, edit_id=request_edit['id'])

        assert openreview_client.get_invitation('openreview.net/Support/Vouch_Request1/-/Vouch_Verification').expdate <= openreview.tools.datetime_millis(datetime.datetime.now())
        vouch_invitation = openreview_client.get_invitation('openreview.net/Support/Vouch_Request3/-/Vouch_Verification')
        assert vouch_invitation.invitees == ['~Elena_Rossi1']
        assert vouch_invitation.assertion['profile']['content']['homepage']['value'] == new_homepage

        request_edit = guest_client.post_note_edit_as_guest(token, {
            'invitation': 'openreview.net/Support/-/Vouch_Request',
            'signatures': ['~Daniel_Okafor1'],
            'note': { 'content': { 'voucher': { 'value': '~Tomas_Varga1' } } }
        })
        assert request_edit['note']['number'] == 4
        helpers.await_queue_edit(openreview_client, edit_id=request_edit['id'])
        assert openreview_client.get_invitation('openreview.net/Support/Vouch_Request3/-/Vouch_Verification').expdate > openreview.tools.datetime_millis(datetime.datetime.now())

        with pytest.raises(openreview.OpenReviewException):
            voucher_client.post_profile_assertion(
                invitation='openreview.net/Support/Vouch_Request1/-/Vouch_Verification',
                signatures=['~Elena_Rossi1'],
                content={ 'confirmations': { 'value': statements } },
                profile={
                    'id': '~Daniel_Okafor1',
                    'content': { 'emails': { 'value': { 'add': ['daniel.okafor@gmail.com'] } } }
                }
            )

        assert openreview_client.get_profile_assertions(profile_id='~Daniel_Okafor1', invitation='openreview.net/Support/Vouch_Request3/-/Vouch_Verification') == []
        assert openreview_client.get_profile('~Daniel_Okafor1').state == 'Needs Moderation'

        vouch = voucher_client.post_profile_assertion(
            invitation='openreview.net/Support/Vouch_Request3/-/Vouch_Verification',
            signatures=['~Elena_Rossi1'],
            content={ 'confirmations': { 'value': statements } },
            profile={
                'id': '~Daniel_Okafor1',
                'content': { 'emails': { 'value': { 'add': ['daniel.okafor@gmail.com'] } } }
            }
        )
        assert vouch['readers'] == ['everyone']
        helpers.await_queue_edit(openreview_client, edit_id=vouch['id'])

        assert openreview_client.get_profile('~Daniel_Okafor1').state == 'Active'

        states = openreview_client.get_profile_assertions(profile_id='~Daniel_Okafor1', invitation='openreview.net/Support/-/Profile_State')
        latest_state = max(states, key=lambda state: state.tcdate)
        assert latest_state.profile['state'] == 'Active'

        vouches = guest_client.get_profile_assertions(profile_id='~Daniel_Okafor1', invitation='openreview.net/Support/Vouch_Request3/-/Vouch_Verification')
        assert len(vouches) == 1
        assert vouches[0].signatures == ['~Elena_Rossi1']
        assert vouches[0].content['confirmations']['value'] == statements
        assert vouches[0].profile['content']['names']['value']['add'] == [{ 'fullname': 'Daniel Okafor', 'username': '~Daniel_Okafor1' }]
        assert vouches[0].profile['content']['history']['value']['add'][0]['institution']['domain'] == 'smalllab.org'
        assert vouches[0].profile['content']['homepage']['value'] == new_homepage
        assert 'emails' not in vouches[0].profile['content']

        vouches = bystander_client.get_profile_assertions(profile_id='~Daniel_Okafor1', invitation='openreview.net/Support/Vouch_Request3/-/Vouch_Verification')
        assert len(vouches) == 1
        assert 'emails' not in vouches[0].profile['content']

        vouches = voucher_client.get_profile_assertions(profile_id='~Daniel_Okafor1', invitation='openreview.net/Support/Vouch_Request3/-/Vouch_Verification')
        assert vouches[0].profile['content']['emails']['value']['add'] == ['daniel.okafor@gmail.com']

        vouchee_client = helpers.get_user('daniel.okafor@gmail.com')
        vouches = vouchee_client.get_profile_assertions(profile_id='~Daniel_Okafor1', invitation='openreview.net/Support/Vouch_Request3/-/Vouch_Verification')
        assert vouches[0].profile['content']['emails']['value']['add'] == ['daniel.okafor@gmail.com']

        vouches = support_client.get_profile_assertions(profile_id='~Daniel_Okafor1', invitation='openreview.net/Support/Vouch_Request3/-/Vouch_Verification')
        assert vouches[0].profile['content']['emails']['value']['add'] == ['daniel.okafor@gmail.com']

        vouches = guest_client.get_profile_assertions(domain='openreview.net', signatures=['~Elena_Rossi1'])
        assert [vouch.invitation for vouch in vouches] == ['openreview.net/Support/Vouch_Request3/-/Vouch_Verification']
        assert vouches[0].profile['id'] == '~Daniel_Okafor1'

        with pytest.raises(openreview.OpenReviewException, match=r'You already vouched for ~Daniel_Okafor1'):
            voucher_client.post_profile_assertion(
                invitation='openreview.net/Support/Vouch_Request3/-/Vouch_Verification',
                signatures=['~Elena_Rossi1'],
                content={ 'confirmations': { 'value': statements } },
                profile={
                    'id': '~Daniel_Okafor1',
                    'content': { 'emails': { 'value': { 'add': ['daniel.okafor@gmail.com'] } } }
                }
            )

        vouch = bystander_client.post_profile_assertion(
            invitation='openreview.net/Support/Vouch_Request4/-/Vouch_Verification',
            signatures=['~Tomas_Varga1'],
            content={ 'confirmations': { 'value': statements } },
            profile={
                'id': '~Daniel_Okafor1',
                'content': { 'emails': { 'value': { 'add': ['daniel.okafor@gmail.com'] } } }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id=vouch['id'])

        assert openreview_client.get_profile('~Daniel_Okafor1').state == 'Active'
        assert len(openreview_client.get_profile_assertions(profile_id='~Daniel_Okafor1', invitation='openreview.net/Support/-/Profile_State')) == len(states)
        vouches = guest_client.get_profile_assertions(profile_id='~Daniel_Okafor1')
        assert sorted(vouch.signatures[0] for vouch in vouches if vouch.invitation.endswith('/-/Vouch_Verification')) == ['~Elena_Rossi1', '~Tomas_Varga1']

    def test_vouch_for_independent_researcher_in_moderation(self, openreview_client, support_client, helpers):

        guest_client = openreview.api.OpenReviewClient(baseurl='http://localhost:3001')

        guest_client.register_user(email='lena.fischer@gmail.com', fullname='Lena Fischer', password=helpers.strong_password, dob=helpers.default_dob())
        guest_client.activate_user('lena.fischer@gmail.com', {
            'names': [{ 'fullname': 'Lena Fischer', 'preferred': True }],
            'emails': ['lena.fischer@gmail.com'],
            'preferredEmail': 'lena.fischer@gmail.com',
            'homepage': f'https://lenafischer{int(time.time())}.openreview.net',
            'dob': helpers.default_dob(),
            'history': [
                {
                    'position': 'Independent Researcher',
                    'start': 2023,
                    'end': None,
                    'institution': { 'country': 'US', 'domain': 'independent-researcher.org', 'name': 'Independent' }
                },
                {
                    'position': 'PhD Student',
                    'start': 2015,
                    'end': 2020,
                    'institution': { 'country': 'US', 'domain': 'smalllab.org', 'name': 'Small Lab' }
                }
            ]
        })
        assert openreview_client.get_profile('~Lena_Fischer1').state == 'Needs Moderation'

        request_invitation = openreview_client.get_invitation('openreview.net/Support/-/Vouch_Request')
        token = openreview.tools.get_user_hash_key('~Lena_Fischer1', request_invitation.secret, invitation='openreview.net/Support/-/Vouch_Request', expires_in=3600)

        request_edit = guest_client.post_note_edit_as_guest(token, {
            'invitation': 'openreview.net/Support/-/Vouch_Request',
            'signatures': ['~Lena_Fischer1'],
            'note': { 'content': { 'voucher': { 'value': '~Elena_Rossi1' } } }
        })
        assert request_edit['note']['number'] == 5
        helpers.await_queue_edit(openreview_client, edit_id=request_edit['id'])

        vouch_invitation = openreview_client.get_invitation('openreview.net/Support/Vouch_Request5/-/Vouch_Verification')
        assert vouch_invitation.assertion['profile']['id'] == '~Lena_Fischer1'
        history = vouch_invitation.assertion['profile']['content']['history']['value']['const']['add']
        assert [entry['institution']['domain'] for entry in history] == ['independent-researcher.org', 'smalllab.org']
        assert history[1]['position'] == 'PhD Student'

        voucher_client = helpers.get_user('elena.rossi@umass.edu')

        vouch = voucher_client.post_profile_assertion(
            invitation='openreview.net/Support/Vouch_Request5/-/Vouch_Verification',
            signatures=['~Elena_Rossi1'],
            content={ 'confirmations': { 'value': vouch_invitation.assertion['content']['confirmations']['value']['param']['enum'] } },
            profile={
                'id': '~Lena_Fischer1',
                'content': { 'emails': { 'value': { 'add': ['lena.fischer@gmail.com'] } } }
            }
        )
        helpers.await_queue_edit(openreview_client, edit_id=vouch['id'])

        assert openreview_client.get_profile('~Lena_Fischer1').state == 'Active'

        token = openreview.tools.get_user_hash_key('~Priya_Raman1', request_invitation.secret, invitation='openreview.net/Support/-/Vouch_Request', expires_in=3600)
        request_edit = guest_client.post_note_edit_as_guest(token, {
            'invitation': 'openreview.net/Support/-/Vouch_Request',
            'signatures': ['~Priya_Raman1'],
            'note': { 'content': { 'voucher': { 'value': '~Lena_Fischer1' } } }
        })
        assert request_edit['note']['number'] == 6
        helpers.await_queue_edit(openreview_client, edit_id=request_edit['id'])

        vouch_invitation = openreview_client.get_invitation('openreview.net/Support/Vouch_Request6/-/Vouch_Verification')
        assert vouch_invitation.invitees == ['~Lena_Fischer1']

        lena_client = helpers.get_user('lena.fischer@gmail.com')
        with pytest.raises(openreview.OpenReviewException, match=r'needs a confirmed email at an institution on our list'):
            lena_client.post_profile_assertion(
                invitation='openreview.net/Support/Vouch_Request6/-/Vouch_Verification',
                signatures=['~Lena_Fischer1'],
                content={ 'confirmations': { 'value': vouch_invitation.assertion['content']['confirmations']['value']['param']['enum'] } },
                profile={
                    'id': '~Priya_Raman1',
                    'content': { 'emails': { 'value': { 'add': ['priya.raman@gmail.com'] } } }
                }
            )
        assert openreview_client.get_profile('~Priya_Raman1').state == 'Needs Moderation'

        config_note = openreview_client.get_notes(invitation='openreview.net/-/OpenReview_Config')[0]
        support_client.post_note_edit(
            invitation='openreview.net/-/OpenReview_Config',
            signatures=['openreview.net/Support'],
            note=openreview.api.Note(
                id=config_note.id,
                content={
                    'moderate': { 'value': 'No' },
                    'weekend_moderation': { 'value': 'Yes' }
                }
            )
        )
