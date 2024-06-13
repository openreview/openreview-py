def process(client, edit, invitation):
    from Crypto.Hash import HMAC, SHA256
    import urllib.parse
    from datetime import datetime
    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    meta_invitation_id = domain.content['meta_invitation_id']['value']
    short_phrase = domain.content['subtitle']['value']
    sender = domain.get_content_value('message_sender')
    submission_name = domain.content['submission_name']['value']
    committee_name = invitation.content['committee_name']['value']
    hash_seed = invitation.content['hash_seed']['value']
    committee_id = invitation.content['committee_id']['value']
    invite_assignment_invitation_id = invitation.content['invite_assignment_invitation_id']['value']
    assignment_invitation_id = invitation.content['assignment_invitation_id']['value']
    invited_label = invitation.content['invited_label']['value']
    accepted_label = invitation.content['accepted_label']['value']
    declined_label = invitation.content['declined_label']['value']
    is_reviewer = committee_name == 'Reviewer'
    action_string = 'to review' if is_reviewer else 'to serve as area chair for'

    note= edit.note

    user = urllib.parse.unquote(note.content['user']['value'])
    hashkey = HMAC.new(hash_seed.encode(), digestmod=SHA256).update(user.encode()).hexdigest()

    if hashkey != note.content['key']['value']:
        raise openreview.OpenReviewException('Invalid key or user for {user}')

    user_profile=None
    if '@' in user:
        profiles=client.search_profiles(confirmedEmails=[user])
        user_profile=profiles.get(user)
    else:
        profiles=client.search_profiles(ids=[user])
        if profiles:
            user_profile=profiles[0]

    submission = client.get_notes(note.content['submission_id']['value'])[0]
    invitation_edges = client.get_edges(invitation=invite_assignment_invitation_id, head=submission.id, tail=user)

    if not invitation_edges:
        ## Check edge with the profile id instead
        if '@' in user and user_profile:
            invitation_edges = client.get_edges(invitation=invite_assignment_invitation_id, head=submission.id, tail=user_profile.id)
            if not invitation_edges:
                raise openreview.OpenReviewException(f'user {user} not invited')

    edge=invitation_edges[0]

    if edge.label not in [invited_label, accepted_label, 'Pending Sign Up'] and not edge.label.startswith(declined_label):
        raise openreview.OpenReviewException(f'user {user} can not reply to this invitation, invalid status {edge.label}')

    preferred_name=user_profile.get_preferred_name(pretty=True) if user_profile else edge.tail

    assignment_edges = client.get_edges(invitation=assignment_invitation_id, head=submission.id, tail=edge.tail)

    if (note.content['response']['value'] == 'Yes'):

        print('Invitation accepted', edge.tail, submission.number)

        ## Check if there is already an accepted edge for that profile id
        accepted_edges = client.get_edges(invitation=invite_assignment_invitation_id, label='Accepted', head=submission.id, tail=user_profile.id)
        if accepted_edges:
            print("User already accepted with another invitation edge", submission.id, user_profile.id)
            return

        edge.label=accepted_label
        edge.readers=[r if r != edge.tail else user_profile.id for r in edge.readers]
        edge.tail=user_profile.id
        edge.cdate=None
        client.post_edge(edge)

        if not assignment_edges:
            print('post assignment edge')
            client.post_edge(openreview.api.Edge(
                invitation=assignment_invitation_id,
                head=edge.head,
                tail=edge.tail,
                weigth = 1,
                readers=None,
                nonreaders=[
                    f'{venue_id}/{submission_name}{submission.number}/Authors'
                ],
                writers=None,
                signatures=[venue_id]
            ))

            print('send confirmation email')
            ## Send email to reviewer
            subject=f'[{short_phrase}] {committee_name} Invitation accepted for paper {submission.number}'
            message =f'''Hi {preferred_name},
Thank you for accepting the invitation {action_string} the paper number: {submission.number}, title: {submission.content['title']['value']}.

Please go to the {short_phrase} {committee_name} Console and check your pending tasks: https://openreview.net/group?id={committee_id}.

If you would like to change your decision, please click the Decline link in the previous invitation email.

OpenReview Team'''

            ## - Send email
            response = client.post_message(subject, [edge.tail], message, invitation=meta_invitation_id, signature=venue_id, sender=sender)

            ## If reviewer recruitment then send email to the assigned AC
            if is_reviewer:
                subject=f'[{short_phrase}] {committee_name} {preferred_name} accepted {action_string} paper {submission.number}'
                message =f'''Hi {{{{fullname}}}},
The {committee_name} {preferred_name} that was invited {action_string} paper {submission.number} has accepted the invitation and is now assigned to the paper {submission.number}.

OpenReview Team'''

                client.post_message(subject, [f'{venue_id}/Submission{submission.number}/Area_Chairs'], message, invitation=meta_invitation_id, signature=venue_id, sender=sender)
            return

    elif (note.content['response']['value'] == 'No'):

        print('Invitation declined', edge.tail, submission.number)
        if assignment_edges:
            print('Delete current assignment')
            assignment_edge=assignment_edges[0]
            assignment_edge.ddate=openreview.tools.datetime_millis(datetime.utcnow())
            client.post_edge(assignment_edge)


        edge.label=declined_label
        edge.cdate=None
        client.post_edge(edge)

        ## Send email to reviewer
        subject=f'[{short_phrase}] {committee_name} Invitation declined for paper {submission.number}'
        message =f'''Hi {preferred_name},
You have declined the invitation {action_string} the paper number: {submission.number}, title: {submission.content['title']['value']}.

If you would like to change your decision, please click the Accept link in the previous invitation email.

OpenReview Team'''

        ## - Send email
        response = client.post_message(subject, [edge.tail], message, invitation=meta_invitation_id, signature=venue_id, sender=sender)

        if is_reviewer:
            subject=f'[{short_phrase}] {committee_name} {preferred_name} declined {action_string} paper {submission.number}'
            message =f'''Hi {{{{fullname}}}},
The {committee_name} {preferred_name} that was invited {action_string} paper {submission.number} has declined the invitation.

Please go to the Area Chair console: https://openreview.net/group?id={venue_id}/Area_Chairs to invite another reviewer.

OpenReview Team'''

            client.post_message(subject, [f'{venue_id}/Submission{submission.number}/Area_Chairs'], message, invitation=meta_invitation_id, signature=venue_id, sender=sender)
        return

    else:
        raise openreview.OpenReviewException(f"Invalid response: {note.content['response']['value']}")
