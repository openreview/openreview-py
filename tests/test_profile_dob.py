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

    def test_super_user_can_delete_the_dob(self, openreview_client, helpers):

        dob = helpers.dob_for_age(30)
        helpers.create_user('dobdelete@profile.org', 'Dobdelete', 'User', dob=dob)
        assert openreview_client.get_profile('~Dobdelete_User1').content['dob'] == dob

        ## A retraction is a negative weight on the stored value, which is the other way to lose one.
        ## The owner is stopped by write-once, but a privileged user is not, and the rule that a
        ## profile has to keep a date of birth is not applied on this path, so the value is removed.
        openreview_client.post_profile(openreview.Profile(
            referent = '~Dobdelete_User1',
            signatures = ['~Dobdelete_User1'],
            content = {},
            metaContent = { 'dob': { 'values': [dob], 'weights': [-1] } }
        ))

        assert 'dob' not in openreview_client.get_profile('~Dobdelete_User1').content

    def test_support_user_can_change_the_dob(self, openreview_client, support_client, helpers):

        dob = helpers.dob_for_age(30)
        owner_client = helpers.create_user('dobsupportedit@profile.org', 'Dobsupportedit', 'User', dob=dob)

        ## The owner is refused whoever else is allowed to override it
        with pytest.raises(openreview.OpenReviewException) as ex:
            owner_client.post_profile(openreview.Profile(
                referent = '~Dobsupportedit_User1',
                signatures = ['~Dobsupportedit_User1'],
                content = { 'dob': helpers.dob_for_age(25) }
            ))
        assert 'Can not update the date of birth' in ex.value.args[0]['message']

        ## Support is privileged, so write-once does not stop it. It signs as the Support group,
        ## because unlike the super user it is not a signatory of the profile.
        new_dob = helpers.dob_for_age(40)
        support_client.post_profile(openreview.Profile(
            referent = '~Dobsupportedit_User1',
            signatures = ['openreview.net/Support'],
            content = { 'dob': new_dob }
        ))

        assert openreview_client.get_profile('~Dobsupportedit_User1').content['dob'] == new_dob

    def test_support_user_can_delete_the_dob(self, openreview_client, support_client, helpers):

        dob = helpers.dob_for_age(30)
        helpers.create_user('dobsupportdelete@profile.org', 'Dobsupportdelete', 'User', dob=dob)
        assert openreview_client.get_profile('~Dobsupportdelete_User1').content['dob'] == dob

        ## A retraction is a negative weight on the stored value, the same way the super user removes
        ## one, signed as the Support group
        support_client.post_profile(openreview.Profile(
            referent = '~Dobsupportdelete_User1',
            signatures = ['openreview.net/Support'],
            content = {},
            metaContent = { 'dob': { 'values': [dob], 'weights': [-1] } }
        ))

        assert 'dob' not in openreview_client.get_profile('~Dobsupportdelete_User1').content

    def test_age_flags_are_visible_only_to_privileged_users(self, openreview_client, support_client, helpers):

        dob = helpers.dob_for_age(30)
        owner_client = helpers.create_user('dobflags@profile.org', 'Dobflags', 'User', dob=dob)
        other_client = helpers.create_user('dobflagsother@profile.org', 'Dobflagsother', 'User', dob=helpers.dob_for_age(30))

        ## Both flags are derived from the date of birth on every read, never stored
        super_profile = openreview_client.get_profile('~Dobflags_User1')
        assert super_profile.content['isMinor'] == False
        assert super_profile.content['isOver18'] == True

        ## Support sees isMinor, which is the flag moderation acts on, but not isOver18
        support_profile = support_client.get_profile('~Dobflags_User1')
        assert support_profile.content['isMinor'] == False
        assert 'isOver18' not in support_profile.content

        ## The owner gets their own date of birth back but neither derived flag
        own_profile = owner_client.get_profile('~Dobflags_User1')
        assert own_profile.content['dob'] == dob
        assert 'isMinor' not in own_profile.content
        assert 'isOver18' not in own_profile.content

        ## Everybody else sees none of the three
        other_profile = other_client.get_profile('~Dobflags_User1')
        assert 'dob' not in other_profile.content
        assert 'isMinor' not in other_profile.content
        assert 'isOver18' not in other_profile.content

        ## isOver18 also reaches an active venue account, which is a group id rather than a person.
        ## That tier needs a venue to exist, so it is covered where one is already set up.

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
