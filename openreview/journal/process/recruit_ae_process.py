def process(client, edit, invitation):
    from Crypto.Hash import HMAC, SHA256
    import urllib.parse
    SHORT_PHRASE = ''
    ACTION_EDITOR_NAME = ''
    ACTION_EDITOR_INVITED_ID = ''
    ACTION_EDITOR_ACCEPTED_ID = ''
    ACTION_EDITOR_DECLINED_ID = ''
    HASH_SEED = ''

    if hasattr(edit, 'note'):
        note=edit.note
        user=note.content['user']['value']
        key=note.content['key']['value']
        response=note.content['response']['value']
    else:
        user=note.content['user']
        key=note.content['key']
        response=note.content['response']

    user = urllib.parse.unquote(user)

    hashkey = HMAC.new(HASH_SEED.encode(), digestmod=SHA256).update(user.encode()).hexdigest()

    if hashkey == key and client.get_groups(prefix=ACTION_EDITOR_INVITED_ID, member=user):
        if (response == 'Yes'):
            client.remove_members_from_group(ACTION_EDITOR_DECLINED_ID, user)
            client.add_members_to_group(ACTION_EDITOR_ACCEPTED_ID, user)

            subject = '[{SHORT_PHRASE}] {SHORT_PHRASE} Invitation accepted'.format(SHORT_PHRASE=SHORT_PHRASE, ACTION_EDITOR_NAME=ACTION_EDITOR_NAME)
            message = '''Thank you for accepting the invitation to be an {ACTION_EDITOR_NAME} for {SHORT_PHRASE}.
The {SHORT_PHRASE} editors in chief will be contacting you with more information regarding next steps soon. In the meantime, please add noreply@openreview.net to your email contacts to ensure that you receive all communications.

If you would like to change your decision, please click the Decline link in the previous invitation email.'''.format(SHORT_PHRASE=SHORT_PHRASE, ACTION_EDITOR_NAME=ACTION_EDITOR_NAME)

            return client.post_message(subject, [user], message, invitation=f'{edit.domain}/-/Edit', signature=edit.domain, parentGroup=ACTION_EDITOR_ACCEPTED_ID)

        if (response == 'No'):
            client.remove_members_from_group(ACTION_EDITOR_ACCEPTED_ID, user)
            client.add_members_to_group(ACTION_EDITOR_DECLINED_ID, user)

            subject = '[{SHORT_PHRASE}] {SHORT_PHRASE} Invitation declined'.format(SHORT_PHRASE=SHORT_PHRASE, ACTION_EDITOR_NAME=ACTION_EDITOR_NAME)
            message = '''You have declined the invitation to become an {ACTION_EDITOR_NAME} for {SHORT_PHRASE}.

If you would like to change your decision, please click the Accept link in the previous invitation email.

'''.format(ACTION_EDITOR_NAME=ACTION_EDITOR_NAME, SHORT_PHRASE=SHORT_PHRASE)

            return client.post_message(subject, [user], message, invitation=f'{edit.domain}/-/Edit', signature=edit.domain, parentGroup=ACTION_EDITOR_DECLINED_ID)
    else:
        raise openreview.OpenReviewException(f'Invalid key or user no invited {user}')