def process(client, edit, invitation):

    if not edit.note.content.get('pdf', {}).get('value') and not edit.note.content.get('html', {}).get('value'):
        raise openreview.OpenReviewException(f'You must upload a PDF or a Beyond PDF file for the submission.')
    
    if edit.note.content.get('pdf', {}).get('value') and edit.note.content.get('html', {}).get('value'):
        raise openreview.OpenReviewException(f'You must upload either a PDF or a Beyond PDF file for the submission, not both.')
    
    if 'Beyond PDF submission' in edit.note.content.get('submission_length', {}).get('value') and not edit.note.content.get('html', {}).get('value'):
        raise openreview.OpenReviewException(f'You must upload a Beyond PDF zip file for the submission if you select "Beyond PDF submission" as the submission type.')
    
    if 'Regular submission' in edit.note.content.get('submission_length', {}).get('value') and not edit.note.content.get('pdf', {}).get('value'):
        raise openreview.OpenReviewException(f'You must upload a PDF file for the submission if you select "Regular submission" as the submission type.')
    
    if 'Long submission' in edit.note.content.get('submission_length', {}).get('value') and not edit.note.content.get('pdf', {}).get('value'):
        raise openreview.OpenReviewException(f'You must upload a PDF file for the submission if you select "Long submission" as the submission type.')