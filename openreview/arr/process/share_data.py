def process(client, edit, invitation):

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
    next_cycle_id = edit.note.content['next_cycle']['value']
    
    ## Try and retrieve different groups, notes and edges and change their readership

    # Groups (Reviewers, ACs, SACs, Ethics Reviewers, Ethics Chairs)
    groups = [
        client.get_group(group_id) for group_id in
        [
            domain.content['reviewers_id']['value'],
            domain.content['area_chairs_id']['value'],
            domain.content['senior_area_chairs_id']['value'],
            domain.content['ethics_chairs_id']['value'],
            f"{venue_id}/{domain.content['ethics_reviewers_name']['value']}",
        ]
    ]

    for group in groups:
        if next_cycle_id not in group.readers:
            group.readers.append(next_cycle_id)
            client.post_group_edit(
                invitation=meta_invitation_id,
                readers=[venue_id],
                writers=[venue_id],
                signatures=[venue_id],
                group=openreview.api.Group(
                    id=group.id,
                    readers=group.readers
                )
            )

    # Notes (Registraton Notes)
    roles = [domain.content['area_chairs_id']['value'], domain.content['reviewers_id']['value']]
    for role in roles:
        reg_invitation = client.get_invitation(f"{role}/-/Registration")
        note_readers = reg_invitation.edit['note']['readers']
        if next_cycle_id not in reg_invitation.edit['note']['readers']:
            note_readers = [next_cycle_id] + note_readers

        client.post_invitation_edit(
            invitations=meta_invitation_id,
            readers=[venue_id],
            writers=[venue_id],
            signatures=[venue_id],
            invitation=openreview.api.Invitation(
                id=f"{role}/-/Registration",
                edit={
                    'note': {
                        'readers': note_readers
                    }
                }
            )
        )

        # Registration invitations have no edit process function, manually post edits with new readers
        notes = client.get_all_notes(invitation=reg_invitation.id)
        for note in notes:
            reg_note_readers = note.readers
            if next_cycle_id not in reg_note_readers:
                reg_note_readers = [next_cycle_id] + reg_note_readers

            client.post_note_edit(
                invitation=meta_invitation_id, ## Would like to not use the meta invitation but cannot sign with user and client is a group
                signatures=[venue_id],
                readers=note.readers,
                note=openreview.api.Note(
                    id=note.id,
                    readers=reg_note_readers
                )
            )

    # Edges (Expertise Edges)