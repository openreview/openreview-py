def process(client, note, invitation):
    GROUP_PREFIX = ''
    SUPPORT_GROUP = GROUP_PREFIX + '/Support'
    conference = openreview.helpers.get_conference(client, note.forum, SUPPORT_GROUP, setup=True)
    forum_note = client.get_note(note.forum)
    invitation_type = invitation.id.split('/')[-1]

    comment_readers = [conference.get_program_chairs_id(), SUPPORT_GROUP]
    import traceback
    try:
        conference.setup_post_submission_stage(force=note.content['force'] == 'Yes', hide_fields=note.content.get('hide_fields', []))

        if isinstance(conference, openreview.venue.Venue) or isinstance(conference, openreview.arr.ARR):
            conference.create_post_submission_stage()
            
        print('Conference: ', conference.get_id())

        comment_note = openreview.Note(
            invitation=SUPPORT_GROUP + '/-/Request' + str(forum_note.number) + '/Comment',
            forum=forum_note.id,
            replyto=forum_note.id,
            readers=comment_readers,
            writers=[SUPPORT_GROUP],
            signatures=[SUPPORT_GROUP],
            content={'title': f'{invitation_type.replace("_", " ")} Process Completed',
                    'comment': f'''
The {invitation_type.replace("_", " ")} process has been completed.

More details: https://api.openreview.net/references?id={note.id}'''
                        }
                    )

        client.post_note(comment_note)    
    except Exception as e:
        error_status = f'''
Post Submission Process failed due to the following error
{repr(e)}

To check references for the note: https://api.openreview.net/references?id={note.id}
        '''
        print("Following error in the process function was posted as a comment:")
        print(traceback.format_exc())

        comment_note = openreview.Note(
            invitation=SUPPORT_GROUP + '/-/Request' + str(forum_note.number) + '/Comment',
            forum=forum_note.id,
            replyto=forum_note.id,
            readers=comment_readers,
            writers=[SUPPORT_GROUP],
            signatures=[SUPPORT_GROUP],
            content={
                'title': 'Post Submission Status [{note_id}]'.format(note_id=note.id),
                'comment': error_status
            }
        )

        client.post_note(comment_note)
