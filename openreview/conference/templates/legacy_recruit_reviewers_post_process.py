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
    ACCEPT_EMAIL_TEMPLATE = ''

    user = urllib.parse.unquote(note.content['user'])

    hashkey = HMAC.new(HASH_SEED.encode(), digestmod=SHA256).update(user.encode()).hexdigest()

    if (hashkey == note.content['key'] and client.get_groups(id=REVIEWERS_INVITED_ID, member=user)):
        members_to_remove=[user]
        profile=openreview.tools.get_profile(client, user)
        if profile:
            members_to_remove.append(profile.id)
        if (note.content['response'] == 'Yes'):
            if (AREA_CHAIRS_ACCEPTED_ID and client.get_groups(id=AREA_CHAIRS_ACCEPTED_ID, member=user)):
                client.remove_members_from_group(REVIEWERS_ACCEPTED_ID, members_to_remove)
                client.add_members_to_group(REVIEWERS_DECLINED_ID, user)

                subject = '[{}] {} Invitation not accepted'.format(SHORT_PHRASE, REVIEWER_NAME)
                message = '''It seems like you already accepted an invitation to serve as a {alternate_role} for {venue}. If you would like to change your decision and serve as a {role}, please click the Decline link in the {alternate_role} invitation email and click the Accept link in the {role} invitation email.'''.format(alternate_role=AREA_CHAIR_NAME, venue=SHORT_PHRASE, role=REVIEWER_NAME)
                client.post_message(subject, [user], message)

            else:
                client.remove_members_from_group(REVIEWERS_DECLINED_ID, members_to_remove)
                client.add_members_to_group(REVIEWERS_ACCEPTED_ID, user)

                subject = '[{}] {} Invitation accepted'.format(SHORT_PHRASE, REVIEWER_NAME)
                if ACCEPT_EMAIL_TEMPLATE:
                    message = ACCEPT_EMAIL_TEMPLATE.format(role=REVIEWER_NAME)
                else:
                    message = '''Thank you for accepting the invitation to be a {role} for {venue}.
The {venue} program chairs will be contacting you with more information regarding next steps soon. In the meantime, please add noreply@openreview.net to your email contacts to ensure that you receive all communications.

If you would like to change your decision, please click the Decline link in the previous invitation email.'''.format(role=REVIEWER_NAME, venue=SHORT_PHRASE)

                client.post_message(subject, [user], message, parentGroup=REVIEWERS_ACCEPTED_ID)

        elif (note.content['response'] == 'No'):
            client.remove_members_from_group(REVIEWERS_ACCEPTED_ID, members_to_remove)
            client.add_members_to_group(REVIEWERS_DECLINED_ID, user)

            subject = '[{}] {} Invitation declined'.format(SHORT_PHRASE, REVIEWER_NAME)
            message = '''You have declined the invitation to become a {} for {}.

If you would like to change your decision, please click the Accept link in the previous invitation email.

'''.format(REVIEWER_NAME, SHORT_PHRASE)

            if (REDUCED_LOAD_INVITATION_NAME):
                role = REVIEWER_NAME.replace(' ', '_') + 's'
                REDUCED_LOAD_INVITATION_ID = f'{CONFERENCE_NAME}/{role}/-/{REDUCED_LOAD_INVITATION_NAME}'
                message += 'In case you only declined because you think you cannot handle the maximum load of papers, you can reduce your load slightly. Be aware that this will decrease your overall score for an outstanding reviewer award, since all good reviews will accumulate a positive score. You can request a reduced reviewer load by clicking here: https://openreview.net/invitation?id={}&user={}&key={}'.format(REDUCED_LOAD_INVITATION_ID, user, note.content['key'])

            client.post_message(subject, [user], message, parentGroup=REVIEWERS_DECLINED_ID)

        else:
            raise openreview.OpenReviewException('Invalid response')

    else:
        raise openreview.OpenReviewException(f'Invalid key or user not in invited group: {user}')