def process(client, edit, invitation):
    from Crypto.Hash import HMAC, SHA256
    import urllib.parse
    REVIEWERS_INVITED_ID = ''
    # REVIEWERS_PREFIX = ''
    CHECK_DECLINE = False

    note = edit.note
    hash_seed = invitation.content['hash_seed']['value']

    user = urllib.parse.unquote(note.content['user']['value'])
    hashkey = HMAC.new(hash_seed.encode(), digestmod=SHA256).update(user.encode()).hexdigest()

    if hashkey != note.content['key']['value']:
        raise openreview.OpenReviewException('Wrong key, please refer back to the recruitment email')

    if not client.get_groups(id=REVIEWERS_INVITED_ID, member=user):
        raise openreview.OpenReviewException('User not in invited group, please accept the invitation using the email address you were invited with')

    # if note.content['response']['value'] == 'No' and CHECK_DECLINE:
    #     memberships = client.get_groups(prefix=REVIEWERS_PREFIX, member=user)
    #     if memberships:
    #         raise openreview.OpenReviewException('You have already been assigned to a paper. Please contact the paper area chair or program chairs to be unassigned.')