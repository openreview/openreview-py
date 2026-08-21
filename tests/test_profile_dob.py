import openreview
import pytest
import re
import time


## The 13-to-17 mail is the same whichever path rejected the profile and does not name it. It carries
## two generated credentials -- the consent upload JWT and a fresh activation token -- so the wording
## is pinned exactly and only those two are matched by shape.
PARENTAL_CONSENT_MESSAGE = re.compile(
    r'OpenReview welcomes younger researchers, aged 13 and above, to participate in scholarly peer review\.\n'
    r'\n'
    r'If you are at least 13 and under 18 years of age, you must submit a consent form to activate your '
    r'profile\. More information can be found here: '
    r'https://docs\.openreview\.net/getting-started/creating-an-openreview-profile/information-for-high-school-students\n'
    r'\n'
    r'Please upload the completed consent form using the following link:\n'
    r'\n'
    r'http://localhost:3030/profile-documents/parental-consent/[\w-]+\.[\w-]+\.[\w-]+\n'
    r'\n'
    r'Once you have uploaded the consent form, use the link below to resubmit your profile for review:\n'
    r'\n'
    r'http://localhost:3030/profile/activate\?token=[0-9a-f]+\n'
    r'\n'
    r'This link expires in \d+ days\.'
)


class TestProfileDob():

    @pytest.fixture(scope="class")
    def support_client(self, openreview_client, helpers):

        support_client = helpers.create_user('dobsupport@support.org', 'Dobsupport', 'User', alternates=[], institution='openreview.net')
        openreview_client.post_group_edit(
            invitation = 'openreview.net/-/Edit',
            signatures = ['openreview.net'],
            group = openreview.api.Group(
                id = 'openreview.net/Support',
                members = {
                    'append': ['~Dobsupport_User1']
                }
            )
        )

        return support_client

    def set_moderation(self, openreview_client, support_client, value):
        config_note = openreview_client.get_notes(invitation='openreview.net/-/OpenReview_Config')[0]
        support_client.post_note_edit(
            invitation='openreview.net/-/OpenReview_Config',
            signatures=['openreview.net/Support'],
            note=openreview.api.Note(
                id=config_note.id,
                content={
                    'moderate': { 'value': value },
                    'weekend_moderation': { 'value': value }
                }
            )
        )

    def test_registration_under_minimum_age_is_refused(self, openreview_client, helpers):

        guest = openreview.api.OpenReviewClient()

        with pytest.raises(openreview.OpenReviewException) as ex:
            guest.register_user(
                email = 'dobchild@profile.org',
                fullname = 'Dobchild User',
                password = helpers.strong_password,
                dob = helpers.dob_for_age(12)
            )

        error = ex.value.args[0]
        assert error['name'] == 'MinimumAgeError'
        assert 'at least 13 years old' in error['message']

        ## The age is checked before anything is created, so the refusal leaves no profile behind
        assert openreview_client.search_profiles(emails=['dobchild@profile.org']) == {}

    def test_registration_at_minimum_age_is_allowed(self, openreview_client, helpers):

        guest = openreview.api.OpenReviewClient()
        guest.register_user(
            email = 'dobthirteen@profile.org',
            fullname = 'Dobthirteen User',
            password = helpers.strong_password,
            dob = helpers.dob_for_age(13)
        )

        assert openreview_client.get_profile('~Dobthirteen_User1')

    def test_minor_with_institutional_email_is_rejected(self, openreview_client, support_client, helpers):

        ## An institutional email activates a profile automatically even with moderation on. A minor
        ## must lose that exemption, so moderation has to be on for the rule to be observable.
        self.set_moderation(openreview_client, support_client, 'Yes')

        try:
            ## Control: an adult on the same institutional domain is activated automatically. Without
            ## this the test would pass for a non-institutional domain, where moderation is the
            ## ordinary outcome and being a minor changes nothing.
            helpers.create_user('dobadult@umass.edu', 'Dobadult', 'User', dob=helpers.dob_for_age(30))
            assert openreview_client.get_profile('~Dobadult_User1').state == 'Active Institutional'

            dob = helpers.dob_for_age(15)

            guest = openreview.api.OpenReviewClient()
            guest.register_user(
                email = 'dobteen@umass.edu',
                fullname = 'Dobteen User',
                password = helpers.strong_password,
                dob = dob
            )
            guest.activate_user('dobteen@umass.edu', {
                'names': [
                    {
                        'fullname': 'Dobteen User',
                        'username': '~Dobteen_User1',
                        'preferred': True
                    }
                ],
                'emails': ['dobteen@umass.edu'],
                'preferredEmail': 'dobteen@umass.edu',
                'homepage': f"https://dobteen{int(time.time())}.openreview.net",
                'dob': dob,
                'history': [{
                    'position': 'PhD Student',
                    'start': 2017,
                    'end': None,
                    'institution': {
                        'country': 'US',
                        'domain': 'umass.edu',
                    }
                }]
            })

            profile = openreview_client.get_profile('~Dobteen_User1')

            ## Same institutional domain as the adult above, so the only difference is the age
            assert profile.state not in ['Active', 'Active Institutional', 'Active Automatic']
            assert profile.state == 'Rejected'

            ## The date of birth is kept: it is what the rejection is based on
            assert profile.content['dob'] == dob

            ## Signing up as a minor is rejected outright rather than queued for a moderator, and is
            ## given the same parental consent route as a dob written onto an existing profile.
            messages = openreview_client.get_messages(to='dobteen@umass.edu')
            consent = [m for m in messages if m['content']['subject'] == 'OpenReview profile requires parental consent']
            assert consent, 'no parental consent message was sent'
            assert PARENTAL_CONSENT_MESSAGE.fullmatch(consent[0]['content']['text']), consent[0]['content']['text']

        finally:
            self.set_moderation(openreview_client, support_client, 'No')

    def test_minor_dob_on_existing_profile_is_rejected(self, openreview_client, helpers):

        helpers.create_user('dobreject@profile.org', 'Dobreject', 'User', dob=helpers.dob_for_age(30))
        assert openreview_client.get_profile('~Dobreject_User1').state in ['Active', 'Active Institutional', 'Active Automatic']

        ## A date showing the person is under 18 is accepted and judged afterwards: refusing the
        ## write would leave the age unknown, and recording it is the point.
        minor_dob = helpers.dob_for_age(15)
        openreview_client.post_profile(openreview.Profile(
            referent = '~Dobreject_User1',
            signatures = ['~Dobreject_User1'],
            content = { 'dob': minor_dob }
        ))

        profile = openreview_client.get_profile('~Dobreject_User1')
        assert profile.state == 'Rejected'
        assert profile.content['dob'] == minor_dob

        messages = openreview_client.get_messages(to='dobreject@profile.org')
        consent = [m for m in messages if m['content']['subject'] == 'OpenReview profile requires parental consent']
        assert consent, 'no parental consent message was sent'

        ## A 13-to-17 gets a different message from an under-13: a consent form is offered as a way
        ## back, where an under-13 has none.
        assert PARENTAL_CONSENT_MESSAGE.fullmatch(consent[0]['content']['text']), consent[0]['content']['text']

    def test_owner_can_not_change_dob_but_super_user_can(self, openreview_client, helpers):

        dob = helpers.dob_for_age(30)
        owner_client = helpers.create_user('dobowner@profile.org', 'Dobowner', 'User', dob=dob)

        assert owner_client.get_profile('~Dobowner_User1').content['dob'] == dob

        ## Resubmitting the same value is not a change, so it is allowed
        owner_client.post_profile(openreview.Profile(
            referent = '~Dobowner_User1',
            signatures = ['~Dobowner_User1'],
            content = { 'dob': dob }
        ))
        assert owner_client.get_profile('~Dobowner_User1').content['dob'] == dob

        ## Replacing it is not
        with pytest.raises(openreview.OpenReviewException) as ex:
            owner_client.post_profile(openreview.Profile(
                referent = '~Dobowner_User1',
                signatures = ['~Dobowner_User1'],
                content = { 'dob': helpers.dob_for_age(25) }
            ))
        assert 'Can not update the date of birth' in ex.value.args[0]['message']

        assert owner_client.get_profile('~Dobowner_User1').content['dob'] == dob

        ## The super user is privileged and can override it
        new_dob = helpers.dob_for_age(40)
        openreview_client.post_profile(openreview.Profile(
            referent = '~Dobowner_User1',
            signatures = ['~Dobowner_User1'],
            content = { 'dob': new_dob }
        ))

        assert openreview_client.get_profile('~Dobowner_User1').content['dob'] == new_dob

    def test_under_minimum_age_dob_on_existing_profile_is_rejected(self, openreview_client, helpers):

        helpers.create_user('dobchildedit@profile.org', 'Dobchildedit', 'User', dob=helpers.dob_for_age(30))

        child_dob = helpers.dob_for_age(11)
        openreview_client.post_profile(openreview.Profile(
            referent = '~Dobchildedit_User1',
            signatures = ['~Dobchildedit_User1'],
            content = { 'dob': child_dob }
        ))

        profile = openreview_client.get_profile('~Dobchildedit_User1')
        assert profile.state == 'Rejected'
        assert profile.content['dob'] == child_dob

        messages = openreview_client.get_messages(to='dobchildedit@profile.org')
        rejection = [m for m in messages if m['content']['subject'] == 'OpenReview profile rejected']
        assert rejection, 'no rejection message was sent'

        ## An under-13 gets a different message from a 13-to-17: no document makes them eligible, so
        ## the mail states the reason and offers no parental consent upload link.
        assert rejection[0]['content']['text'] == '''Your OpenReview profile ~Dobchildedit_User1 has been rejected because OpenReview accounts are not available to anyone under 13 years old.

If you believe this is a mistake, please contact us using the Feedback Form. Otherwise, your profile will be deleted.'''

    def test_profile_without_dob_can_not_be_edited_without_supplying_one(self, openreview_client, helpers):

        ## The V1 API predates the date of birth, so a profile registered through it has none. That is
        ## what a profile created before the requirement looks like.
        guest = openreview.Client()
        guest.register_user(
            email = 'doblegacy@profile.org',
            fullname = 'Doblegacy User',
            password = helpers.strong_password
        )
        guest.activate_user('doblegacy@profile.org', {
            'names': [
                {
                    'first': 'Doblegacy',
                    'last': 'User',
                    'username': '~Doblegacy_User1'
                }
            ],
            'emails': ['doblegacy@profile.org'],
            'preferredEmail': 'doblegacy@profile.org',
            'homepage': f"https://doblegacy{int(time.time())}.openreview.net",
            'history': [{
                'position': 'PhD Student',
                'start': 2017,
                'end': None,
                'institution': {
                    'country': 'US',
                    'domain': 'profile.org',
                }
            }],
        })

        assert 'dob' not in openreview_client.get_profile('~Doblegacy_User1').content

        owner_client = openreview.api.OpenReviewClient(username='doblegacy@profile.org', password=helpers.strong_password)

        ## An edit that leaves the profile without one is refused
        with pytest.raises(openreview.OpenReviewException) as ex:
            owner_client.post_profile(openreview.Profile(
                referent = '~Doblegacy_User1',
                signatures = ['~Doblegacy_User1'],
                content = { 'homepage': f"https://doblegacyedited{int(time.time())}.openreview.net" }
            ))
        assert 'The field dob cannot be empty or missing' in ex.value.args[0]['message']

        ## Supplying a first one is allowed: write-once only refuses replacing an existing value
        dob = helpers.dob_for_age(30)
        owner_client.post_profile(openreview.Profile(
            referent = '~Doblegacy_User1',
            signatures = ['~Doblegacy_User1'],
            content = { 'dob': dob }
        ))

        assert openreview_client.get_profile('~Doblegacy_User1').content['dob'] == dob
