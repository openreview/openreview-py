def process(client, note, invitation):

    username = note.content.get('username')

    profile = openreview.tools.get_profile(client, username)

    if not profile:
        raise openreview.OpenReviewException(f'Profile not found for {username}')

    if username == profile.get_preferred_name():
        raise openreview.OpenReviewException(f'Can not remove preferred name')
