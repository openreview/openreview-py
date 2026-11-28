def process(client, edit, invitation):
    # Private tracking of manual jmlr.org publication, not an OpenReview lifecycle transition.
    from urllib.parse import urlparse

    journal = openreview.journal.JournalRequest.get_journal(client, "{{PROD_JOURNAL_ID}}")
    note = edit.note
    submission = client.get_note(note.forum)
    venue_id = (submission.content or {}).get('venueid', {}).get('value')
    if venue_id != journal.accepted_venue_id:
        raise openreview.OpenReviewException('Publication work may only be recorded for an accepted final record.')
    if note.replyto != submission.id:
        raise openreview.OpenReviewException('Publication status must reply directly to the accepted record.')

    status = note.content['status']['value']
    if status not in {'Ready', 'Published'}:
        raise openreview.OpenReviewException('Invalid publication worklist status.')

    existing = client.get_notes(invitation=invitation.id, forum=submission.id)
    if len(existing) > 1:
        raise openreview.OpenReviewException('More than one publication status exists for this paper.')
    if existing and note.id != existing[0].id:
        raise openreview.OpenReviewException('Update the existing publication status for this paper.')
    publication_url = (note.content or {}).get('jmlr_publication_url', {}).get('value', '').strip()
    if not publication_url:
        if status == 'Published':
            raise openreview.OpenReviewException('The JMLR publication URL is required before marking publication complete.')
        return
    parsed = urlparse(publication_url)
    path_parts = parsed.path.split('/')
    if (parsed.scheme != 'https' or parsed.hostname not in {'jmlr.org', 'www.jmlr.org'}
            or not parsed.path.startswith('/papers/v') or len(path_parts) != 4
            or not path_parts[2][1:].isdigit() or not path_parts[3].lower().endswith('.html')):
        raise openreview.OpenReviewException(
            'The JMLR publication URL must use https://www.jmlr.org/papers/v<volume>/<paper>.html.'
        )
