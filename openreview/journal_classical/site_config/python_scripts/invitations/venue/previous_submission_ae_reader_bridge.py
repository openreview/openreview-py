"""Give the current paper-scoped AE group read access to prior-round records."""


def _content_value(note, key):
    value = (getattr(note, 'content', None) or {}).get(key)
    return value.get('value') if isinstance(value, dict) else value


def _previous_forum_id(value):
    from urllib.parse import parse_qsl, urlsplit

    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = urlsplit(value.strip())
    except ValueError:
        return None
    if (
        parsed.scheme != 'https'
        or parsed.netloc not in {'openreview.net', 'dev.openreview.net'}
        or parsed.path != '/forum'
    ):
        return None
    forum_ids = [
        item
        for key, item in parse_qsl(parsed.query, keep_blank_values=True)
        if key == 'id'
    ]
    if len(forum_ids) != 1 or not forum_ids[0] or forum_ids[0] != forum_ids[0].strip():
        return None
    return forum_ids[0]


def _is_jmlr_submission(note, journal):
    if not note or getattr(note, 'domain', None) != journal.venue_id:
        return False
    invitations = list(getattr(note, 'invitations', None) or [])
    invitation = getattr(note, 'invitation', None)
    if invitation:
        invitations.append(invitation)
    return journal.get_author_submission_id() in invitations


def _previous_submission_chain(client, journal, submission):
    """Yield the validated linked chain once, stopping on malformed data or cycles."""
    seen = {getattr(submission, 'id', None)}
    current = submission
    while True:
        previous_id = _previous_forum_id(
            _content_value(current, 'previous_JMLR_submission_url')
        )
        if not previous_id or previous_id in seen:
            return
        seen.add(previous_id)
        try:
            previous = client.get_note(previous_id)
        except Exception:
            return
        if getattr(previous, 'id', None) != previous_id or not _is_jmlr_submission(previous, journal):
            return
        yield previous
        current = previous


def _add_group_reader(client, journal, note, group_id):
    readers = list(getattr(note, 'readers', None) or [])
    if 'everyone' in readers or group_id in readers:
        return
    readers.append(group_id)
    client.post_note_edit(
        invitation=journal.get_meta_invitation_id(),
        signatures=[journal.venue_id],
        note=openreview.api.Note(id=note.id, readers=readers),
    )


def ensure_previous_submission_access_for_current_ae(client, journal, submission):
    """Bridge prior forums without changing historical membership or content."""
    current_ae_group = journal.get_action_editors_id(number=submission.number)
    for previous in _previous_submission_chain(client, journal, submission):
        _add_group_reader(client, journal, previous, current_ae_group)
        decisions = client.get_notes(
            forum=previous.id,
            invitation=journal.get_ae_decision_id(number=previous.number),
        )
        for decision in decisions:
            _add_group_reader(client, journal, decision, current_ae_group)
        reviews = client.get_notes(
            forum=previous.id,
            invitation=journal.get_review_id(number=previous.number),
        )
        for review in reviews:
            _add_group_reader(client, journal, review, current_ae_group)
