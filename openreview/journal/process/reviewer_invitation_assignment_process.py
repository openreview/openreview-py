def process(client, edge, invitation):

    journal = openreview.journal.Journal()

    short_phrase = journal.short_name
    recruitment_invitation_id = journal.get_reviewer_assignment_recruitment_id()
    invite_label = 'Invitation Sent'
    hash_seed = journal.secret_key
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
        subject=f'[{short_phrase}] Invitation to review paper titled "{submission.content["title"]["value"]}"'
        message=f'''Hi {{{{fullname}}}},

You were invited to review the paper number: {submission.number}, title: "{submission.content['title']['value']}".

Abstract: {submission.content['abstract']['value']}

{invitation_links}

Thanks,

{inviter_id}
{inviter_preferred_name}'''

        
        ## - Send email
        response = client.post_message(subject, [user_profile.id], message, invitation=journal.get_meta_invitation_id(), signature=journal.venue_id, replyTo=inviter_profile.get_preferred_name(), sender=journal.get_message_sender())

        ## - Update edge to INVITED_LABEL
        edge.label=invite_label
        edge.readers=[r if r != edge.tail else user_profile.id for r in edge.readers]
        edge.tail=user_profile.id
        edge.cdate=None 
        client.post_edge(edge)