def process(client, edit, invitation):
    from Crypto.Hash import HMAC, SHA256
    import urllib.parse
    SHORT_PHRASE = ''
    ACTION_EDITOR_NAME = ''
    ACTION_EDITOR_INVITED_ID = ''
    ACTION_EDITOR_ACCEPTED_ID = ''
    ACTION_EDITOR_DECLINED_ID = ''
    HASH_SEED = ''

    note=edit.note
    user = urllib.parse.unquote(note.content['user']['value'])

    hashkey = HMAC.new(HASH_SEED.encode(), digestmod=SHA256).update(user.encode()).hexdigest()

    if (hashkey == note.content['key']['value'] and client.get_groups(regex=ACTION_EDITOR_INVITED_ID, member=user)):
        if (note.content['response']['value'] == 'Yes'):
            client.remove_members_from_group(ACTION_EDITOR_DECLINED_ID, user)
            client.add_members_to_group(ACTION_EDITOR_ACCEPTED_ID, user)

            subject = '[{SHORT_PHRASE}] {SHORT_PHRASE} Invitation accepted'.format(SHORT_PHRASE=SHORT_PHRASE, ACTION_EDITOR_NAME=ACTION_EDITOR_NAME)
            message = '''Thank you for accepting the invitation to be a {ACTION_EDITOR_NAME} for {SHORT_PHRASE}.
The {SHORT_PHRASE} editors in chief will be contacting you with more information regarding next steps soon. In the meantime, please add noreply@openreview.net to your email contacts to ensure that you receive all communications.

If you would like to change your decision, please click the Decline link in the previous invitation email.'''.format(SHORT_PHRASE=SHORT_PHRASE, ACTION_EDITOR_NAME=ACTION_EDITOR_NAME)

            return client.post_message(subject, [user], message, parentGroup=ACTION_EDITOR_ACCEPTED_ID)

        if (note.content['response']['value'] == 'No'):
            client.remove_members_from_group(ACTION_EDITOR_ACCEPTED_ID, user)
            client.add_members_to_group(ACTION_EDITOR_DECLINED_ID, user)

            subject = '[{SHORT_PHRASE}] {SHORT_PHRASE} Invitation declined'.format(SHORT_PHRASE=SHORT_PHRASE, ACTION_EDITOR_NAME=ACTION_EDITOR_NAME)
            message = '''You have declined the invitation to become a {ACTION_EDITOR_NAME} for {SHORT_PHRASE}.

If you would like to change your decision, please click the Accept link in the previous invitation email.

'''.format(ACTION_EDITOR_NAME=ACTION_EDITOR_NAME, SHORT_PHRASE=SHORT_PHRASE)

            return client.post_message(subject, [user], message, parentGroup=REVIEWERS_DECLINED_ID)
    else:
        raise OpenReviewException(f'Invalid key or user no invited {user}')