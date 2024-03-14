def process(client, note, invitation):

    if 'No' not in note.content['compute_affinity_scores'] and 'upload_affinity_scores' in note.content:
        raise openreview.OpenReviewException('Either upload your own affinity scores or select affinity scores computed by OpenReview')

    matching_group = note.content['matching_group']
    matching_notes = client.get_all_notes(invitation=invitation.id, sort='tmdate:desc')

    if matching_notes:
        latest_matching_note = None
        for i, matching_note in enumerate(matching_notes):
            if matching_note.content['matching_group'] == matching_group:
                latest_matching_note = matching_notes[i]
                break

        if latest_matching_note:
            status_inv = invitation.id.replace('Paper_Matching_Setup', 'Paper_Matching_Setup_Status')
            status_note = client.get_all_notes(invitation=status_inv, replyto=latest_matching_note.id)

            if not status_note:
                raise openreview.OpenReviewException('Paper matching is already being run for this group. Please wait for a status reply in the forum.')
