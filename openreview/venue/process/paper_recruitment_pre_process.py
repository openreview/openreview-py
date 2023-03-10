def process(client, edit, invitation):
    from Crypto.Hash import HMAC, SHA256
    import urllib.parse
    import re
    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    hash_seed = invitation.content['hash_seed']['value']
    committee_invited_id = invitation.content['committee_invited_id']['value']
    committee_name = invitation.content['committee_id']['value'].split('/')[-1]
    submission_venue_id = domain.content['submission_venue_id']['value']
    check_decline = False
    invite_assignment_invitation = domain.content['reviewers_invite_assignment_id']['value']

    note = edit.note

    user = urllib.parse.unquote(note.content['user']['value'])
    hashkey = HMAC.new(hash_seed.encode(), digestmod=SHA256).update(user.encode()).hexdigest()

    submission = client.get_notes(note.content['submission_id']['value'])[0]

    invite_edges = client.get_edges(invitation=invite_assignment_invitation, head=submission.id, tail=user)
    if not invite_edges:
        profile = openreview.tools.get_profile(client, user)
        if profile:
            invite_edges = client.get_edges(invitation=invite_assignment_invitation, head=submission.id, tail=profile.id)
        # if still no edges with profile.id, raise exception
        if not invite_edges:
            raise openreview.OpenReviewException('Invitation no longer exists. No action is required from your end.')

    if hashkey != note.content['key']['value']:
        raise openreview.OpenReviewException('Wrong key, please refer back to the recruitment email')

    if not client.get_groups(id=committee_invited_id, member=user):
        raise openreview.OpenReviewException('User not in invited group, please accept the invitation using the email address you were invited with')

    if submission_venue_id not in submission.content['venueid']['value']:
        raise openreview.OpenReviewException('This submission is no longer under review. No action is required from your end.')

    if note.content['response']['value'] == 'Yes':
        if invite_edges[0].label == 'Accepted':
            raise openreview.OpenReviewException('You have already accepted this invitation.')
        if invite_edges[0].label == 'Pending Sign Up':
            raise openreview.OpenReviewException('You have already accepted this invitation, but the assignment is pending until you create a profile and no conflict are detected.')
        if invite_edges[0].label == 'Conflict Detected':
            raise openreview.OpenReviewException('You have already accepted this invitation, but a conflict was detected and the assignment cannot be made.')

    if note.content['response']['value'] == 'No':
        if not note.content.get('comment') and 'Declined' in invite_edges[0].label:
            raise openreview.OpenReviewException('You have already declined this invitation.')
        if check_decline:
            groups = client.get_groups(prefix=venue_id, member=user)
            regex = venue_id + '/.*[0-9]/' + committee_name
            for group in groups:
                if re.match(regex, group.id):
                    raise openreview.OpenReviewException('You have already been assigned to a paper. Please contact the paper area chair or program chairs to be unassigned.')
