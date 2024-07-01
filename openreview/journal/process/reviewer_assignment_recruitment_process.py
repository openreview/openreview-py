def process(client, edit, invitation):
    from Crypto.Hash import HMAC, SHA256
    import urllib.parse
    from datetime import datetime


    journal = openreview.journal.Journal()

    venue_id = journal.venue_id
    short_phrase = journal.short_name
    submission_name = journal.submission_name
    committee_name = journal.reviewers_name
    hash_seed = journal.secret_key
    committee_id = journal.get_reviewers_id()
    invite_assignment_invitation_id = journal.get_reviewer_invite_assignment_id()
    assignment_invitation_id = journal.get_reviewer_assignment_id()
    invited_label = 'Invitation Sent'
    accepted_label = 'Accepted'
    declined_label = 'Declined'
    conflict_policy = 'NeurIPS'
    conflict_n_years = 3
    note = edit.note

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

    if not invitation_edges and user_profile:
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

        decline_instructions = 'If you would like to change your decision, please follow the link in the previous invitation email and click on the "Decline" button.'

        if not user_profile or user_profile.active == False:
            edge.label='Pending Sign Up'
            edge.cdate=None
            client.post_edge(edge)

            ## Send email to reviewer
            subject=f'[{short_phrase}] {committee_name} Invitation accepted for paper {submission.number}: {submission.content["title"]["value"]}, assignment pending'
            message =f'''Hi {preferred_name},
Thank you for accepting the invitation to review the paper number: {submission.number}, title: {submission.content['title']['value']}.

Please signup in OpenReview using the email address {edge.tail} and complete your profile.
Confirmation of the assignment is pending until your profile is active and no conflicts of interest are detected.

{decline_instructions}

OpenReview Team'''
            response = client.post_message(subject, [edge.tail], message, invitation=journal.get_meta_invitation_id(), signature=venue_id, replyTo=journal.contact_info, sender=journal.get_message_sender())

            ## Send email to inviter
            subject=f'[{short_phrase}] {committee_name} {preferred_name} accepted to review paper {submission.number}: {submission.content["title"]["value"]}, assignment pending'
            message =f'''Hi {{{{fullname}}}},
The {committee_name} {preferred_name} that you invited to review paper {submission.number} has accepted the invitation.

Confirmation of the assignment is pending until the invited reviewer creates a profile in OpenReview and no conflicts of interest are detected.

OpenReview Team'''

            ## - Send email
            response = client.post_message(subject, edge.signatures, message, invitation=journal.get_meta_invitation_id(), signature=venue_id, replyTo=journal.contact_info, sender=journal.get_message_sender())
            return

        ## Check if there is already an accepted edge for that profile id
        accepted_edges = client.get_edges(invitation=invite_assignment_invitation_id, label='Accepted', head=submission.id, tail=user_profile.id)
        if accepted_edges:
            print("User already accepted with another invitation edge", submission.id, user_profile.id)
            return

        ## - Check conflicts
        authorids = submission.content['authorids']['value']
        author_profiles = openreview.tools.get_profiles(client, authorids, with_publications=True)
        profiles=openreview.tools.get_profiles(client, [edge.tail], with_publications=True)
        conflicts=openreview.tools.get_conflicts(author_profiles, profiles[0], policy=conflict_policy, n_years=conflict_n_years)
        if conflicts:
            print('Conflicts detected', conflicts)
            edge.label='Conflict Detected'
            edge.readers=[r if r != edge.tail else user_profile.id for r in edge.readers]
            edge.tail=user_profile.id
            edge.cdate=None
            client.post_edge(edge)

            ## Send email to reviewer
            subject=f'[{short_phrase}] Conflict detected for paper {submission.number}: {submission.content["title"]["value"]}'
            message =f'''Hi {{{{fullname}}}},
You have accepted the invitation to review the paper number: {submission.number}, title: {submission.content['title']['value']}.

A conflict was detected between you and the submission authors and the assignment can not be done.

If you have any questions, please contact us as info@openreview.net.

OpenReview Team'''
            response = client.post_message(subject, [edge.tail], message, invitation=journal.get_meta_invitation_id(), signature=venue_id, replyTo=journal.contact_info, sender=journal.get_message_sender())

            ## Send email to inviter
            subject=f'[{short_phrase}] Conflict detected between {committee_name} {preferred_name} and paper {submission.number}: {submission.content["title"]["value"]}'
            message =f'''Hi {{{{fullname}}}},
A conflict was detected between {preferred_name} and the paper {submission.number} and the assignment can not be done.

If you have any questions, please contact us as info@openreview.net.

OpenReview Team'''

            ## - Send email
            response = client.post_message(subject, edge.signatures, message, invitation=journal.get_meta_invitation_id(), signature=venue_id, replyTo=journal.contact_info, sender=journal.get_message_sender())
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
                weight = 1,
                signatures=[venue_id]
            ))

            instructions=f'Please go to the Tasks page and check your {short_phrase} pending tasks: https://openreview.net/tasks'

            print('send confirmation email')
            ## Send email to reviewer
            subject=f'[{short_phrase}] {committee_name} Invitation accepted for paper {submission.number}: {submission.content["title"]["value"]}'
            message =f'''Hi {preferred_name},
Thank you for accepting the invitation to review the paper number: {submission.number}, title: {submission.content['title']['value']}.

{instructions}

{decline_instructions}

OpenReview Team'''

            ## - Send email
            response = client.post_message(subject, [edge.tail], message, invitation=journal.get_meta_invitation_id(), signature=venue_id, replyTo=journal.contact_info, sender=journal.get_message_sender())

            ## Send email to inviter
            subject=f'[{short_phrase}] {committee_name} {preferred_name} accepted to review paper {submission.number}: {submission.content["title"]["value"]}'
            message =f'''Hi {{{{fullname}}}},
The {committee_name} {preferred_name} that you invited to review paper {submission.number} has accepted the invitation and is now assigned to the paper {submission.number}.

OpenReview Team'''

            ## - Send email
            response = client.post_message(subject, edge.signatures, message, invitation=journal.get_meta_invitation_id(), signature=venue_id, replyTo=journal.contact_info, sender=journal.get_message_sender())


    elif (note.content['response']['value'] == 'No'):

        print('Invitation declined', edge.tail, submission.number)
        accept_instructions = 'If you would like to change your decision, please follow the link in the previous invitation email and click on the "Accept" button.'

        if assignment_edges:
            print('Delete current assignment')
            assignment_edge=assignment_edges[0]
            assignment_edge.ddate=openreview.tools.datetime_millis(datetime.utcnow())
            client.post_edge(assignment_edge)


        edge.label=declined_label
        if 'comment' in note.content:
            edge.label=edge.label + ': ' + note.content['comment']['value']
        edge.cdate=None
        client.post_edge(edge)

        ## Send email to reviewer
        subject=f'[{short_phrase}] {committee_name} Invitation declined for paper {submission.number}: {submission.content["title"]["value"]}'
        message =f'''Hi {preferred_name},
You have declined the invitation to review the paper number: {submission.number}, title: {submission.content['title']['value']}.

{accept_instructions}

OpenReview Team'''

        ## - Send email
        response = client.post_message(subject, [edge.tail], message, invitation=journal.get_meta_invitation_id(), signature=venue_id, replyTo=journal.contact_info, sender=journal.get_message_sender())

        ## Send email to inviter
        subject=f'[{short_phrase}] {committee_name} {preferred_name} declined to review paper {submission.number}: {submission.content["title"]["value"]}'
        message =f'''Hi {{{{fullname}}}},
The {committee_name} {preferred_name} that you invited to review paper {submission.number} has declined the invitation.

To read their response, please click here: https://openreview.net/forum?id={note.id}

OpenReview Team'''

        ## - Send email
        response = client.post_message(subject, edge.signatures, message, invitation=journal.get_meta_invitation_id(), signature=venue_id, replyTo=journal.contact_info, sender=journal.get_message_sender())

    else:
        raise openreview.OpenReviewException(f"Invalid response: {note.content['response']['value']}")
