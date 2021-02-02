def process(client, note, invitation):
    from Crypto.Hash import HMAC, SHA256
    import urllib.parse
    SHORT_PHRASE = ''
    CONFERENCE_NAME = ''
    REVIEWER_NAME = ''
    REVIEWERS_INVITED_ID = ''
    REVIEWERS_ACCEPTED_ID = ''
    REVIEWERS_DECLINED_ID = ''
    AREA_CHAIR_NAME = ''
    AREA_CHAIRS_ACCEPTED_ID = ''
    HASH_SEED = ''
    REDUCED_LOAD_INVITATION_NAME = ''

    user = urllib.parse.unquote(note.content['user'])

    hashkey = HMAC.new(HASH_SEED.encode(), digestmod=SHA256).update(user.encode()).hexdigest()
    
    invited_group = client.get_group(REVIEWERS_INVITED_ID)
    if (hashkey == note.content['key'] and user in invited_group.members):
        if (note.content['response'] == 'Yes'):
            if (AREA_CHAIRS_ACCEPTED_ID and user in client.get_group(AREA_CHAIRS_ACCEPTED_ID).members):
                client.remove_members_from_group(REVIEWERS_ACCEPTED_ID, user)
                client.add_members_to_group(REVIEWERS_DECLINED_ID, user)

                subject = '[{}] {} Invitation not accepted'.format(SHORT_PHRASE, REVIEWER_NAME)
                message = '''It seems like you already accepted an invitation to serve as a {} for {}. If you would like to change your decision and serve as a {}, please click the Decline link in the {} invitation email and click the Accept link in the {} invitation email.'''.format(AREA_CHAIR_NAME, SHORT_PHRASE, REVIEWER_NAME, AREA_CHAIR_NAME, REVIEWER_NAME)
                client.post_message(subject, [user], message)

            else:
                client.remove_members_from_group(REVIEWERS_DECLINED_ID, user)
                client.add_members_to_group(REVIEWERS_ACCEPTED_ID, user)

                subject = '[{}] {} Invitation accepted'.format(SHORT_PHRASE, REVIEWER_NAME)
                message = '''Thank you for accepting the invitation to be a {} for {}.
The {} program chairs will be contacting you with more information regarding next steps soon. In the meantime, please add noreply@openreview.net to your email contacts to ensure that you receive all communications.

If you would like to change your decision, please click the Decline link in the previous invitation email.'''.format(REVIEWER_NAME, SHORT_PHRASE, SHORT_PHRASE)
            
                client.post_message(subject, [user], message, parentGroup=REVIEWERS_ACCEPTED_ID)

        elif (note.content['response'] == 'No'):
            client.remove_members_from_group(REVIEWERS_ACCEPTED_ID, user)
            client.add_members_to_group(REVIEWERS_DECLINED_ID, user)

            subject = '[{}] {} Invitation declined'.format(SHORT_PHRASE, REVIEWER_NAME)
            message = '''You have declined the invitation to become a {} for {}.

If you would like to change your decision, please click the Accept link in the previous invitation email.

'''.format(REVIEWER_NAME, SHORT_PHRASE)

            if (REDUCED_LOAD_INVITATION_NAME):
                message += 'In case you only declined because you think you cannot handle the maximum load of papers, you can reduce your load slightly. Be aware that this will decrease your overall score for an outstanding reviewer award, since all good reviews will accumulate a positive score. You can request a reduced reviewer load by clicking here: https://openreview.net/invitation?id={}/-/{}&user={}&key={}'.format(CONFERENCE_NAME, REDUCED_LOAD_INVITATION_NAME, user, note.content['key'])

            client.post_message(subject, [user], message, parentGroup=REVIEWERS_DECLINED_ID)