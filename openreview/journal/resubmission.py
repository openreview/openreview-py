"""Shared resubmission lookup, assignment continuity, and prior-round access."""

import re
from urllib.parse import parse_qs, urlparse

from .. import openreview


INVALID_PREDECESSOR = (
    'The previous submission reference is invalid or inaccessible.')
RESUBMISSION_PERMISSIONS = {
    'The authors may consider submitting a major revision at a later time.',
    'Reject with encouragement to resubmit',
}


def validate_resubmission_settings(journal):
    enabled = journal.settings.get('resubmission_continuity_enabled', False)
    mode = journal.settings.get('resubmission_continuity', 'score')
    if type(enabled) is not bool:
        raise ValueError('resubmission_continuity_enabled must be boolean')
    if enabled and mode not in ('score', 'immediate_previous_ae'):
        raise ValueError('resubmission_continuity has an unsupported mode')


def content_value(note, key, default=None):
    value = (getattr(note, 'content', None) or {}).get(key, default)
    return value.get('value', default) if isinstance(value, dict) else value


def profile_ids(client, values):
    return {profile.id for value in values if isinstance(value, str) and value
            and (profile := openreview.tools.get_profile(client, value))}


def parse_forum_id(value):
    if not isinstance(value, str):
        return None
    try:
        parsed = urlparse(value)
        ids = parse_qs(parsed.query, keep_blank_values=True).get('id', [])
    except ValueError:
        return None
    return ids[0] if (parsed.scheme == 'https' and parsed.netloc in
        ('openreview.net', 'dev.openreview.net') and parsed.path == '/forum' and
        not parsed.params and not parsed.fragment and len(ids) == 1 and
        re.fullmatch(r'[^/?#&\s=]+', ids[0])) else None


def resolve_resubmission_predecessor(client, journal, submission):
    """Resolve an admitted immutable relationship for later continuity use."""
    note_id = parse_forum_id(content_value(submission, f'previous_{journal.short_name}_submission_url'))
    return _resolve_resubmission_predecessor(client, journal, note_id) if note_id else None


def _resolve_resubmission_predecessor(client, journal, note_id):
    try:
        previous = client.get_note(note_id)
    except openreview.OpenReviewException as error:
        details = error.args[0] if error.args and isinstance(error.args[0], dict) else {}
        if details.get('name') == 'NotFoundError' or details.get('status') == 404:
            return None
        raise
    invitations = {*list(getattr(previous, 'invitations', None) or []), getattr(previous, 'invitation', None)}
    if (previous.id != note_id or getattr(previous, 'ddate', None) or
            previous.domain != journal.venue_id or previous.forum != previous.id or
            journal.get_author_submission_id() not in invitations):
        return None
    return previous


def validate_resubmission_admission(client, journal, previous, current_authors,
                                    actor):
    current_authors = profile_ids(client, current_authors)
    previous_authors = profile_ids(client, content_value(previous, 'authorids', []) or [])
    actor_id = next(iter(profile_ids(client, [actor])), None) if actor else None
    if (not current_authors.intersection(previous_authors) or
            actor and (actor_id not in current_authors or
                       actor_id not in previous_authors)):
        raise openreview.OpenReviewException(
            'The previous submission must belong to a current author.')
    decision = latest_active_ae_decision(client, journal, previous)
    if (content_value(previous, 'venueid') != journal.rejected_venue_id or
            content_value(decision, 'recommendation') != 'Reject'):
        raise openreview.OpenReviewException(
            'The previous submission must have a released rejection decision.')
    permission = content_value(decision, 'resubmission_of_major_revision')
    if (permission is not True and not set(permission if isinstance(permission, list)
            else [permission]).intersection(RESUBMISSION_PERMISSIONS)):
        raise openreview.OpenReviewException(
            'The previous decision does not permit resubmission.')


def validate_resubmission_submission_edit(client, journal, edit, invitation=None):
    """Reject an unauthorized or changed predecessor before a note write."""
    proposed = edit.note
    field = f'previous_{journal.short_name}_submission_url'
    proposed_content = getattr(proposed, 'content', None) or {}
    existing = client.get_note(proposed.id) if getattr(proposed, 'id', None) else None
    if existing and field in proposed_content:
        if content_value(proposed, field) != content_value(existing, field):
            raise openreview.OpenReviewException(
                'The previous submission link is immutable.')
    previous_url = content_value(proposed if field in proposed_content else existing, field)
    if not previous_url:
        return None
    note_id = parse_forum_id(previous_url)
    if not note_id or getattr(proposed, 'id', None) == note_id:
        raise openreview.OpenReviewException(INVALID_PREDECESSOR)
    authors = (content_value(proposed, 'authorids', [])
               if 'authorids' in proposed_content
               else content_value(existing, 'authorids', []) if existing else [])
    actor = getattr(edit, 'tauthor', None)
    if not actor:
        signatures = list(getattr(edit, 'signatures', None) or [])
        actor = (signatures[0] if len(signatures) == 1 and
                 isinstance(signatures[0], str) and signatures[0].startswith('~')
                 else None)
    author_ids = profile_ids(client, authors or [])
    actor_id = next(iter(profile_ids(client, [actor])), None) if actor else None
    if existing and actor and actor_id not in author_ids:
        if (getattr(invitation, 'id', None) not in {
                journal.get_revision_id(number=existing.number),
                journal.get_eic_revision_id(number=existing.number)} or
                not actor_id or
                not client.get_groups(id=journal.get_editors_in_chief_id(),
                                      member=actor_id)):
            raise openreview.OpenReviewException(
                'Only current authors or an authorized Editor-in-Chief may revise.')
    if existing:
        # The immutable relationship was admitted when the successor was
        # created. Ordinary revisions must not re-evaluate mutable predecessor
        # authors or decisions; only its structural target is resolved here.
        previous = _resolve_resubmission_predecessor(client, journal, note_id)
        if (previous and parse_forum_id(content_value(previous, field)) ==
                getattr(existing, 'id', None)):
            raise openreview.OpenReviewException(INVALID_PREDECESSOR)
        return previous
    try:
        previous = _resolve_resubmission_predecessor(client, journal, note_id)
        if previous:
            validate_resubmission_admission(
                client, journal, previous, set(authors or []), actor)
    except openreview.OpenReviewException as error:
        details = error.args[0] if error.args and isinstance(error.args[0], dict) else {}
        if details.get('status', 0) >= 500:
            raise
        raise openreview.OpenReviewException(INVALID_PREDECESSOR)
    if not previous:
        raise openreview.OpenReviewException(INVALID_PREDECESSOR)
    return previous


def latest_active_ae_decision(client, journal, submission):
    return max((note for note in client.get_notes(
        invitation=journal.get_ae_decision_id(number=submission.number))
        if not getattr(note, 'ddate', None)), key=lambda note:
        (getattr(note, 'tcdate', None) or 0, getattr(note, 'id', None) or ''), default=None)


def get_previous_assignments(client, journal, previous, role='ae'):
    getter = journal.get_ae_assignment_id if role == 'ae' else journal.get_reviewer_assignment_id
    found = {}
    edge_key = lambda edge: (getattr(edge, 'tcdate', None) or 0,
                             getattr(edge, 'id', None) or '')
    get_edges = getattr(client, 'get_all_edges', None) or client.get_edges
    for archived in (False, True):
        for edge in get_edges(invitation=getter(archived=archived), head=previous.id):
            if (not getattr(edge, 'ddate', None) and
                    (edge.tail not in found or edge_key(edge) > edge_key(found[edge.tail]))):
                found[edge.tail] = edge
    return sorted(found.values(), key=edge_key, reverse=True)


def active_prior_assignment(client, journal, submission, profile_id, role='ae'):
    previous = resolve_resubmission_predecessor(client, journal, submission)
    return bool(previous and any(edge.tail == profile_id
        for edge in get_previous_assignments(client, journal, previous, role)))


def ensure_resubmission_ae_access(client, journal, submission):
    previous = resolve_resubmission_predecessor(client, journal, submission)
    if not previous:
        return None
    successor = journal.get_action_editors_id(number=submission.number)
    predecessor = journal.get_action_editors_id(number=previous.number)
    group = client.get_group(predecessor)
    if successor not in (group.members or []):
        client.add_members_to_group(predecessor, [successor])
        group = client.get_group(predecessor)
    if successor not in (group.members or []):
        raise openreview.OpenReviewException('Prior-round Action Editor access was not granted.')
    return previous


def validate_ae_continuity_assignment(client, journal, edge, submission):
    if not active_prior_assignment(client, journal, submission, edge.tail):
        return False
    if client.get_groups(id=journal.get_authors_id(number=submission.number), member=edge.tauthor):
        raise openreview.OpenReviewException('Authors cannot edit Action Editor assignments.')
    if not journal.is_active_submission(submission):
        raise openreview.OpenReviewException('Action Editor assignments require an active submission.')
    if edge.tail not in (client.get_group(journal.get_action_editors_id()).members or []):
        raise openreview.OpenReviewException('Previous Action Editor is not a current Action Editor.')
    if journal.assignment.compute_conflicts(submission, edge.tail):
        raise openreview.OpenReviewException(f'Conflict detected for {edge.tail}.')
    return True


def prepare_resubmission_continuity(client, journal, submission):
    """Assign the newest qualifying prior AE, preserving the availability exception."""
    if (journal.settings.get('resubmission_continuity_enabled') is not True or
            journal.settings.get('resubmission_continuity', 'score') != 'immediate_previous_ae'):
        return None
    previous = ensure_resubmission_ae_access(client, journal, submission)
    if not previous:
        return None
    if any(not getattr(edge, 'ddate', None) for edge in client.get_edges(
            invitation=journal.get_ae_assignment_id(), head=submission.id)):
        return None
    roster = set(client.get_group(journal.get_action_editors_id()).members or [])
    for prior in get_previous_assignments(client, journal, previous):
        if prior.tail not in roster or journal.assignment.compute_conflicts(submission, prior.tail):
            continue
        proposed = openreview.api.Edge(
            invitation=journal.get_ae_assignment_id(),
            signatures=[journal.get_editors_in_chief_id()], head=submission.id,
            tail=prior.tail, weight=1, label='Resubmission continuity')
        try:
            return client.post_edge(proposed)
        except Exception:
            exact = [edge for edge in client.get_edges(
                invitation=journal.get_ae_assignment_id(), head=submission.id,
                tail=prior.tail) if not getattr(edge, 'ddate', None)]
            if len(exact) == 1:
                return exact[0]
            raise
    return None


def prior_reviewer_ids(client, journal, previous):
    return sorted({edge.tail for edge in get_previous_assignments(
                   client, journal, previous, 'reviewer') if isinstance(edge.tail, str)
                   and re.fullmatch(r'~[^\s/]*\d+', edge.tail)})


def active_prior_reviewer_assignment(client, journal, submission, reviewer_id):
    previous = resolve_resubmission_predecessor(client, journal, submission)
    return bool(previous and reviewer_id in prior_reviewer_ids(client, journal, previous))
