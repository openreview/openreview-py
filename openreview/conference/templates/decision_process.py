def process_update(client, note, invitation, existing_note):

    CONFERENCE_ID = ''
    SHORT_PHRASE = ''
    AUTHORS_NAME = ''
    AUTHORS_NAME_ACCEPTED = ''
    EMAIL_AUTHORS = False
    baseUrl='https://openreview.net'

    forum_note = client.get_note(note.forum)
   
    AUTHORS_ID = CONFERENCE_ID + '/Paper' + str(forum_note.number) + '/' + AUTHORS_NAME
    
    # Check if the content of the existing note is the same as the updated note
    if existing_note:
      if (EMAIL_AUTHORS and ('everyone' in note.readers or AUTHORS_ID in note.readers)):
        equal = True
        for key in existing_note.content:
          if note.content.get(key) and (existing_note.content[key] != note.content.get(key)):
            equal = False
      # If the content is not equal, want to send emails 
        if(not equal):
          groups = [AUTHORS_ID]
          subject = '[{SHORT_PHRASE}] Decision updated for your submission - Paper number: {paper_number}, Paper title: "{paper_title}"'.format(
            SHORT_PHRASE = SHORT_PHRASE,
            paper_number = str(forum_note.number),
            paper_title = forum_note.content['title']
          )
          message = 'To view the decision, click here: {baseUrl}/forum?id={forum}&noteId={id}'.format(
            baseUrl = baseUrl,
            forum = note.forum,
            id=note.id
          )
          client.post_message(subject, groups, message)
         
    else:
      if (EMAIL_AUTHORS and ('everyone' in note.readers or AUTHORS_ID in note.readers)):

        groups = [AUTHORS_ID]
        subject = '[{SHORT_PHRASE}] Decision posted to your submission - Paper number: {paper_number}, Paper title: "{paper_title}"'.format(
            SHORT_PHRASE = SHORT_PHRASE,
            paper_number = str(forum_note.number),
            paper_title = forum_note.content['title']
          )
        message = 'To view the decision, click here: {baseUrl}/forum?id={forum}&noteId={id}'.format(
          baseUrl = baseUrl,
          forum = note.forum,
          id=note.id
        )
        client.post_message(subject, groups, message)

    
    
    if (AUTHORS_NAME_ACCEPTED):
      group = CONFERENCE_ID + '/' + AUTHORS_NAME_ACCEPTED
      
      if ('Accept' in note.content['decision']):
        client.add_members_to_group(group, AUTHORS_ID)
      elif ('Reject' in note.content['decision']):
        client.remove_members_from_group(group, AUTHORS_ID)

    
    
    return True


