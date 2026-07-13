def get_content_value(note, field_name):
    return note.content.get(field_name, {}).get('value')


def format_openreview_month_year(timestamp_millis):
    date = datetime.datetime.fromtimestamp(timestamp_millis / 1000.0, datetime.timezone.utc)
    return f'{date.month}/{date.year % 100:02d}'


def get_previous_submission_from_url(client, previous_url):
    if not previous_url or previous_url == 'N/A' or 'forum?id=' not in previous_url:
        return None
    note_id = previous_url.split('forum?id=', 1)[1].split('&', 1)[0]
    if not note_id:
        return None
    return client.get_note(note_id)


def get_submission_chain(client, submission):
    chain = [submission]
    seen_note_ids = {submission.id}
    current = submission
    while True:
        previous_url = get_content_value(current, 'previous_JMLR_submission_URL')
        try:
            previous = get_previous_submission_from_url(client, previous_url)
        except Exception as error:
            print(f'Could not resolve previous submission for camera-ready dates: {error}')
            return chain
        if not previous or previous.id in seen_note_ids:
            return chain
        chain.append(previous)
        seen_note_ids.add(previous.id)
        current = previous


def build_jmlr_publication_id(year, paper_number):
    return f'{year % 100:02d}-{paper_number % 100000:05d}'


def build_openreview_date_metadata(client, submission, decision):
    chain = get_submission_chain(client, submission)
    original_submission = chain[-1]
    first_revision = chain[-2] if len(chain) > 1 else None
    accepted_timestamp = decision.tcdate or decision.cdate
    submitted = format_openreview_month_year(original_submission.tcdate or original_submission.cdate)
    revised = format_openreview_month_year((first_revision.tcdate or first_revision.cdate) if first_revision else accepted_timestamp)
    accepted = format_openreview_month_year(accepted_timestamp)
    year = datetime.datetime.fromtimestamp(accepted_timestamp / 1000.0, datetime.timezone.utc).year
    return {
        'submitted': submitted,
        'revised': revised,
        'accepted': accepted,
        'accepted_timestamp': accepted_timestamp,
        'year': year,
        'volume': (year % 100) + 1,
        'paper_id': build_jmlr_publication_id(year, submission.number)
    }


def build_openreview_dates_block(client, submission, decision):
    metadata = build_openreview_date_metadata(client, submission, decision)
    return (
        '\\jmlropenreviewdates{\n'
        f'  submitted = {{{metadata["submitted"]}}},\n'
        f'  revised = {{{metadata["revised"]}}},\n'
        f'  accepted = {{{metadata["accepted"]}}},\n'
        f'  paperid = {{{metadata["paper_id"]}}}\n'
        '}'
    )


def split_final_author_list(value):
    return [part.strip() for part in str(value or '').split(',') if part.strip()]


def build_publication_metadata(client, submission, decision):
    date_metadata = build_openreview_date_metadata(client, submission, decision)
    final_authors = split_final_author_list(get_content_value(submission, 'final_publication_author_list'))
    authorids = get_content_value(submission, 'authorids') or []
    return {
        'id': date_metadata['paper_id'],
        'issue': submission.number,
        'volume': date_metadata['volume'],
        'title': get_content_value(submission, 'title') or '',
        'abstract': get_content_value(submission, 'abstract') or '',
        'authors': final_authors,
        'emails': ['' for _ in final_authors] if final_authors else ['' for _ in authorids],
        'pages': [1, None],
        'year': date_metadata['year'],
        'submitted': date_metadata['submitted'],
        'revised': date_metadata['revised'],
        'accepted': date_metadata['accepted']
    }
