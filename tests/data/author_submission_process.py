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

