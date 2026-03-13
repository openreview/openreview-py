def process_update(client, edge, invitation, existing_edge):

    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    program_chairs_id = domain.content['program_chairs_id']['value']
    meta_invitation_id = domain.content['meta_invitation_id']['value']
    short_phrase = domain.content['subtitle']['value']
    contact = domain.content['contact']['value']
    sender = domain.get_content_value('message_sender')
    area_chairs_name = domain.get_content_value('area_chairs_name')
    recruitment_invitation_id = invitation.content['recruitment_invitation_id']['value']
    committee_invited_id = invitation.content['committee_invited_id']['value']
    invite_label = invitation.content['invite_label']['value']
    invited_label = invitation.content['invited_label']['value']
    hash_seed = invitation.content['hash_seed']['value']
    paper_reviewer_invited_id = invitation.content['paper_reviewer_invited_id']['value']
    email_template = invitation.content['email_template']['value']
    is_reviewer = invitation.content['is_reviewer']['value']
    is_ethics_reviewer = invitation.content.get('is_ethics_reviewer',{}).get('value', False)
    assignment_invitation_id = invitation.content['assignment_invitation_id']['value']
    assignment_label = invitation.content.get('assignment_label', {}).get('value')
    action_string = 'to review' if is_reviewer else f'to serve as {area_chairs_name.replace("_", " ")} for'
    if is_ethics_reviewer:
        action_string = 'to serve as ethics reviewer for'
    print(edge.id)

    should_get_inviter_profile = True
    if is_reviewer:
        signature_group = client.get_group(edge.signatures[0])
        reviewers_name = domain.content['reviewers_name']['value']
        reviewer_readers = [r for r in signature_group.readers if r.endswith(f'/{reviewers_name}')]   
        should_get_inviter_profile = len(reviewer_readers) > 0
    
    ## Determine if inviter should receive notifications (not venue or program chairs)
    should_notify_inviter = venue_id not in edge.signatures and program_chairs_id not in edge.signatures

    if edge.ddate is None and edge.label == invite_label and not existing_edge:

        ## Get the submission
        notes=client.get_notes(id=edge.head)
        if not notes:
            raise openreview.OpenReviewException(f'Note not found: {edge.head}')
        submission=notes[0]

        ## - Get profile
        user = edge.tail
        print(f'Get profile for {user}')
        user_profile=openreview.tools.get_profile(client, user)
        inviter_profile=openreview.tools.get_profile(client, edge.tauthor) if should_get_inviter_profile else None
        inviter_id=openreview.tools.pretty_id(edge.signatures[0])
        # When AC identity is hidden, use pretty_id for both values to avoid redundancy
        inviter_preferred_name=inviter_profile.get_preferred_name(pretty=True) if inviter_profile else inviter_id

        if not user_profile:
            user_profile=openreview.Profile(id=user,
                content={
                    'names': [],
                    'emails': [user],
                    'preferredEmail': user
                })

        preferred_name=user_profile.get_preferred_name(pretty=True)
        
        ## - Determine role name for messages
        role_name = 'reviewer'
        if not is_reviewer:
            role_name = area_chairs_name.replace('_', ' ').lower()
        if is_ethics_reviewer:
            role_name = 'ethics reviewer'
        
        ## - Check if the user is already assigned
        ## This handles the race condition where assignment happens between pre-process and post-process
        existing_assignment_edges = client.get_edges(invitation=assignment_invitation_id, head=edge.head, tail=user_profile.id, label=assignment_label)
        if existing_assignment_edges:
            print(f'User {user_profile.id} is already assigned, not sending invitation')
            ## Update edge label to "Already Assigned" instead of sending email
            edge.label = 'Already Assigned'
            edge.readers = [r if r != edge.tail else user_profile.id for r in edge.readers]
            edge.tail = user_profile.id
            edge.cdate = None
            client.post_edge(edge)
            return

        ## - Build invitation link
        print(f'Send invitation to {user_profile.id}')
        from Crypto.Hash import HMAC, SHA256
        hashkey = HMAC.new(hash_seed.encode('utf-8'), msg=user_profile.id.encode('utf-8'), digestmod=SHA256).hexdigest()
        baseurl = 'https://openreview.net' #Always pointing to the live site so we don't send more invitations with localhost

        # build the URL to send in the message
        invitation_url = f'{baseurl}/invitation?id={recruitment_invitation_id}&user={user_profile.id}&key={hashkey}&submission_id={submission.id}&inviter={inviter_profile.id if inviter_profile else edge.signatures[0]}'

        invitation_links = f'''Please respond the invitation clicking the following link:

{invitation_url}'''


        # format the message defined above
        subject=f'[{short_phrase}] Invitation {action_string} paper titled "{submission.content["title"]["value"]}"'
        if email_template:
            message=email_template.format(
                title=submission.content['title']['value'],
                number=submission.number,
                abstract=submission.content.get('abstract', {}).get('value'),
                invitation_url=invitation_url,
                inviter_id=inviter_id,
                inviter_name=inviter_preferred_name
            )
        else:
            abstract_string = f'''
Abstract: {submission.content['abstract']['value']}
''' if 'abstract' in submission.content else ''
            
            # Build signature - show only one line if inviter_id and inviter_preferred_name are the same
            signature = inviter_id if inviter_id == inviter_preferred_name else f'''{inviter_id}
{inviter_preferred_name}'''
            
            message=f'''Hi {preferred_name},

You were invited {action_string} the paper number: {submission.number}, title: "{submission.content['title']['value']}".
{abstract_string}
{invitation_links}

Thanks,

{signature}'''

        
        if paper_reviewer_invited_id:
            paper_reviewers_invited_id=paper_reviewer_invited_id.replace('{number}', str(submission.number))
            ## Paper invited group
            client.add_members_to_group(paper_reviewers_invited_id, [user_profile.id])

        if committee_invited_id:
            ## General invited group
            client.add_members_to_group(committee_invited_id, [user_profile.id])

        ## - Update edge to INVITED_LABEL
        edge.label=invited_label
        edge.readers=[r if r != edge.tail else user_profile.id for r in edge.readers]
        edge.tail=user_profile.id
        edge.cdate=None 
        
        try:
            client.post_edge(edge)
        except Exception as e:
            print(f'Error posting edge: {str(e)}')
            error_str = str(e)
            
            ## Check if error is "Already assigned" - if so, update edge label instead of sending email
            if 'already assigned' in error_str.lower():
                print(f'User {user_profile.id} is already assigned, updating edge label')
                edge.label = 'Already Assigned'
                client.post_edge(edge)
                return
            
            ## Send email to the inviter for other errors only if inviter is not venue or program chairs
            if should_notify_inviter:
                error_subject = f'[{short_phrase}] Error sending invitation for paper number {submission.number}'
                error_message = f'''Hi {inviter_preferred_name},

There was an error sending the invitation to {role_name} {preferred_name} ({user_profile.id}) for paper number {submission.number}, title: "{submission.content['title']['value']}".

Error: {error_str}

Please try again or contact support if the problem persists.

Thank you,

OpenReview Team'''
                client.post_message(error_subject, [edge.tauthor], error_message, invitation=meta_invitation_id, signature=domain.id, replyTo=contact, sender=sender)
            return

        ## - Send email after successful edge update
        response = client.post_message(subject, [user_profile.id], message, invitation=meta_invitation_id, signature=domain.id, parentGroup=committee_invited_id, replyTo=contact, sender=sender)

    if edge.ddate and edge.label == invited_label:

        ## Get the submission
        notes=client.get_notes(id=edge.head)
        if not notes:
            raise openreview.OpenReviewException(f'Note not found: {edge.head}')
        submission=notes[0]

        ## - Get profile
        user = edge.tail
        print(f'Get profile for {user}')
        user_profile=openreview.tools.get_profile(client, user)
        inviter_profile=openreview.tools.get_profile(client, edge.tauthor) if should_get_inviter_profile else None
        inviter_id=openreview.tools.pretty_id(edge.signatures[0])
        # When AC identity is hidden, use pretty_id for both values to avoid redundancy
        inviter_preferred_name=inviter_profile.get_preferred_name(pretty=True) if inviter_profile else inviter_id

        if not user_profile:
            user_profile=openreview.Profile(id=user,
                content={
                    'names': [],
                    'emails': [user],
                    'preferredEmail': user
                })

        preferred_name=user_profile.get_preferred_name(pretty=True)

        invite_assignment_invitations = client.get_edges(invitation=edge.invitation, tail=user_profile.id)
        if not invite_assignment_invitations:
            if paper_reviewer_invited_id:
                paper_reviewers_invited_id=paper_reviewer_invited_id.replace('{number}', str(submission.number))
                ## Paper invited group
                client.remove_members_from_group(paper_reviewers_invited_id, [user_profile.id])

            if committee_invited_id:
                ## General invited group
                client.remove_members_from_group(committee_invited_id, [user_profile.id])

        ## Send email
        subject=f'[{short_phrase}] Invitation canceled {action_string} paper titled "{submission.content["title"]["value"]}"'
        # Build signature - show only one line if inviter_id and inviter_preferred_name are the same
        signature = inviter_id if inviter_id == inviter_preferred_name else f'''{inviter_id}
{inviter_preferred_name}'''
        
        message=f'''Hi {preferred_name},

You were previously invited {action_string} the paper number: {submission.number}, title: "{submission.content['title']['value']}".
While we appreciate your help, we no longer need you {action_string} this paper.

Thanks,

{signature}'''

        response = client.post_message(subject, [user_profile.id], message, invitation=meta_invitation_id, signature=domain.id, replyTo=contact, sender=sender)