def process(client, note, invitation):

    request_form = client.get_note(note.forum)

    previous_references = client.get_references(referent=note.forum, invitation=note.invitation)
    if len(previous_references) > 0:
        if not client.get_process_logs(id=previous_references[0].id):
            raise openreview.OpenReviewException('There is currently a stage process running, please wait until it finishes to try again.')    

    if request_form.content.get('api_version', '1') == '1' and 'Double-blind' not in request_form.content['Author and Reviewer Anonymity']:
        if 'No' in note.content.get('withdrawn_submissions_author_anonymity', ''):
            raise openreview.OpenReviewException('Author identities of withdrawn submissions can only be anonymized for double-blind submissions')

        if 'No' in note.content.get('desk_rejected_submissions_author_anonymity', ''):
            raise openreview.OpenReviewException('Author identities of desk-rejected submissions can only be anonymized for double-blind submissions')