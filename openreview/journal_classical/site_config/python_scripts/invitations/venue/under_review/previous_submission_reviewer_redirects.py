"""Add prior-reviewer continuity that Journal's load-filtered browser cannot expose."""

REDIRECT_SCRIPT = "{{WEB_FRAGMENT_JSON:assignment_launchers/previous_reviewer_redirects.js}}"
REDIRECT_BEGIN = '// JMLR PREVIOUS REVIEWER REDIRECTS BEGIN'
REDIRECT_END = '// JMLR PREVIOUS REVIEWER REDIRECTS END'

# {{PYTHON_SCRIPT_FILE:invitations/venue/under_review/previous_submission_reviewer_policy.py}}


def profile_display_name(profile, fallback):
    """Use profile name fields only; never inspect contact fields."""
    content = getattr(profile, 'content', None) or {}
    names = content.get('names') or []
    preferred = next(
        (name for name in names if isinstance(name, dict) and name.get('preferred')),
        None,
    )
    ordered = ([preferred] if preferred else []) + list(names)
    for name in ordered:
        if not isinstance(name, dict):
            continue
        fullname = name.get('fullname')
        if isinstance(fullname, str) and fullname.strip():
            return fullname.strip()
    return fallback


def safe_reviewer_rows(client, reviewer_ids):
    rows = []
    for reviewer_id in reviewer_ids:
        try:
            display_name = profile_display_name(client.get_profile(reviewer_id), reviewer_id)
        except Exception:
            display_name = reviewer_id
        rows.append({'id': reviewer_id, 'displayName': display_name})
    rows.sort(key=lambda row: (row['displayName'].casefold(), row['id']))
    counts = {}
    for row in rows:
        key = row['displayName'].casefold()
        counts[key] = counts.get(key, 0) + 1
    for row in rows:
        if counts[row['displayName'].casefold()] > 1:
            row['displayName'] = f"{row['displayName']} ({row['id']})"
    return rows


def active_reviewer_assignment_ids(client, journal, submission):
    """Return active profile tails already assigned to this submission."""
    try:
        edges = client.get_edges(
            invitation=journal.get_reviewer_assignment_id(),
            head=submission.id,
        )
    except Exception:
        return set()
    return {
        edge.tail
        for edge in edges
        if not getattr(edge, 'ddate', None)
        and is_openreview_profile_id(getattr(edge, 'tail', None))
    }


def paper_action_editor_signature_id(client, journal, submission):
    """Resolve the one anonymous AE identity belonging to the paper's AE."""
    try:
        paper_group = client.get_group(
            journal.get_action_editors_id(number=submission.number)
        )
        paper_members = set(getattr(paper_group, 'members', None) or [])
        prefix = journal.get_action_editors_id(
            number=submission.number, anon=True
        )
        matching = {
            group.id
            for group in client.get_groups(prefix=prefix)
            if isinstance(getattr(group, 'id', None), str)
            and group.id.startswith(prefix)
            and paper_members.intersection(
                set(getattr(group, 'members', None) or [])
            )
        }
    except Exception:
        return None
    return next(iter(matching)) if len(matching) == 1 else None


def _without_redirect_overlay(web):
    import re

    return re.sub(
        r'\n?' + re.escape(REDIRECT_BEGIN) + r'.*?' + re.escape(REDIRECT_END) + r'\n?',
        '',
        web or '',
        flags=re.DOTALL,
    )


def reviewer_assignment_browser_web(web, previous_forum_id, reviewers, assignment=None):
    """Add continuity context without rebuilding Journal's browser parameters."""
    import json

    web = _without_redirect_overlay(web)
    config = {
        'previousForumId': previous_forum_id,
        'reviewers': reviewers,
        **(assignment or {}),
    }
    config_json = json.dumps(config)
    for unsafe, escaped in (
        ('&', '\\u0026'),
        ('<', '\\u003c'),
        ('>', '\\u003e'),
        ('\u2028', '\\u2028'),
        ('\u2029', '\\u2029'),
    ):
        config_json = config_json.replace(unsafe, escaped)
    injection = (
        '\n' + REDIRECT_BEGIN + '\n'
        + 'var JMLR_PREVIOUS_REVIEWER_REDIRECTS = ' + config_json + ';\n'
        + REDIRECT_SCRIPT + '\n'
        + 'JMLRPreviousReviewerRedirects.install(JMLR_PREVIOUS_REVIEWER_REDIRECTS);\n'
        + REDIRECT_END + '\n'
    )
    marker = '// Go!\nmain();'
    return web.replace(marker, injection + marker) if marker in web else web + injection


def wait_for_native_invitation(client, invitation_id, timeout=30, poll_interval=1):
    """Wait for concurrent native setup without hiding non-not-found failures."""
    import time

    deadline = time.monotonic() + timeout
    while True:
        try:
            return client.get_invitation(invitation_id)
        except Exception as error:
            status = getattr(error, 'status_code', None)
            if status is None:
                status = getattr(
                    getattr(error, 'response', None), 'status_code', None
                )
            structured = error.args[0] if len(error.args) == 1 else None
            if status is None and isinstance(structured, dict):
                status = structured.get('status')
            name = structured.get('name') if isinstance(structured, dict) else None
            if status != 404 or name not in (None, 'NotFoundError'):
                raise
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise RuntimeError(
                'Reviewer assignment setup did not become ready.'
            )
        time.sleep(min(poll_interval, remaining))


def prepare_previous_submission_reviewer_redirects(client, journal, submission):
    """Prepare one paper-child launcher; invalid history degrades to generic."""
    previous = resolve_previous_submission(client, journal, submission)
    reviewer_ids = prior_reviewer_ids(client, journal, previous) if previous else []
    reviewers = safe_reviewer_rows(client, reviewer_ids) if reviewer_ids else []
    assigned_ids = active_reviewer_assignment_ids(client, journal, submission)
    for reviewer in reviewers:
        reviewer['assigned'] = reviewer['id'] in assigned_ids
    invitation_id = journal.get_reviewer_assignment_id(number=submission.number)
    invitation = wait_for_native_invitation(client, invitation_id)
    current_web = invitation.web or ''
    desired_web = reviewer_assignment_browser_web(
        current_web,
        getattr(previous, 'id', None) if previous else None,
        reviewers,
        {
            'venueId': journal.venue_id,
            'submissionId': submission.id,
            'assignmentInvitationId': journal.get_reviewer_assignment_id(),
            'paperActionEditorsId': journal.get_action_editors_id(
                number=submission.number
            ),
            'paperActionEditorSignatureId': paper_action_editor_signature_id(
                client, journal, submission
            ),
            'paperAuthorsId': journal.get_authors_id(number=submission.number),
        } if previous and reviewers else None,
    )
    if desired_web == current_web:
        return
    invitation.web = desired_web
    client.post_invitation_edit(
        invitations=journal.get_meta_invitation_id(),
        signatures=[journal.venue_id],
        invitation=invitation,
        replacement=True,
    )
