def process(client, note, invitation):

    request_form = client.get_note(note.forum)

    if ('Assigned program committee' in request_form.content.get('submission_readers', '') or 'Program chairs and paper authors only' in request_form.content.get('submission_readers', '')):
        raise openreview.OpenReviewException('Papers should be visible to all program committee if bidding is enabled')
    
    if 'pdf' not in request_form.content.get('hide_fields', []):
        raise openreview.OpenReviewException('The pdf field should be hidden during the bidding stage')