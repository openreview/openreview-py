def process(client, edit, invitation):
    # JMLR delta: Journal has no immutable inherited submission track.
    note = edit.note
    requested = note.content.get('track_id', {}).get('value', 'Regular')

    previous_url = note.content.get('previous_JMLR_submission_url', {}).get('value')
    if previous_url:
        previous_id = previous_url.split('?id=')[-1].split('&')[0]
        previous = client.get_note(previous_id)
        inherited = previous.content.get('track_id', {}).get('value', 'Regular')
        if inherited != 'Regular':
            raise openreview.OpenReviewException('Direct JMLR resubmission is available only for Regular papers.')
        if requested != inherited:
            raise openreview.OpenReviewException(
                f'Resubmission track must match the previous paper: select {inherited}.'
            )
        decisions = client.get_notes(invitation=f'JMLR/Paper{previous.number}/-/Decision')
        permitted = decisions and decisions[0].content.get('recommendation', {}).get('value') == 'Reject' and bool(
            decisions[0].content.get('resubmission_of_major_revision', {}).get('value')
        )
        if not permitted:
            raise openreview.OpenReviewException('The previous JMLR decision does not permit resubmission.')
    else:
        # The display link is server-owned and absent on ordinary submissions.
        note.content.pop('previous_JMLR_submission', None)

    if note.id:
        current = client.get_note(note.id)
        existing = current.content.get('track_id', {}).get('value', 'Regular')
        if note.content.get('track_id', {}).get('value', existing) != existing:
            raise openreview.OpenReviewException('Track is immutable after submission.')
    elif not previous_url:
        import datetime
        import json
        aoe = datetime.timezone(datetime.timedelta(hours=-12))
        today = datetime.datetime.now(aoe).date()
        records = json.loads(client.get_group('JMLR/Tracks').content['tracks']['value'])
        active = {'Regular'}
        for record in records:
            beginning = datetime.date.fromisoformat(record['beginning_date']) if record.get('beginning_date') else None
            ending = datetime.date.fromisoformat(record['ending_date']) if record.get('ending_date') else None
            if (beginning is None or today >= beginning) and (ending is None or today <= ending):
                active.add(record['id'])
        if requested not in active:
            raise openreview.OpenReviewException(f'Track {requested} is not open for new submissions.')
