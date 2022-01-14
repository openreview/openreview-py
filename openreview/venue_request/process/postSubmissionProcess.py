def process(client, note, invitation):
    GROUP_PREFIX = ''
    SUPPORT_GROUP = GROUP_PREFIX + '/Support'
    conference = openreview.helpers.get_conference(client, note.forum)
    forum_note = client.get_note(note.forum)

    comment_readers = forum_note.content.get('Contact Emails', []) + forum_note.content.get('program_chair_emails', []) + [SUPPORT_GROUP]
    import traceback
    try:
        conference.setup_post_submission_stage(force=note.content['force'] == 'Yes', hide_fields=note.content.get('hide_fields', []))
        print('Conference: ', conference.get_id())
    except Exception as e:
        error_status = f'''
        Post Submission Process failed due to the following error: \n 
        {repr(e)} \n 
        {traceback.format_exc()}
        '''
        comment_note = openreview.Note(
            invitation=SUPPORT_GROUP + '/-/Request' + str(forum_note.number) + '/Comment',
            forum=forum_note.id,
            replyto=forum_note.id,
            readers=comment_readers,
            writers=[SUPPORT_GROUP],
            signatures=[SUPPORT_GROUP],
            content={
                'title': 'Post Submission Status',
                'comment': error_status
            }
        )

        client.post_note(comment_note)
