def process_update(client, edge, invitation, existing_edge):

    domain = client.get_group(edge.domain)
    venue_id = domain.id
    meta_invitation_id = domain.content['meta_invitation_id']['value']
    short_phrase = domain.content['subtitle']['value']
    contact = domain.content['contact']['value']
    program_chairs_id = domain.content['program_chairs_id']['value']
    submission_name = domain.content['submission_name']['value']
    reviewers_name = invitation.content['reviewers_name']['value']
    reviewers_id = invitation.content['reviewers_id']['value']
    sync_sac_id = invitation.content.get('sync_sac_id',{}).get('value')
    sac_assignment_id = invitation.content.get('sac_assignment_id',{}).get('value')
    sender = domain.get_content_value('message_sender')
    pretty_name = openreview.tools.pretty_id(reviewers_name)
    pretty_name = pretty_name[:-1] if pretty_name.endswith('s') else pretty_name


    note=client.get_note(edge.head)
    group=client.get_group(f'{venue_id}/{submission_name}{note.number}/{reviewers_name}')
    if edge.ddate and edge.tail in group.members:
        assignment_edges = client.get_edges(invitation=edge.invitation, head=edge.head, tail=edge.tail)
        if assignment_edges:
            return
        print(f'Remove member {edge.tail} from {group.id}')
        client.remove_members_from_group(group.id, edge.tail)

        if sync_sac_id and sync_sac_id.format(number=note.number) not in edge.signatures:
            print(f'Remove member from SAC group')
            assignments = client.get_edges(invitation=sac_assignment_id, head=edge.tail)
            if assignments:
                client.remove_members_from_group(sync_sac_id.format(number=note.number), assignments[0].tail)
            else:
                print('No SAC assignments found')

    if not edge.ddate and edge.tail not in group.members:
        print(f'Add member {edge.tail} to {group.id}')
        client.add_members_to_group(group.id, edge.tail)
        client.add_members_to_group(reviewers_id, edge.tail)

        if sync_sac_id:
            print('Add the SAC to the paper group')
            assignments = client.get_edges(invitation=sac_assignment_id, head=edge.tail)
            if assignments:
                client.add_members_to_group(sync_sac_id.format(number=note.number), assignments[0].tail)
            else:
                print('No SAC assignments found')

        signature=f'{openreview.tools.pretty_id(edge.signatures[0])}'

        if venue_id in edge.signatures or program_chairs_id in edge.signatures:
            signature=f'{openreview.tools.pretty_id(program_chairs_id)}'

        recipients=[edge.tail]
        subject=f'[{short_phrase}] You have been assigned as a {pretty_name} for paper number {note.number}'
        message=f'''This is to inform you that you have been assigned as a {pretty_name} for paper number {note.number} for {short_phrase}.

To review this new assignment, please login to OpenReview and go to https://openreview.net/forum?id={note.forum}.

To check all of your assigned papers, go to https://openreview.net/group?id={reviewers_id}.

Thank you,

{signature}'''

        client.post_message(subject, recipients, message, invitation=meta_invitation_id, signature=venue_id, parentGroup=group.id, replyTo=contact, sender=sender)
