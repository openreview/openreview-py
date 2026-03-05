def process(client, edit, invitation):

    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    authors_name = domain.get_content_value('authors_name')
    readers = edit.content['readers']['value']

    is_submission_change_invitation = 'Submission_Change_Before' in invitation.id.split('/Readers')[0]

    if 'everyone' in readers and len(readers) > 1:
        raise openreview.OpenReviewException('The "everyone" reader option cannot be included with other reader options.')
    
    if 'everyone' not in readers:
        if venue_id not in readers and not any(r for r in readers if r.endswith('/Program_Chairs')):
            raise openreview.OpenReviewException(f'If "everyone" is not selected as reader, the Program Chairs must be included as readers.')
        if is_submission_change_invitation and not any(r for r in readers if r.endswith(f'/{authors_name}')):
            raise openreview.OpenReviewException(f'If "everyone" is not selected as reader, the submission authors group must be included as readers.')