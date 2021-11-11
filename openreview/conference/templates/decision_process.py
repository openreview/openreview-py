def process_update(client, note, invitation, existing_note):

    CONFERENCE_ID = ''
    SHORT_PHRASE = ''
    AUTHORS_NAME = ''
    ACCEPTED_AUTHORS_NAME = 'Authors/Accepted'
    EMAIL_AUTHORS = False
    baseUrl='https://openreview.net'

    forum_note = client.get_note(note.forum)
   
    AUTHORS_ID = CONFERENCE_ID + '/Paper' + str(forum_note.number) + '/' + AUTHORS_NAME
    
    # Check if the content of the existing note is the same as the updated note
    if (existing_note):
      equal = True
      for key in existing_note.content:
        if existing_note.content[key] != note.content[key]:
          equal = False
      # If the content is not equal, want to send emails 
      if(not equal):
        if (EMAIL_AUTHORS and 'everyone' in note.readers) or (AUTHORS_ID in note.readers):
          groups = AUTHORS_ID
          subject = SHORT_PHRASE + 'Decision posted to your submission - Paper number: ' + str(forum_note.number) + ', Paper title: "' + forum_note.content['title'] + '"'
          message = 'To view the decision, click here: ' + baseUrl + '/forum?id=' + note.forum + '&noteId=' + note.id
          client.post_message(subject, groups, message)
    else:
      if (EMAIL_AUTHORS and 'everyone' in note.readers) or (AUTHORS_ID in note.readers):
        groups = AUTHORS_ID
        subject = SHORT_PHRASE + 'Decision posted to your submission - Paper number: ' + str(forum_note.number) + ', Paper title: "' + forum_note.content['title'] + '"'
        message = 'To view the decision, click here: ' + baseUrl + '/forum?id=' + note.forum + '&noteId=' + note.id
        client.post_message(subject, groups, message)

    if (ACCEPTED_AUTHORS_NAME):
      group = CONFERENCE_ID + '/' + ACCEPTED_AUTHORS_NAME
      
      if ('Accept' in note.content['decision']):
        client.add_members_to_group(group, AUTHORS_ID)
      elif ('Reject' in note.content['decision']):
        client.remove_member_from_group(group, AUTHORS_ID)
    
    return True


