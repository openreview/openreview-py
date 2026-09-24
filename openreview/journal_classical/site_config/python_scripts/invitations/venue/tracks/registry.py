# JMLR delta: Journal has no ordered, date-bounded managed-track registry.
import datetime
import json
import re

TRACKS_GROUP_ID = 'JMLR/Tracks'
REGULAR_TRACK_ID = 'Regular'
AOE = datetime.timezone(datetime.timedelta(hours=-12))
IDLE_DATEPROCESS_MILLIS = 9999999999998
TRACK_ID_RE = re.compile(r'^[A-Za-z][A-Za-z0-9_]{0,63}$')


def track_records_from_value(value):
    records = json.loads(value or '[]')
    if not isinstance(records, list):
        raise openreview.OpenReviewException('Track registry must be an ordered list.')
    return records


def track_records_from_group(group):
    value = (group.content or {}).get('tracks', {}).get('value', '[]')
    return track_records_from_value(value)


def aoe_boundary_millis(date_value, end=False):
    if not date_value:
        return None
    day = datetime.date.fromisoformat(date_value)
    if end:
        day += datetime.timedelta(days=1)
    boundary = datetime.datetime.combine(day, datetime.time.min, tzinfo=AOE)
    return int(boundary.timestamp() * 1000)


def validate_track_records(records, previous=None):
    seen = set()
    normalized = []
    for record in records:
        if not isinstance(record, dict):
            raise openreview.OpenReviewException('Every track must be an object.')
        track_id = str(record.get('id') or '').strip()
        name = str(record.get('name') or '').strip()
        beginning = record.get('beginning_date') or None
        ending = record.get('ending_date') or None
        if track_id == REGULAR_TRACK_ID:
            raise openreview.OpenReviewException('Regular is permanent and is not a managed track.')
        if not TRACK_ID_RE.fullmatch(track_id):
            raise openreview.OpenReviewException(f'Invalid track identifier: {track_id}.')
        if track_id in seen:
            raise openreview.OpenReviewException(f'Duplicate track identifier: {track_id}.')
        if not name:
            raise openreview.OpenReviewException(f'Track {track_id} requires a display name.')
        try:
            start = aoe_boundary_millis(beginning)
            finish = aoe_boundary_millis(ending, end=True)
        except ValueError:
            raise openreview.OpenReviewException(f'Track {track_id} dates must use YYYY-MM-DD.')
        if start is not None and finish is not None and start >= finish:
            raise openreview.OpenReviewException(f'Track {track_id} ending date must not precede its beginning date.')
        seen.add(track_id)
        normalized.append({
            'id': track_id,
            'name': name,
            'beginning_date': beginning,
            'ending_date': ending,
        })
    previous_ids = {record['id'] for record in (previous or [])}
    if not previous_ids.issubset(seen):
        missing = ', '.join(sorted(previous_ids - seen))
        raise openreview.OpenReviewException(f'Tracks cannot be deleted; set an ending date instead: {missing}.')
    return normalized


def track_is_open(record, now_millis=None):
    now_millis = now_millis or int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000)
    beginning = aoe_boundary_millis(record.get('beginning_date'))
    ending = aoe_boundary_millis(record.get('ending_date'), end=True)
    return (beginning is None or now_millis >= beginning) and (ending is None or now_millis < ending)


def open_track_ids(records, now_millis=None):
    return [REGULAR_TRACK_ID] + [record['id'] for record in records if track_is_open(record, now_millis)]


def future_boundaries(records, now_millis=None):
    now_millis = now_millis or int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000)
    boundaries = set()
    for record in records:
        for value in (
            aoe_boundary_millis(record.get('beginning_date')),
            aoe_boundary_millis(record.get('ending_date'), end=True),
        ):
            if value is not None and value > now_millis:
                boundaries.add(value)
    return sorted(boundaries)


def load_track_records(client):
    return validate_track_records(track_records_from_group(client.get_group(TRACKS_GROUP_ID)))


def refresh_track_surfaces(client, journal, records):
    """Refresh the exact submission schema and the next AoE boundary timer."""
    submission = client.get_invitation(journal.get_author_submission_id())
    submission.edit['note']['content']['track_id']['value']['param']['enum'] = open_track_ids(records)
    client.post_invitation_edit(
        invitations=journal.get_meta_invitation_id(),
        signatures=[journal.venue_id],
        invitation=submission,
        replacement=True,
    )

    manager = client.get_invitation(f'{journal.venue_id}/-/Manage_Tracks')
    manager.date_processes = [{
        'dates': future_boundaries(records) or [IDLE_DATEPROCESS_MILLIS],
        'script': manager.date_processes[0]['script'],
    }]
    client.post_invitation_edit(
        invitations=journal.get_meta_invitation_id(),
        signatures=[journal.venue_id],
        invitation=manager,
        replacement=True,
    )
