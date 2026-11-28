"""Resolve Journal prior-round reviewer continuity for checked server policy."""


def content_value(note, key, default=None):
    value = (getattr(note, 'content', None) or {}).get(key, default)
    if isinstance(value, dict) and 'value' in value:
        return value['value']
    return value


def parse_openreview_forum_id(value):
    """Return one structurally valid production/DEV OpenReview forum id."""
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
    ids = [
        item
        for key, item in parse_qsl(parsed.query, keep_blank_values=True)
        if key == 'id'
    ]
    if len(ids) != 1 or not ids[0] or ids[0] != ids[0].strip():
        return None
    return ids[0]


def is_jmlr_submission(note, journal):
    if not note or getattr(note, 'domain', None) != journal.venue_id:
        return False
    invitations = list(getattr(note, 'invitations', None) or [])
    invitation = getattr(note, 'invitation', None)
    if invitation:
        invitations.append(invitation)
    return journal.get_author_submission_id() in invitations


def resolve_previous_submission(client, journal, submission):
    previous_id = parse_openreview_forum_id(
        content_value(submission, 'previous_JMLR_submission_url')
    )
    if not previous_id:
        return None
    try:
        previous = client.get_note(previous_id)
    except Exception:
        return None
    return (
        previous
        if getattr(previous, 'id', None) == previous_id
        and is_jmlr_submission(previous, journal)
        else None
    )


def is_openreview_profile_id(value):
    """Accept OpenReview's leading-tilde and trailing-number profile boundary."""
    import re

    return bool(
        isinstance(value, str)
        and not re.search(r'[\s/]', value)
        and re.fullmatch(r'~.*\d+', value)
    )


def prior_reviewer_ids(client, journal, previous_submission):
    """Return a complete deterministic set from active and archived assignments."""
    reviewer_ids = set()
    try:
        for archived in (False, True):
            invitation_id = journal.get_reviewer_assignment_id(archived=archived)
            edges = client.get_edges(
                invitation=invitation_id, head=previous_submission.id
            )
            for edge in edges:
                tail = getattr(edge, 'tail', None)
                if not getattr(edge, 'ddate', None) and is_openreview_profile_id(tail):
                    reviewer_ids.add(tail)
    except Exception:
        return []
    return sorted(reviewer_ids)


def active_prior_reviewer_assignment(client, journal, submission, reviewer_id):
    """Preserve the independent Journal continuity load exception."""
    previous = resolve_previous_submission(client, journal, submission)
    return bool(
        previous
        and reviewer_id in prior_reviewer_ids(client, journal, previous)
    )
