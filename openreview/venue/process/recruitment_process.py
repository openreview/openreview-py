def process(client, edit, invitation):
    from Crypto.Hash import HMAC, SHA256
    import urllib.parse
    SHORT_PHRASE = ''
    REVIEWER_NAME = ''
    REVIEWERS_INVITED_ID = ''
    REVIEWERS_ACCEPTED_ID = ''
    REVIEWERS_DECLINED_ID = ''
    AREA_CHAIR_NAME = ''
    AREA_CHAIRS_ACCEPTED_ID = ''

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

    if (hashkey == key and client.get_groups(id=REVIEWERS_INVITED_ID, member=user)):
        members_to_remove=[user]
        profile=openreview.tools.get_profile(client, user)
        if profile:
            members_to_remove.append(profile.id)
        if (response == 'Yes'):
            if (AREA_CHAIRS_ACCEPTED_ID and client.get_groups(id=AREA_CHAIRS_ACCEPTED_ID, member=user)):
                client.remove_members_from_group(REVIEWERS_ACCEPTED_ID, members_to_remove)
                client.add_members_to_group(REVIEWERS_DECLINED_ID, user)

                subject = f'[{SHORT_PHRASE}] {REVIEWER_NAME} Invitation not accepted'
                message = f'''It seems like you already accepted an invitation to serve as a {AREA_CHAIR_NAME} for {SHORT_PHRASE}. If you would like to change your decision and serve as a {REVIEWER_NAME}, please decline the invitation to be {AREA_CHAIR_NAME} and then accept the inviation to be {REVIEWER_NAME}.'''
                client.post_message(subject, [user], message)
                return

            client.remove_members_from_group(REVIEWERS_DECLINED_ID, members_to_remove)
            client.add_members_to_group(REVIEWERS_ACCEPTED_ID, user)

            reduced_load_subject = ' with reduced load' if reduced_load else ''
            reduced_load_text = f'''
You have selected a reduced load of {reduced_load} submissions to review.''' if reduced_load else ''

            subject = f'[{SHORT_PHRASE}] {REVIEWER_NAME} Invitation accepted{reduced_load_subject}'
            message = f'''Thank you for accepting the invitation to be a {REVIEWER_NAME} for {SHORT_PHRASE}.{reduced_load_text}

The {SHORT_PHRASE} program chairs will be contacting you with more information regarding next steps soon. In the meantime, please add noreply@openreview.net to your email contacts to ensure that you receive all communications.

If you would like to change your decision, please follow the link in the previous invitation email and click on the "Decline" button.'''

            client.post_message(subject, [user], message, parentGroup=REVIEWERS_ACCEPTED_ID)
            return

        if (response == 'No'):
            client.remove_members_from_group(REVIEWERS_ACCEPTED_ID, members_to_remove)
            client.add_members_to_group(REVIEWERS_DECLINED_ID, user)

            subject = f'[{SHORT_PHRASE}] {REVIEWER_NAME} Invitation declined'
            message = f'''You have declined the invitation to become a {REVIEWER_NAME} for {SHORT_PHRASE}.

If you would like to change your decision, please follow the link in the previous invitation email and click on the "Accept" button.'''

            client.post_message(subject, [user], message, parentGroup=REVIEWERS_DECLINED_ID)

        else:
            raise openreview.OpenReviewException('Invalid response')

    else:
        raise openreview.OpenReviewException(f'Invalid key or user not in invited group: {user}')