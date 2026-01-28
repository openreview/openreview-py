def process(client, edit, invitation):

    print('add aceppted reviewers to the official committee group')

    
    domain = client.get_group(invitation.domain)
    
    committee_group = client.get_group(invitation.content['committee_id']['value'])
    committee_role = committee_group.content['committee_role']['value']
    committee_invited_id = domain.content[f'{committee_role}_invited_id']['value']
    committee_id = domain.content[f'{committee_role}_id']['value']
    committee_declined_id = domain.content[f'{committee_role}_declined_id']['value']
    committee_invited_message_id = domain.content[f'{committee_role}_invited_message_id']['value']

    note = edit.note
    user=note.content.get('user', {}).get('value', note.signatures[0])
    response=note.content['response']['value']
    reduced_load=note.content.get('reduced_load')
    if reduced_load:
        reduced_load = reduced_load['value']    

    if note.ddate:
        print('Note has been deleted. Exiting.')
        return
    
    user = openreview.tools.get_user_parse(user, quote=False)

    
    members_to_remove=[user]

    profile=openreview.tools.get_profile(client, user)
    if profile:
        members_to_remove.append(profile.id)

    if response == 'Yes':

        client.remove_members_from_group(committee_declined_id, members_to_remove)
        client.add_members_to_group(committee_id, user)

        subject = invitation.content['accepted_message_subject_template']['value']
        message = invitation.content['accepted_message_body_template']['value']

        reduced_load_subject = ' with reduced load' if reduced_load else ''       

        client.post_message(subject + reduced_load_subject, [user], message, invitation=committee_invited_message_id, signature=domain.id)
        return

    if response == 'No':
        client.remove_members_from_group(committee_id, members_to_remove)
        client.add_members_to_group(committee_declined_id, user)

        subject = invitation.content['declined_message_subject_template']['value']
        message = invitation.content['declined_message_body_template']['value']

        client.post_message(subject, [user], message, invitation=committee_invited_message_id, signature=domain.id)
        return

    
    raise openreview.OpenReviewException('Invalid response')



      