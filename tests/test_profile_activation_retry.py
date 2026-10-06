import openreview
import pytest


class TestProfileActivationRetry():

    def test_rejected_activation_leaves_no_orphan_groups(self, openreview_client, helpers):

        ## Register with an institutional email and one name
        email = 'repro_orphan@umass.edu'
        guest = openreview.api.OpenReviewClient(baseurl='http://localhost:3001')
        guest.register_user(email=email, fullname='Repro Orphan', password=helpers.strong_password, dob=helpers.default_dob())
        registered_username = '~Repro_Orphan1'
        assert openreview_client.get_profile(registered_username).state == 'Inactive'

        ## On the activation form, enter a different name and an employer that does not match
        ## the domain of the email, so the activation is rejected by the history validation
        profile_content = {
            'names': [{ 'fullname': 'Orphan Repro', 'preferred': True }],
            'emails': [email],
            'preferredEmail': email,
            'homepage': 'https://orphanrepro.openreview.net',
            'dob': helpers.default_dob(),
            'history': [{
                'position': 'Engineer',
                'start': 2017,
                'end': None,
                'institution': { 'country': 'US', 'name': 'Some Company', 'domain': 'somecompany.com' }
            }]
        }

        ## Submit the same rejected form several times, as a confused user would
        for _ in range(3):
            with pytest.raises(openreview.OpenReviewException) as exc:
                guest.activate_user(email, profile_content)
            assert f'The institution of your email {email} must be added to the history' in str(exc.value)

        ## The profile was never activated
        profile = openreview_client.get_profile(registered_username)
        assert profile.state == 'Inactive'
        assert [name['username'] for name in profile.content['names']] == [registered_username]

        ## A rejected activation must not leave anything behind: the only group the email belongs to
        ## is the username created at registration, and that username only has the email as member
        ## '~' is the implicit group of every profile and is not a username group
        username_groups = [group for group in openreview_client.get_groups(member=email) if group.id.startswith('~') and group.id != '~']
        assert sorted(group.id for group in username_groups) == [registered_username], [(group.id, group.members) for group in username_groups]

        email_group = openreview_client.get_group(email)
        assert email_group.members == [registered_username]

        ## No username group was created for the name entered in the rejected form
        with pytest.raises(openreview.OpenReviewException):
            openreview_client.get_group('~Orphan_Repro1')
