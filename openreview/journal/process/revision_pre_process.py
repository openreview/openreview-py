def process(client, edit, invitation):

    submission = client.get_note(edit.note.id)

    if submission.content.get('pdf', {}).get('value') and edit.note.content.get('beyond_pdf', {}).get('value'):
        raise openreview.OpenReviewException(f'The original submission has a PDF, you must upload a PDF.')
    
    if submission.content.get('beyond_pdf', {}).get('value') and edit.note.content.get('pdf', {}).get('value'):
        raise openreview.OpenReviewException(f'The original submission has a Beyond PDF file, you must upload a Beyond PDF file.')
    
    if submission.content.get('pdf', {}).get('value') and edit.note.content.get('submission_length', {}).get('value') == 'Beyond PDF submission':
        raise openreview.OpenReviewException(f'You must select "Beyond PDF submission" as the submission type if your submission contains a Beyond PDF file.')
    
    if submission.content.get('beyond_pdf', {}).get('value') and edit.note.content.get('submission_length', {}).get('value', '') in ['Regular submission', 'Long submission']:
        raise openreview.OpenReviewException(f'You must select "Regular submission" or "Long submission" as the submission type if your submission contains a PDF file.')