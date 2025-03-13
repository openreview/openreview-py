def process(client, edit, invitation):

    print('add aceppted reviewers to the official committee group')

    domain = client.get_group(invitation.domain)
    reviewers_invited_id = domain.content['reviewers_invited_id']['value']
    reviewers_id = domain.content['reviewers_id']['value']
    reviewers_declined_id = domain.content['reviewers_declined_id']['value']
    reviewers_invited_message_id = domain.content['reviewers_invited_message_id']['value']

    note = edit.note
    user=note.content['user']['value']
    key=note.content['key']['value']
    response=note.content['response']['value']

    if note.ddate:
        print('Note has been deleted. Exiting.')
        return
    
    user = openreview.tools.get_user_parse(user, quote=False)
    hash_seed = invitation.content['hash_seed']['value']

    hashkey = openreview.tools.get_user_hash_key(user, hash_seed)

    if hashkey != key:
        raise openreview.OpenReviewException(f'Invalid key: {user}')
    
    if not client.get_groups(id=reviewers_invited_id, member=user):
        raise openreview.OpenReviewException(f'User not invited: {user}')
    
    members_to_remove=[user]

    profile=openreview.tools.get_profile(client, user)
    if profile:
        members_to_remove.append(profile.id)

    reviewers_invited_group = client.get_group(reviewers_invited_id)
    
    if response == 'Yes':

        client.remove_members_from_group(reviewers_declined_id, members_to_remove)
        client.add_members_to_group(reviewers_id, user)

        subject = reviewers_invited_group.content['accepted_message_subject_template']['value']
        message = reviewers_invited_group.content['accepted_message_body_template']['value']

        client.post_message(subject, [user], message, invitation=reviewers_invited_message_id, signature=domain.id)
        return

    if response == 'No':
        client.remove_members_from_group(reviewers_id, members_to_remove)
        client.add_members_to_group(reviewers_declined_id, user)

        subject = reviewers_invited_group.content['declined_message_subject_template']['value']
        message = reviewers_invited_group.content['declined_message_body_template']['value']

        client.post_message(subject, [user], message, invitation=reviewers_invited_message_id, signature=domain.id)
        return

    
    raise openreview.OpenReviewException('Invalid response')



      