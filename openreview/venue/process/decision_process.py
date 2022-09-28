def process(client, edit, invitation):
    SHORT_PHRASE = ''
    PAPER_AUTHORS_ID = ''
    AUTHORS_ID_ACCEPTED = ''
    EMAIL_AUTHORS = False

    submission = client.get_note(edit.note.forum)
    decision = client.get_note(edit.note.id)

    PAPER_AUTHORS_ID = PAPER_AUTHORS_ID.replace('{number}', str(submission.number))

    action = 'posted to' if decision.tcdate == decision.tmdate else 'edited on'

    if (EMAIL_AUTHORS and ('everyone' in decision.readers or PAPER_AUTHORS_ID in decision.readers)):

        client.post_message(
            recipients=[PAPER_AUTHORS_ID],
            subject=f'''[{SHORT_PHRASE}] Decision {action} your submission - Paper Number: {submission.number}, Paper Title: "{submission.content['title']['value']}"''',
            message=f'''To view the decision, click here: https://openreview.net/forum?id={submission.id}&noteId={decision.id}'''
        )

    if (AUTHORS_ID_ACCEPTED):      
      if ('Accept' in decision.content['decision']['value']):
        client.add_members_to_group(AUTHORS_ID_ACCEPTED, PAPER_AUTHORS_ID)
      elif ('Reject' in decision.content['decision']['value']):
        client.remove_members_from_group(AUTHORS_ID_ACCEPTED, PAPER_AUTHORS_ID)