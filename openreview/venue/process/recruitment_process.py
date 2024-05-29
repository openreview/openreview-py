def process(client, edit, invitation):
    from Crypto.Hash import HMAC, SHA256
    import urllib.parse
    domain = client.get_group(invitation.domain)
    meta_invitation_id = domain.content['meta_invitation_id']['value']
    short_phrase = domain.content['subtitle']['value']
    contact = domain.content['contact']['value']
    sender = domain.get_content_value('message_sender')
    committee_name = invitation.content['committee_name']['value']
    committee_invited_id = invitation.content['committee_invited_id']['value']
    committee_id = invitation.content['committee_id']['value']
    committee_declined_id = invitation.content['committee_declined_id']['value']
    overlap_committee_name = invitation.content['overlap_committee_name']['value'] if 'overlap_committee_name' in invitation.content else ''
    overlap_committee_id = invitation.content['overlap_committee_id']['value'] if 'overlap_committee_id' in invitation.content else ''

    note = edit.note
    user=note.content['user']['value']
    key=note.content['key']['value']
    response=note.content['response']['value']
    reduced_load=note.content.get('reduced_load')
    if reduced_load:
        reduced_load = reduced_load['value']

    if note.ddate:
        return
    
    user = urllib.parse.unquote(user)
    hash_seed = invitation.content['hash_seed']['value']

    hashkey = HMAC.new(hash_seed.encode(), digestmod=SHA256).update(user.encode()).hexdigest()

    if (hashkey == key and client.get_groups(id=committee_invited_id, member=user)):
        members_to_remove=[user]
        profile=openreview.tools.get_profile(client, user)
        if profile:
            members_to_remove.append(profile.id)
        if (response == 'Yes'):
            if (overlap_committee_id and client.get_groups(id=overlap_committee_id, member=user)):
                client.remove_members_from_group(committee_id, members_to_remove)
                client.add_members_to_group(committee_declined_id, user)

                subject = f'[{short_phrase}] {committee_name} Invitation not accepted'
                message = f'''It seems like you already accepted an invitation to serve as a {overlap_committee_name} for {short_phrase}. If you would like to change your decision and serve as a {committee_name}, please decline the invitation to be {overlap_committee_name} and then accept the invitation to be {committee_name}.'''
                client.post_message(subject, [user], message, invitation=meta_invitation_id, signature=domain.id, replyTo=contact, sender=sender)
                return

            client.remove_members_from_group(committee_declined_id, members_to_remove)
            client.add_members_to_group(committee_id, user)

            reduced_load_subject = ' with reduced load' if reduced_load else ''
            reduced_load_text = f'''
You have selected a reduced load of {reduced_load} submissions to review.''' if reduced_load else ''

            subject = f'[{short_phrase}] {committee_name} Invitation accepted{reduced_load_subject}'
            message = f'''Thank you for accepting the invitation to be a {committee_name} for {short_phrase}.{reduced_load_text}

The {short_phrase} program chairs will be contacting you with more information regarding next steps soon. In the meantime, please add noreply@openreview.net to your email contacts to ensure that you receive all communications.

If you would like to change your decision, please follow the link in the previous invitation email and click on the "Decline" button.'''

            client.post_message(subject, [user], message, invitation=meta_invitation_id, signature=domain.id, parentGroup=committee_id, replyTo=contact, sender=sender)
            return

        if (response == 'No'):
            client.remove_members_from_group(committee_id, members_to_remove)
            client.add_members_to_group(committee_declined_id, user)

            subject = f'[{short_phrase}] {committee_name} Invitation declined'
            message = f'''You have declined the invitation to become a {committee_name} for {short_phrase}.

If you would like to change your decision, please follow the link in the previous invitation email and click on the "Accept" button.'''

            client.post_message(subject, [user], message, invitation=meta_invitation_id, signature=domain.id, parentGroup=committee_declined_id, replyTo=contact, sender=sender)

        else:
            raise openreview.OpenReviewException('Invalid response')

    else:
        raise openreview.OpenReviewException(f'Invalid key or user not in invited group: {user}')