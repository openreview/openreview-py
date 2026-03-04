def process(client, edit, invitation):

    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    authors_name = domain.get_content_value('authors_name')
    readers = edit.content['readers']['value']

    if 'everyone' in readers and len(readers) > 1:
        raise openreview.OpenReviewException('The "everyone" reader option cannot be included with other reader options.')
    
    if 'everyone' not in readers:
        if venue_id not in readers:
            raise openreview.OpenReviewException(f'If "everyone" is not selected as reader, the Program Chairs must be included as readers.')
        if not any(r for r in readers if r.endswith(f'/{authors_name}')):
            raise openreview.OpenReviewException(f'If "everyone" is not selected as reader, the submission authors group must be included as readers.')