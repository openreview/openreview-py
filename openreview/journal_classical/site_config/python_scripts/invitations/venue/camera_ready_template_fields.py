import datetime


def _content_value(note, field_name, default=None):
    return (getattr(note, 'content', {}) or {}).get(field_name, {}).get('value', default)


def _timestamp(note):
    return getattr(note, 'tcdate', None) or getattr(note, 'cdate', None)


def _month_year(timestamp_millis):
    value = datetime.datetime.fromtimestamp(
        timestamp_millis / 1000.0, datetime.timezone.utc
    )
    return f'{value.month}/{value.year % 100:02d}'


def get_camera_ready_template_fields(client, journal, submission, decision):
    chain = [submission]
    seen = {submission.id}
    current = submission
    previous_field = f'previous_{journal.short_name}_submission_url'

    while True:
        previous_url = _content_value(current, previous_field)
        if not previous_url or 'forum?id=' not in previous_url:
            break
        previous_id = previous_url.split('forum?id=', 1)[1].split('&', 1)[0]
        if not previous_id or previous_id in seen:
            break
        try:
            previous = client.get_note(previous_id)
        except Exception as error:
            print(f'Could not resolve previous submission for camera-ready dates: {error}')
            break
        chain.append(previous)
        seen.add(previous_id)
        current = previous

    accepted_timestamp = _timestamp(decision)
    original = chain[-1]
    revision = chain[-2] if len(chain) > 1 else None
    revised_timestamp = _timestamp(revision) if revision else accepted_timestamp
    accepted_date = datetime.datetime.fromtimestamp(
        accepted_timestamp / 1000.0, datetime.timezone.utc
    )
    submitted = _month_year(_timestamp(original))
    revised = _month_year(revised_timestamp)
    accepted = _month_year(accepted_timestamp)
    accepted_year = accepted_date.year
    accepted_year_short = f'{accepted_year % 100:02d}'
    submission_number_padded = f'{submission.number % 100000:05d}'
    publication_id = f'{accepted_year_short}-{submission_number_padded}'
    dates_block = (
        '\\jmlropenreviewdates{\n'
        f'  submitted = {{{submitted}}},\n'
        f'  revised = {{{revised}}},\n'
        f'  accepted = {{{accepted}}},\n'
        f'  paperid = {{{publication_id}}}\n'
        '}'
    )

    return {
        'camera_ready_submitted': submitted,
        'camera_ready_revised': revised,
        'camera_ready_accepted': accepted,
        'camera_ready_accepted_year_short': accepted_year_short,
        'camera_ready_submission_number_padded': submission_number_padded,
        'camera_ready_accepted_year': accepted_year,
        'camera_ready_volume': (accepted_year % 100) + 1,
        'camera_ready_publication_id': publication_id,
        'camera_ready_dates_block': dates_block,
    }
