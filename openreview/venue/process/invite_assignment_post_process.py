def process(client, edge, invitation):

    domain = client.get_group(invitation.domain)
    short_phrase = domain.content['subtitle']['value']
    recruitment_invitation_id = invitation.content['recruitment_invitation_id']['value']
    committee_invited_id = invitation.content['committee_invited_id']['value']
    invite_label = invitation.content['invite_label']['value']
    invited_label = invitation.content['invited_label']['value']
    hash_seed = invitation.content['hash_seed']['value']
    assignment_invitation_id = invitation.content['assignment_invitation_id']['value']
    paper_reviewer_invited_id = invitation.content['paper_reviewer_invited_id']['value']
    email_template = invitation.content['email_template']['value']
    is_reviewer = 'Reviewers' in assignment_invitation_id
    action_string = 'to review' if is_reviewer else 'to serve as area chair for'
    print(edge.id)

    if edge.ddate is None and edge.label == invite_label:

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
        invitation_url = f'{baseurl}/invitation?id={recruitment_invitation_id}&user={user_profile.id}&key={hashkey}&submission_id={submission.id}&inviter={edge.tauthor}'

        invitation_links = f'''Please respond the invitation clicking the following link:

{invitation_url}'''


        # format the message defined above
        subject=f'[{short_phrase}] Invitation {action_string} paper titled "{submission.content["title"]["value"]}"'
        if email_template:
            message=email_template.format(
                title=submission.content['title']['value'],
                number=submission.number,
                abstract=submission.content['abstract']['value'],
                invitation_url=invitation_url,
                inviter_id=inviter_id,
                inviter_name=inviter_preferred_name,
                inviter_email=edge.tauthor
            )
        else:
            message=f'''Hi {preferred_name},

You were invited {action_string} the paper number: {submission.number}, title: "{submission.content['title']['value']}".

Abstract: {submission.content['abstract']['value']}

{invitation_links}

Thanks,

{inviter_id}
{inviter_preferred_name} ({edge.tauthor})'''

        
        if paper_reviewer_invited_id:
            paper_reviewers_invited_id=paper_reviewer_invited_id.replace('{number}', str(submission.number))
            ## Paper invited group
            client.add_members_to_group(paper_reviewers_invited_id, [user_profile.id])

        if committee_invited_id:
            ## General invited group
            client.add_members_to_group(committee_invited_id, [user_profile.id])

        ## - Send email
        response = client.post_message(subject, [user_profile.id], message, parentGroup=committee_invited_id)

        ## - Update edge to INVITED_LABEL
        edge.label=invited_label
        edge.readers=[r if r != edge.tail else user_profile.id for r in edge.readers]
        edge.tail=user_profile.id
        edge.cdate=None 
        client.post_edge(edge)