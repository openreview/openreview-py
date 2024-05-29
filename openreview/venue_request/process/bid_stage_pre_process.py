def process(client, note, invitation):

    request_form = client.get_note(note.forum)

    previous_references = client.get_references(referent=note.forum, invitation=note.invitation)
    if len(previous_references) > 0:
        if not client.get_process_logs(id=previous_references[0].id):
            raise openreview.OpenReviewException('There is currently a stage process running, please wait until it finishes to try again.')    

    if ('Assigned program committee' in request_form.content.get('submission_readers', '') or 'Program chairs and paper authors only' in request_form.content.get('submission_readers', '')):
        raise openreview.OpenReviewException('Papers should be visible to all program committee if bidding is enabled')
    
    if 'pdf' not in request_form.content.get('hide_fields', []):
        raise openreview.OpenReviewException('The pdf field should be hidden during the bidding stage. Please use the Post Submission button to hide pdfs.')