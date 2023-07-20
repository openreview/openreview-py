def process_update(client, edge, invitation, existing_edge):

    domain = client.get_group(edge.domain)
    venue_id = domain.id
    short_phrase = domain.content['subtitle']['value']
    program_chairs_id = domain.content['program_chairs_id']['value']
    submission_name = domain.content['submission_name']['value']
    reviewers_name = invitation.content['reviewers_name']['value']
    reviewers_id = invitation.content['reviewers_id']['value']
    sync_sac_id = invitation.content['sync_sac_id']['value']
    sac_assingment_id = invitation.content['sac_assignment_id']['value']
    pretty_name = openreview.tools.pretty_id(reviewers_name)
    pretty_name = pretty_name[:-1] if pretty_name.endswith('s') else pretty_name


    note=client.get_note(edge.head)
    group=client.get_group(f'{venue_id}/{submission_name}{note.number}/{reviewers_name}')
    if edge.ddate and edge.tail in group.members:
        print(f'Remove member {edge.tail} from {group.id}')
        client.remove_members_from_group(group.id, edge.tail)

        if sync_sac_id and sync_sac_id.format(number=note.number) not in edge.signatures:
            print(f'Remove member from SAC group')
            group = client.get_group(sync_sac_id.format(number=note.number))
            client.post_group_edit(
                invitation=f'{venue_id}/-/Edit',
                readers = [venue_id],
                writers = [venue_id],
                signatures = [venue_id],
                group = openreview.api.Group(
                    id = group.id,
                    members = []
                )
            )

    if not edge.ddate and edge.tail not in group.members:
        print(f'Add member {edge.tail} to {group.id}')
        client.add_members_to_group(group.id, edge.tail)
        client.add_members_to_group(reviewers_id, edge.tail)

        if sync_sac_id:
            print('Add the SAC to the paper group')
            assignments = client.get_edges(invitation=sac_assingment_id, head=edge.tail)
            if assignments:
                client.add_members_to_group(sync_sac_id.format(number=note.number), assignments[0].tail)
            else:
                print('No SAC assignments found')

        signature=f'{openreview.tools.pretty_id(edge.signatures[0])}({edge.tauthor})'

        if venue_id in edge.signatures or program_chairs_id in edge.signatures:
            signature=f'{openreview.tools.pretty_id(program_chairs_id)}'

        recipients=[edge.tail]
        subject=f'[{short_phrase}] You have been assigned as a {pretty_name} for paper number {note.number}'
        message=f'''This is to inform you that you have been assigned as a {pretty_name} for paper number {note.number} for {short_phrase}.

To review this new assignment, please login to OpenReview and go to https://openreview.net/forum?id={note.forum}.

To check all of your assigned papers, go to https://openreview.net/group?id={reviewers_id}.

Thank you,

{signature}'''

        client.post_message(subject, recipients, message, parentGroup=group.id)
