def validate_final_author_list(client, edit):
    import re

    def is_openreview_profile_id(value):
        return bool(re.match(r'^~[A-Za-z0-9_]+[0-9]*$', str(value or '').strip()))

    def split_final_author_list(value):
        raw = str(value or '')
        if '\n' in raw or '\r' in raw:
            raise openreview.OpenReviewException({
                'name': 'ValidationError',
                'message': 'Final Publication Author List must use comma-separated OpenReview profile IDs only. Line breaks are not allowed.',
                'status': 400,
                'details': {'path': 'note/content/final_publication_author_list/value'}
            })
        return [part.strip() for part in raw.split(',') if part.strip()]

    def content_value(content, field_name, default=None):
        field = (content or {}).get(field_name, default)
        if isinstance(field, dict) and 'value' in field:
            return field.get('value')
        return field

    def normalized_submitted_authorids(submission):
        authorids = [
            str(authorid or '').strip()
            for authorid in (content_value(submission.content, 'authorids', []) or [])
            if str(authorid or '').strip()
        ]
        if authorids:
            return authorids
        return [
            str(author or '').strip()
            for author in (content_value(submission.content, 'authors', []) or [])
            if is_openreview_profile_id(author)
        ]

    submission = client.get_note(edit.note.id)
    submitted_authorids = normalized_submitted_authorids(submission)
    final_authors = split_final_author_list(edit.note.content.get('final_publication_author_list', {}).get('value'))
    if not final_authors:
        raise openreview.OpenReviewException({
            'name': 'ValidationError',
            'message': 'Final Publication Author List is required. Enter OpenReview profile IDs separated by commas. Line breaks are not allowed.',
            'status': 400,
            'details': {'path': 'note/content/final_publication_author_list/value'}
        })
    invalid_final_authors = [author for author in final_authors if not is_openreview_profile_id(author)]
    if invalid_final_authors:
        raise openreview.OpenReviewException({
            'name': 'ValidationError',
            'message': 'Final Publication Author List must contain valid OpenReview profile IDs only, for example ~First_Author1. Invalid entries: ' + ', '.join(invalid_final_authors) + '.',
            'status': 400,
            'details': {'path': 'note/content/final_publication_author_list/value'}
        })
    normalized_final_authors = []
    for index, author in enumerate(final_authors, start=1):
        try:
            profile = client.get_profile(author)
        except Exception:
            raise openreview.OpenReviewException({
                'name': 'ValidationError',
                'message': f'Final Publication Author List entry {index} has an OpenReview profile ID that could not be resolved: {author}.',
                'status': 400,
                'details': {'path': 'note/content/final_publication_author_list/value'}
            })
        if not profile:
            raise openreview.OpenReviewException({
                'name': 'ValidationError',
                'message': f'Final Publication Author List entry {index} has an OpenReview profile ID that could not be resolved: {author}.',
                'status': 400,
                'details': {'path': 'note/content/final_publication_author_list/value'}
            })
        normalized_final_authors.append(getattr(profile, 'id', None) or author)
    final_authors = normalized_final_authors
    edit.note.content['final_publication_author_list'] = {'value': ', '.join(final_authors)}

    submitted_sorted = sorted(submitted_authorids)
    final_sorted = sorted(final_authors)

    submitted_author_set = set(submitted_authorids)
    final_author_set = set(final_authors)
    unknown_final_authors = [author for author in final_authors if author not in submitted_author_set]
    duplicate_final_authors = sorted({author for author in final_authors if final_authors.count(author) > 1})
    missing_submitted_authors = [
        str(authorid)
        for authorid in submitted_authorids
        if authorid not in final_author_set
    ]
    if final_sorted != submitted_sorted:
        message = 'The Final Publication Author List may reorder submitted authors, but it must contain exactly the submitted OpenReview profile IDs separated by commas.'
        if unknown_final_authors:
            message += ' Not in submitted author list: ' + ', '.join(unknown_final_authors) + '.'
        if duplicate_final_authors:
            message += ' Duplicate author IDs: ' + ', '.join(duplicate_final_authors) + '.'
        if missing_submitted_authors:
            message += ' Missing submitted authors: ' + ', '.join(missing_submitted_authors) + '.'
        raise openreview.OpenReviewException({
            'name': 'ValidationError',
            'message': message,
            'status': 400,
            'details': {'path': 'note/content/final_publication_author_list/value'}
        })
