def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    meta_invitation_id = domain.get_content_value('meta_invitation_id')
    short_name = domain.get_content_value('subtitle')
    contact = domain.get_content_value('contact')
    authors_name = domain.get_content_value('authors_name')
    submission_name = domain.get_content_value('submission_name')    
    authors_accepted_id = domain.get_content_value('authors_accepted_id') 
    decision_field_name = domain.content.get('decision_field_name', {}).get('value', 'decision')
    accept_options = domain.get_content_value('accept_decision_options')
    sender = domain.get_content_value('message_sender')   
    super_invitation = client.get_invitation(invitation.invitations[0])
    email_authors = super_invitation.get_content_value('email_authors', domain.get_content_value('decision_email_authors'))

    submission = client.get_note(edit.note.forum)
    decision = client.get_note(edit.note.id)

    action = 'posted to' if decision.tcdate == decision.tmdate else 'edited on'
    if decision.ddate:
        action = 'deleted on'

    is_accepted_decision = openreview.tools.is_accept_decision(decision.content[decision_field_name]['value'], accept_options)
    paper_group_id=f'{venue_id}/{submission_name}{submission.number}'

    paper_authors_id = f'{paper_group_id}/{authors_name}'

    openreview.tools.create_forum_invitations(client, client.get_notes(id=submission.id, details='replies')[0])
    
    if (email_authors and ('everyone' in decision.readers or paper_authors_id in decision.readers)):

        client.post_message(
            invitation=meta_invitation_id,
            recipients=[paper_authors_id],
            subject=f'''[{short_name}] Decision {action} your submission - Paper Number: {submission.number}, Paper Title: "{submission.content['title']['value']}"''',
            message=f'''To view the decision, click here: https://openreview.net/forum?id={submission.id}&noteId={decision.id}''',
            replyTo=contact,
            signature=venue_id,
            sender=sender
        )

    if (authors_accepted_id):
      if is_accepted_decision and action != 'deleted on':
        client.add_members_to_group(authors_accepted_id, paper_authors_id)
      else:
        client.remove_members_from_group(authors_accepted_id, paper_authors_id)