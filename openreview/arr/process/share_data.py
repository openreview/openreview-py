def process(client, edit, invitation):

    def _is_identical_content(note_to_post, notes):
        for note in notes:
            is_identical = True
            if set(note.content.keys()) != set(note_to_post.content.keys()):
                continue
            for k, v in note_to_post.content.items():
                if v['value'] != note.content[k]['value']:
                    is_identical = False
            if is_identical:
                return note
        return None

    import time
    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    submission_venue_id = domain.content['submission_venue_id']['value']
    meta_invitation_id = domain.content['meta_invitation_id']['value']
    venue_name = domain.content['title']['value']

    now = openreview.tools.datetime_millis(datetime.datetime.utcnow())
    cdate = invitation.cdate

    if cdate > now:
        ## invitation is in the future, do not process
        print('invitation is not yet active', cdate)
        return
    previous_cycle_id = edit.note.content['previous_cycle']['value']
    next_cycle_id = venue_id
    
    ## Try and retrieve different groups, notes and edges and change their readership

    # Groups (Reviewers, ACs, SACs, Ethics Reviewers, Ethics Chairs)
    groups = [
        client.get_group(group_id) for group_id in
        [
            domain.content['reviewers_id']['value'].replace(venue_id, previous_cycle_id),
            domain.content['area_chairs_id']['value'].replace(venue_id, previous_cycle_id),
            domain.content['senior_area_chairs_id']['value'].replace(venue_id, previous_cycle_id),
            domain.content['ethics_chairs_id']['value'].replace(venue_id, previous_cycle_id),
            f"{previous_cycle_id}/{domain.content['ethics_reviewers_name']['value']}",
        ]
    ]

    for group in groups:
        role = group.id.split('/')[-1]
        destination_group = client.get_group(f"{next_cycle_id}/{role}")
        missing_members = set(group.members).difference(set(destination_group.members))
        if len(missing_members) > 0:
            client.add_members_to_group(destination_group, list(missing_members))

    # Notes (Registraton Notes)
    roles = [
        domain.content['senior_area_chairs_id']['value'].replace(venue_id, previous_cycle_id),
        domain.content['area_chairs_id']['value'].replace(venue_id, previous_cycle_id),
        domain.content['reviewers_id']['value'].replace(venue_id, previous_cycle_id)]
    for role in roles:
        reg_invitation = client.get_invitation(f"{role}/-/Registration")
        next_reg_invitation = client.get_invitation(f"{next_cycle_id}/{role.split('/')[-1]}/-/Registration")

        existing_notes = client.get_all_notes(invitation=next_reg_invitation.id)
        notes = client.get_all_notes(invitation=reg_invitation.id)

        for note in notes:
            if _is_identical_content(note, existing_notes):
                continue
            # Clear note fields
            note.id = None
            note.invitations = None
            note.cdate = None
            note.mdate = None
            note.license = None
            note.readers = [next_cycle_id, note.signatures[0]]
            note.writers = [next_cycle_id, note.signatures[0]]
            note.forum = next_reg_invitation.edit['note']['forum']
            note.replyto = next_reg_invitation.edit['note']['replyto']

            client.post_note_edit(
                invitation=f"{next_cycle_id}/{role.split('/')[-1]}/-/Registration",
                signatures=note.signatures,
                readers=note.readers,
                note=note
            )

    # Edges (Expertise Edges)
    for role in roles:
        exp_edges = {o['id']['tail']: o['values'] for o in client.get_grouped_edges(
            invitation=f"{role}/-/Expertise_Selection",
            groupby='tail',
            select='head,label')
        }
        existing_exp_edges = {o['id']['tail']: [e['head'] for e in o['values']] for o in client.get_grouped_edges(
            invitation=f"{next_cycle_id}/{role.split('/')[-1]}/-/Expertise_Selection",
            groupby='tail',
            select='head')
        }

        for tail, pub_edges in exp_edges.items():
            for pub_edge in pub_edges:
                if tail in existing_exp_edges and pub_edge['head'] in existing_exp_edges[tail]:
                    continue
                client.post_edge(
                    openreview.api.Edge(
                        invitation=f"{next_cycle_id}/{role.split('/')[-1]}/-/Expertise_Selection",
                        readers=[next_cycle_id, tail],
                        writers=[next_cycle_id, tail],
                        signatures=[tail],
                        head=pub_edge['head'],
                        tail=tail,
                        label=pub_edge['label']
                    )
                )