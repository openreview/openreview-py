def process(client, edit, invitation):

    usernames = edit.note.content.get('usernames', {}).get('value', [])
    name = edit.note.content.get('name', {}).get('value')

    for username in usernames:
        profile = openreview.tools.get_profile(client, username)

        if not profile:
            raise openreview.OpenReviewException(f'Profile not found for {username}')

        if username == profile.get_preferred_name():
            raise openreview.OpenReviewException(f'Can not remove preferred name for {username}')

        if name != openreview.tools.pretty_id(username):
            raise openreview.OpenReviewException(f"Name does not match with username {username}")
