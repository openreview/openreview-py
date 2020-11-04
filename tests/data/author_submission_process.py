def process(client, note, invitation):
    venue_id='.TMLR'

    paper_group=client.post_group(openreview.Group(id=f'{venue_id}/Paper{note.number}',
        readers=[venue_id],
        writers=[venue_id],
        signatures=[venue_id],
        signatories=[venue_id]
    ))

    authors_group_id=f'{paper_group.id}/Authors'
    authors_group=client.post_group(openreview.Group(id=authors_group_id,
        readers=[venue_id, authors_group_id],
        writers=[venue_id],
        signatures=[venue_id],
        signatories=[venue_id, authors_group_id],
        members=note.content['authorids']['value']
    ))

    action_editors_group_id=f'{paper_group.id}/AEs'
    action_editors_group=client.post_group(openreview.Group(id=action_editors_group_id,
        readers=[venue_id, action_editors_group_id],
        nonreaders=[authors_group_id],
        writers=[venue_id],
        signatures=[venue_id],
        signatories=[venue_id, action_editors_group_id],
        members=[]
    ))

    reviewers_group_id=f'{paper_group.id}/Reviewers'
    reviewers_group=client.post_group(openreview.Group(id=reviewers_group_id,
        readers=[venue_id, action_editors_group_id],
        nonreaders=[authors_group_id],
        writers=[venue_id, action_editors_group_id],
        signatures=[venue_id],
        signatories=[venue_id],
        members=[]
    ))

    ## TODO: create this invitation using an invitation
    review_invitation_id=f'{paper_group.id}/-/Review'
    invitation = client.post_invitation_edit(readers=[venue_id],
                                writers=[venue_id],
                                signatures=[venue_id],
                                invitation=openreview.Invitation(id=review_invitation_id,
                                                invitees=[f"{paper_group.id}/Reviewers", f'{paper_group.id}/AEs'],
                                                readers=['everyone'],
                                                writers=[venue_id],
                                                signatures=[venue_id],
                                                reply={
                                                    'signatures': { 'values-regex': '~.*' },
                                                    'readers': { 'values': [ venue_id, '${signatures}', f'{paper_group.id}/AEs']},
                                                    'writers': { 'values': [ venue_id, '${signatures}', f'{paper_group.id}/AEs']},
                                                    'note': {
                                                        'forum': { 'value': note.id },
                                                        'replyto': { 'value': note.id },
                                                        'signatures': { 'values-regex': f'{paper_group.id}/AnonReviewer1|{paper_group.id}/AEs' },
                                                        'readers': { 'values': [ venue_id, f'{paper_group.id}/AnonReviewer1', f'{paper_group.id}/AEs']},
                                                        'writers': { 'values': [ venue_id, f'{paper_group.id}/AnonReviewer1', f'{paper_group.id}/AEs']},
                                                        'content': {
                                                            'title': {
                                                                'value': {
                                                                    'value-regex': '.*',
                                                                    'required': True
                                                                }
                                                            },
                                                            'review': {
                                                                'value': {
                                                                    'value-regex': '.*',
                                                                    'required': True
                                                                }
                                                            },
                                                            'rating': {
                                                                'value': {
                                                                    'values-regex': '.*',
                                                                    'required': True
                                                                }
                                                            },
                                                            'confidence': {
                                                                'value': {
                                                                    'values-regex': '.*',
                                                                    'required': True
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                    ))

