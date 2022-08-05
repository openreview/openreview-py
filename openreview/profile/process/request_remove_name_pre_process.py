def process(client, note, invitation):

    usernames = note.content.get('usernames')
    name = note.content.get('name')

    for username in usernames:
        profile = openreview.tools.get_profile(client, username)

        if not profile:
            raise openreview.OpenReviewException(f'Profile not found for {username}')

        if username == profile.get_preferred_name():
            raise openreview.OpenReviewException(f'Can not remove preferred name for {username}')

        if name != openreview.tools.pretty_id(username):
            raise openreview.OpenReviewException(f"Name does not match with username {username}")
