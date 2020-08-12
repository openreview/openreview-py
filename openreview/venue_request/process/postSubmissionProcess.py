def process(client, note, invitation):

    conference = openreview.helpers.get_conference(client, note.forum)
    conference.setup_post_submission_stage(force=note.content['force'] == 'Yes', hide_fields=note.content.get('hide_fields', []))

    print('Conference: ', conference.get_id())