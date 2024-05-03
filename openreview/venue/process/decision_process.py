def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    meta_invitation_id = domain.get_content_value('meta_invitation_id')
    short_name = domain.get_content_value('subtitle')
    contact = domain.get_content_value('contact')
    authors_name = domain.get_content_value('authors_name')
    submission_name = domain.get_content_value('submission_name')    
    authors_accepted_id = domain.get_content_value('authors_accepted_id') 
    sender = domain.get_content_value('message_sender')   

    submission = client.get_note(edit.note.forum)
    decision = client.get_note(edit.note.id)
    paper_group_id=f'{venue_id}/{submission_name}{submission.number}'

    paper_authors_id = f'{paper_group_id}/{authors_name}'

    action = 'posted to' if decision.tcdate == decision.tmdate else 'edited on'

    if (domain.get_content_value('decision_email_authors') and ('everyone' in decision.readers or paper_authors_id in decision.readers)):

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
      accept_options = domain.get_content_value('accept_decision_options')
      if openreview.tools.is_accept_decision(decision.content['decision']['value'], accept_options):
        client.add_members_to_group(authors_accepted_id, paper_authors_id)
      else:
        client.remove_members_from_group(authors_accepted_id, paper_authors_id)