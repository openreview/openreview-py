def process_update(client, edge, invitation, existing_edge):

    domain = client.get_group(invitation.domain)
    meta_invitation_id = domain.content['meta_invitation_id']['value']
    short_phrase = domain.content['subtitle']['value']
    contact = domain.content['contact']['value']
    sender = domain.get_content_value('message_sender')
    recruitment_invitation_id = invitation.content['recruitment_invitation_id']['value']
    committee_invited_id = invitation.content['committee_invited_id']['value']
    invite_label = invitation.content['invite_label']['value']
    invited_label = invitation.content['invited_label']['value']
    hash_seed = invitation.content['hash_seed']['value']
    paper_reviewer_invited_id = invitation.content['paper_reviewer_invited_id']['value']
    email_template = invitation.content['email_template']['value']
    is_reviewer = invitation.content['is_reviewer']['value']
    is_ethics_reviewer = invitation.content.get('is_ethics_reviewer',{}).get('value', False)
    action_string = 'to review' if is_reviewer else 'to serve as area chair for'
    if is_ethics_reviewer:
        action_string = 'to serve as ethics reviewer for'
    print(edge.id)

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
        inviter_id=openreview.tools.pretty_id(edge.signatures[0])
        inviter_profile=openreview.tools.get_profile(client, edge.tauthor)
        inviter_preferred_name=inviter_profile.get_preferred_name(pretty=True) if inviter_profile else edge.signatures[0]

        if not user_profile:
            user_profile=openreview.Profile(id=user,
                content={
                    'names': [],
                    'emails': [user],
                    'preferredEmail': user
                })

        preferred_name=user_profile.get_preferred_name(pretty=True)

        ## - Build invitation link
        print(f'Send invitation to {user_profile.id}')
        from Crypto.Hash import HMAC, SHA256
        hashkey = HMAC.new(hash_seed.encode('utf-8'), msg=user_profile.id.encode('utf-8'), digestmod=SHA256).hexdigest()
        baseurl = 'https://openreview.net' #Always pointing to the live site so we don't send more invitations with localhost

        # build the URL to send in the message
        invitation_url = f'{baseurl}/invitation?id={recruitment_invitation_id}&user={user_profile.id}&key={hashkey}&submission_id={submission.id}&inviter={inviter_profile.id}'

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
            
            message=f'''Hi {preferred_name},

You were invited {action_string} the paper number: {submission.number}, title: "{submission.content['title']['value']}".
{abstract_string}
{invitation_links}

Thanks,

{inviter_id}
{inviter_preferred_name}'''

        
        if paper_reviewer_invited_id:
            paper_reviewers_invited_id=paper_reviewer_invited_id.replace('{number}', str(submission.number))
            ## Paper invited group
            client.add_members_to_group(paper_reviewers_invited_id, [user_profile.id])

        if committee_invited_id:
            ## General invited group
            client.add_members_to_group(committee_invited_id, [user_profile.id])

        ## - Send email
        response = client.post_message(subject, [user_profile.id], message, invitation=meta_invitation_id, signature=domain.id, parentGroup=committee_invited_id, replyTo=contact, sender=sender)

        ## - Update edge to INVITED_LABEL
        edge.label=invited_label
        edge.readers=[r if r != edge.tail else user_profile.id for r in edge.readers]
        edge.tail=user_profile.id
        edge.cdate=None 
        client.post_edge(edge)

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
        inviter_id=openreview.tools.pretty_id(edge.signatures[0])
        inviter_profile=openreview.tools.get_profile(client, edge.tauthor)
        inviter_preferred_name=inviter_profile.get_preferred_name(pretty=True) if inviter_profile else edge.signatures[0]

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
        message=f'''Hi {preferred_name},

You were previously invited {action_string} the paper number: {submission.number}, title: "{submission.content['title']['value']}".
While we appreciate your help, we no longer need you {action_string} this paper.

Thanks,

{inviter_id}
{inviter_preferred_name}'''

        response = client.post_message(subject, [user_profile.id], message, invitation=meta_invitation_id, signature=domain.id, replyTo=contact, sender=sender)