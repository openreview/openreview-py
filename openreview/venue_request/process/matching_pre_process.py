def process(client, note, invitation):

    if 'No' not in note.content['compute_affinity_scores'] and 'upload_affinity_scores' in note.content:
        raise openreview.OpenReviewException('Either upload your own affinity scores or select affinity scores computed by OpenReview')

    matching_group = note.content['matching_group']
    matching_notes = client.get_all_notes(invitation=invitation.id, sort='tmdate:desc')
    matching_group_notes = [matching_note for matching_note in matching_notes if matching_note.content['matching_group'] == matching_group]
    
    if matching_group_notes:
        status_note = client.get_all_notes(invitation=invitation.id.replace('Paper_Matching_Setup', 'Paper_Matching_Setup_Status'), replyto=matching_group_notes[0].id)
        if not status_note:
            raise openreview.OpenReviewException('Paper matching is already being run for this group. Please wait for a status reply in the forum.')
