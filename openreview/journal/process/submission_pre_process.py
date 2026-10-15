def process(client, edit, invitation):

    journal = openreview.journal.Journal()
    content = edit.note.content or {}

    submission_length = content.get('submission_length', {}).get('value', [])
    beyond_pdf = content.get('beyond_pdf', {}).get('value')

    if 'Beyond PDF submission' in submission_length and not beyond_pdf:
        raise openreview.OpenReviewException(f'You must upload a Beyond PDF zip file for the submission if you select "Beyond PDF submission" as the submission type.')

    if beyond_pdf and 'Beyond PDF submission' not in submission_length:
        raise openreview.OpenReviewException(f'You must select "Beyond PDF submission" as the submission type if your submission contains a Beyond PDF zip file.')

    if not content.get(f'previous_{journal.short_name}_submission_url', {}).get('value'):
        return

    ## use the same error for all the cases so the link can not be used to find out which notes exist
    invalid_link_error = openreview.OpenReviewException(f'The previous {journal.short_name} submission URL must link to a {journal.short_name} submission that shares at least one author with this submission.')

    previous_submission_id = journal.get_previous_submission_id(edit.note)
    if not previous_submission_id or previous_submission_id == edit.note.id:
        raise invalid_link_error

    try:
        previous_submission = openreview.tools.get_note(client, previous_submission_id)
    except openreview.OpenReviewException:
        ## the note belongs to another venue
        previous_submission = None

    if not previous_submission or previous_submission.domain != journal.venue_id or previous_submission.forum != previous_submission.id:
        raise invalid_link_error

    ## revisions don't include the authors, take them from the submission
    authorids = content.get('authorids', {}).get('value') or client.get_note(edit.note.id).content['authorids']['value']
    if not set(authorids).intersection(previous_submission.content.get('authorids', {}).get('value', [])):
        raise invalid_link_error
