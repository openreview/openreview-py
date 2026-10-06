def process(client, edit, invitation):

    SUPPORT_USER_ID = ''

    usernames = edit.note.content.get('usernames', {}).get('value', [])
    name = edit.note.content.get('name', {}).get('value')
    signature = edit.signatures[0]

    for username in usernames:
        profile = openreview.tools.get_profile(client, username)

        if not profile:
            raise openreview.OpenReviewException(f'Profile not found for {username}')

        if signature not in [SUPPORT_USER_ID, '~Super_User1']:
            profile_usernames = [n.get('username') for n in profile.content.get('names', []) if n.get('username')]
            if signature not in profile_usernames:
                raise openreview.OpenReviewException(f'You can only remove names from your own profile, {username} does not belong to {signature}')

        if username == profile.get_preferred_name():
            raise openreview.OpenReviewException(f'Can not remove preferred name for {username}')

        if name != openreview.tools.pretty_id(username):
            raise openreview.OpenReviewException(f"Name does not match with username {username}")
