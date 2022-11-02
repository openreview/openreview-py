def process(client, edit, invitation):
    from Crypto.Hash import HMAC, SHA256
    import urllib.parse
    import re
    committee_invited_id = invitation.content['committee_invited_id']['value']
    venue_id = invitation.content['venue_id']['value']
    committee_name = invitation.content['committee_id']['value'].split('/')[-1]

    note = edit.note
    hash_seed = invitation.content['hash_seed']['value']

    user = urllib.parse.unquote(note.content['user']['value'])
    hashkey = HMAC.new(hash_seed.encode(), digestmod=SHA256).update(user.encode()).hexdigest()

    if hashkey != note.content['key']['value']:
        raise openreview.OpenReviewException('Wrong key, please refer back to the recruitment email')

    if not client.get_groups(id=committee_invited_id, member=user):
        raise openreview.OpenReviewException('User not in invited group, please accept the invitation using the email address you were invited with')

    if note.content['response']['value'] == 'No':
        groups = client.get_groups(prefix=venue_id, member=user)
        regex = venue_id + '/.*[0-9]/' + committee_name
        for group in groups:
            if re.match(regex, group.id):
                raise openreview.OpenReviewException('You have already been assigned to a paper. Please contact the paper area chair or program chairs to be unassigned.')