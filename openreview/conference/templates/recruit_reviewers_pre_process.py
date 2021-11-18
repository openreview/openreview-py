def process(client, note, invitation):
    from Crypto.Hash import HMAC, SHA256
    import urllib.parse
    HASH_SEED = ''
    REVIEWERS_INVITED_ID = ''
    REVIEWERS_REGEX = ''
    CHECK_DECLINE = False

    user = urllib.parse.unquote(note.content['user'])
    hashkey = HMAC.new(HASH_SEED.encode(), digestmod=SHA256).update(user.encode()).hexdigest()

    if hashkey != note.content['key']:
        raise openreview.OpenReviewException('Wrong key, please refer back to the recruitment email')

    if not client.get_groups(id=REVIEWERS_INVITED_ID, member=user):
        raise openreview.OpenReviewException('User not in invited group, please accept the invitation using the email address you were invited with')

    if note.content['response'] == 'No' and CHECK_DECLINE:
        memberships = client.get_groups(regex=REVIEWERS_REGEX, member=user)
        if memberships:
            raise openreview.OpenReviewException('You have already been assigned to a paper. Please contact the paper area chair or program chairs to be unassigned.')
