def process(client, edit, invitation):
    from Crypto.Hash import HMAC, SHA256
    import urllib.parse
    committee_invited_id = invitation.content['committee_invited_id']['value']

    note = edit.note
    hash_seed = invitation.content['hash_seed']['value']

    user = urllib.parse.unquote(note.content['user']['value'])
    hashkey = HMAC.new(hash_seed.encode(), digestmod=SHA256).update(user.encode()).hexdigest()

    if hashkey != note.content['key']['value']:
        raise openreview.OpenReviewException('Wrong key, please refer back to the recruitment email')

    if not client.get_groups(id=committee_invited_id, member=user):
        raise openreview.OpenReviewException('User not in invited group, please accept the invitation using the email address you were invited with')