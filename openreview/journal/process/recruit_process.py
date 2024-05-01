def process(client, edit, invitation):
    from Crypto.Hash import HMAC, SHA256
    import urllib.parse
    SHORT_PHRASE = ''
    ACTION_EDITOR_NAME = ''
    ACTION_EDITOR_INVITED_ID = ''
    ACTION_EDITOR_ACCEPTED_ID = ''
    ACTION_EDITOR_DECLINED_ID = ''
    HASH_SEED = ''
    JOURNAL_REQUEST_ID = ''
    SUPPORT_GROUP = ''
    VENUE_ID = ''

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

    if hashkey == key and client.get_groups(id=ACTION_EDITOR_INVITED_ID, member=user):
        if (response == 'Yes'):
            action = 'accepted'
            client.remove_members_from_group(ACTION_EDITOR_DECLINED_ID, user)
            client.add_members_to_group(ACTION_EDITOR_ACCEPTED_ID, user)

            subject = '[{SHORT_PHRASE}] {SHORT_PHRASE} Invitation accepted'.format(SHORT_PHRASE=SHORT_PHRASE, ACTION_EDITOR_NAME=ACTION_EDITOR_NAME)
            message = '''Thank you for accepting the invitation to be a {ACTION_EDITOR_NAME} for {SHORT_PHRASE}.
The {SHORT_PHRASE} editors in chief will be contacting you with more information regarding next steps soon. In the meantime, please add noreply@openreview.net to your email contacts to ensure that you receive all communications.

If you would like to change your decision, please click the Decline link in the previous invitation email.'''.format(SHORT_PHRASE=SHORT_PHRASE, ACTION_EDITOR_NAME=ACTION_EDITOR_NAME)

            response =  client.post_message(subject, [user], message, invitation=f'{edit.domain}/-/Edit', signature=edit.domain, parentGroup=ACTION_EDITOR_ACCEPTED_ID)

        elif (response == 'No'):
            action = 'declined'
            client.remove_members_from_group(ACTION_EDITOR_ACCEPTED_ID, user)
            client.add_members_to_group(ACTION_EDITOR_DECLINED_ID, user)

            subject = '[{SHORT_PHRASE}] {SHORT_PHRASE} Invitation declined'.format(SHORT_PHRASE=SHORT_PHRASE, ACTION_EDITOR_NAME=ACTION_EDITOR_NAME)
            message = '''You have declined the invitation to become a {ACTION_EDITOR_NAME} for {SHORT_PHRASE}.

If you would like to change your decision, please click the Accept link in the previous invitation email.

'''.format(ACTION_EDITOR_NAME=ACTION_EDITOR_NAME, SHORT_PHRASE=SHORT_PHRASE)

            response =  client.post_message(subject, [user], message, invitation=f'{edit.domain}/-/Edit', signature=edit.domain, parentGroup=ACTION_EDITOR_DECLINED_ID)

        if JOURNAL_REQUEST_ID:
            journal_request = client.get_note(JOURNAL_REQUEST_ID)
            recruitment_notes = list(openreview.tools.iterget_notes(client, invitation=f'{SUPPORT_GROUP}/Journal_Request{journal_request.number}/-/Reviewer_Recruitment_by_AE', replyto=JOURNAL_REQUEST_ID, sort='number:desc'))
            for note in recruitment_notes:
                invitee = note.content['invitee_email']['value'].strip()
                invitee_ids = [invitee]
                invitee_profile = openreview.tools.get_profile(client, invitee)
                if invitee_profile:
                    invitee_ids.append(invitee_profile.id)
                id_or_email = user
                if '~' in user:
                    profile = openreview.tools.get_profile(client, user)
                    id_or_email = profile.id
                if id_or_email in invitee_ids:
                    comment_inv = client.get_invitation(id=f'{SUPPORT_GROUP}/Journal_Request{journal_request.number}/-/Comment')
                    comment_content = f'''The user {invitee} has {action} an invitation to be a reviewer for {SHORT_PHRASE}.'''
                    recruitment_response_notes = list(openreview.tools.iterget_notes(client, replyto=note.id, sort='number:desc'))
                    if recruitment_response_notes and 'New Recruitment Response' in recruitment_response_notes[0].content['title']['value']:
                        posted_recruitment_response = recruitment_response_notes[0]
                        revision = client.post_note_edit(invitation=comment_inv.id,
                            signatures = [VENUE_ID],
                            note = openreview.api.Note(id=posted_recruitment_response.id,
                                                        replyto=posted_recruitment_response.replyto,
                                                        readers=posted_recruitment_response.readers,
                                                        content = {
                                                            'title': posted_recruitment_response.content['title'],
                                                            'comment': { 'value': comment_content }
                                                        }
                        ))
                    else:
                        #post new comment to journal request
                        recruitment_inv = note.invitations[0]
                        comment = client.post_note_edit(invitation=comment_inv.id,
                            signatures=[VENUE_ID],
                            note = openreview.api.Note(
                                content = {
                                    'title': { 'value': 'New Recruitment Response'},
                                    'comment': { 'value': comment_content}
                                },
                                forum = JOURNAL_REQUEST_ID,
                                replyto = note.id,
                                readers = note.readers
                            ))
                    return response

        return response
    else:
        raise openreview.OpenReviewException(f'Invalid key or user no invited {user}')