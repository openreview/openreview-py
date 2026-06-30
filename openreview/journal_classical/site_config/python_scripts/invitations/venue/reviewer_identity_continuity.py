def content_value(note_or_invitation, field_name, default=''):
    content = note_or_invitation.get('content', {}) if isinstance(note_or_invitation, dict) else getattr(note_or_invitation, 'content', {})
    field = (content or {}).get(field_name, {})
    if isinstance(field, dict):
        return field.get('value', default)
    return field or default


def internal_readers(journal, submission):
    return [journal.venue_id]


def metadata_field_name():
    return '_reviewer_identity_continuity'


def legacy_metadata_field_name():
    return 'reviewer_identity_continuity'


def is_valid_reviewer_profile_id(journal, reviewer_profile_id):
    if not reviewer_profile_id:
        return False
    reviewer_profile_id = str(reviewer_profile_id)
    if reviewer_profile_id == journal.get_reviewers_id():
        return False
    if reviewer_profile_id.startswith(f'{journal.venue_id}/'):
        return False
    return True


def parse_json(value, fallback):
    import json

    if not value:
        return fallback
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except Exception:
        return fallback


def reviewer_anon_id_from_signature(signature):
    if not signature or '/Reviewer_' not in str(signature):
        return ''
    return str(signature).split('/Reviewer_', 1)[1].split('/', 1)[0]


def reviewer_anon_id_from_group_id(group_id):
    return reviewer_anon_id_from_signature(group_id)


def is_reviewer_scoring_input_anon_id(anon_id):
    return str(anon_id or '') == 'Scoring_Input'


def reviewer_anon_id_from_decision_field(field_name):
    return str(field_name or '').replace('resubmission_auto_assign_reviewer_', '', 1).replace('reviewer_', '', 1)


def reviewer_anon_id_from_checkbox_value(value):
    import re

    match = re.search(r'Reviewer\s+([^:\s]+)', str(value or ''))
    return match.group(1) if match else ''


def reviewer_anon_id_from_rating_invitation_id(invitation_id):
    return reviewer_anon_id_from_signature(invitation_id)


def reviewer_rating_invitation_has_selection_field(invitation):
    edit = getattr(invitation, 'edit', None) or {}
    if not isinstance(edit, dict):
        return False
    content = edit.get('note', {}).get('content', {})
    return 'resubmission_auto_assignment' in content


def stable_reviewer_number_from_row(row):
    import re

    if not isinstance(row, dict):
        return None
    value = row.get('stable_number') or row.get('reviewer_number')
    try:
        number = int(value)
        return number if number > 0 else None
    except Exception:
        pass
    label = str(row.get('stable_label') or '')
    match = re.search(r'Reviewer\s+(\d+)', label)
    if match:
        try:
            return int(match.group(1))
        except Exception:
            return None
    return None


def stable_reviewer_label(number):
    return f'Reviewer {number}' if number else ''


def reviewer_anon_display_label(current_anon_id='', stable_number=None, previous_anon_id=''):
    anon_id = current_anon_id or previous_anon_id
    base = f'Reviewer {anon_id}' if anon_id else 'Reviewer'
    number_label = stable_reviewer_label(stable_number)
    return f'{base} ({number_label})' if number_label else base


def truthy_content_value(value):
    if isinstance(value, list):
        return bool(value)
    if isinstance(value, str):
        return bool(value.strip()) and value.strip() not in ('false', 'False', '0', 'No')
    return value is True or value == 1


def parse_forum_id(url):
    if not url or str(url).strip().upper() == 'N/A':
        return None
    try:
        from urllib.parse import parse_qs, urlparse
        parsed = urlparse(str(url))
        forum_ids = parse_qs(parsed.query).get('id')
        if forum_ids and forum_ids[0]:
            return forum_ids[0]
    except Exception:
        pass
    try:
        return str(url).split('forum?id=', 1)[1].split('&', 1)[0]
    except Exception:
        return None


def previous_forum_id_from_list(submission):
    import re

    value = content_value(submission, 'previous_JMLR_submissions')
    match = re.search(r'forum\?id=([A-Za-z0-9_-]+)', str(value or ''))
    return match.group(1) if match else None


def resolve_previous_submission(client, journal, submission):
    previous_url = content_value(submission, 'previous_JMLR_submission_URL')
    previous_forum_id = parse_forum_id(previous_url)
    if previous_forum_id:
        try:
            return client.get_note(previous_forum_id)
        except Exception as error:
            print(f'Could not load previous submission {previous_forum_id}: {error}')
            return None

    previous_number = str(content_value(submission, 'previous_JMLR_submission_number') or '').strip()
    if not previous_number or previous_number.upper() == 'N/A':
        previous_forum_id = previous_forum_id_from_list(submission)
        if previous_forum_id:
            try:
                return client.get_note(previous_forum_id)
            except Exception as error:
                print(f'Could not load previous submission {previous_forum_id}: {error}')
        return None
    try:
        previous_notes = client.get_notes(
            invitation=f'{journal.venue_id}/-/Submission',
            number=int(previous_number)
        )
        return previous_notes[0] if previous_notes else None
    except Exception as error:
        print(f'Could not load previous submission number {previous_number}: {error}')
        return None


def get_eligible_previous_decision(client, journal, previous_submission):
    if not previous_submission:
        return None
    eligible = {
        'Accept after minor revisions',
        'Accept with minor revision',
        'Reject with encouragement to resubmit'
    }
    try:
        decisions = client.get_notes(
            forum=previous_submission.id,
            invitation=journal.get_ae_decision_id(number=previous_submission.number)
        )
    except Exception as error:
        print(f'Could not load previous decisions for Paper{previous_submission.number}: {error}')
        return None
    for decision in decisions:
        if not getattr(decision, 'ddate', None) and content_value(decision, 'recommendation') in eligible:
            return decision
    return None


def selected_previous_reviewer_anon_ids(previous_decision):
    if not previous_decision:
        return []
    selected = []
    checkbox_value = content_value(previous_decision, 'reviewers')
    checkbox_values = checkbox_value if isinstance(checkbox_value, list) else ([checkbox_value] if checkbox_value else [])
    for value in checkbox_values:
        anon_id = reviewer_anon_id_from_checkbox_value(value)
        if anon_id and anon_id not in selected:
            selected.append(anon_id)
    for field_name, field in (previous_decision.content or {}).items():
        if field_name == 'reviewer_auto_assignment':
            continue
        if not (field_name.startswith('reviewer_') or field_name.startswith('resubmission_auto_assign_reviewer_')):
            continue
        if truthy_content_value(field.get('value') if isinstance(field, dict) else field):
            anon_id = reviewer_anon_id_from_decision_field(field_name)
            if anon_id and anon_id not in selected:
                selected.append(anon_id)
    return selected


def previous_reviewer_profile_id(client, journal, previous_submission, previous_anon_id):
    if not previous_submission or not previous_anon_id:
        return ''
    try:
        group = client.get_group(f'{journal.venue_id}/Paper{previous_submission.number}/Reviewer_{previous_anon_id}')
        members = group.members or []
        return members[0] if members else ''
    except Exception as error:
        print(f'Could not resolve previous reviewer {previous_anon_id} on Paper{previous_submission.number}: {error}')
        return ''


def previous_reviewer_anon_id(client, journal, previous_submission, reviewer_profile_id):
    if not previous_submission or not reviewer_profile_id:
        return ''
    try:
        groups = client.get_groups(prefix=f'{journal.venue_id}/Paper{previous_submission.number}/Reviewer_')
    except Exception as error:
        print(f'Could not load previous reviewer groups for Paper{previous_submission.number}: {error}')
        return ''
    for group in groups:
        anon_id = reviewer_anon_id_from_group_id(group.id)
        if is_reviewer_scoring_input_anon_id(anon_id):
            continue
        if reviewer_profile_id in (group.members or []):
            return anon_id
    return ''


def selected_previous_reviewer_profile_ids_from_ratings(client, journal, previous_submission):
    if not previous_submission:
        return [], False
    selected_profile_ids = []
    has_rating_selection_field = False
    try:
        previous_submission_with_replies = client.get_note(previous_submission.id, details='replies')
        rating_notes = [
            reply for reply in previous_submission_with_replies.details.get('replies', [])
            if reply.get('invitations') and reply['invitations'][0].endswith('/-/Rating') and not reply.get('ddate')
        ]
    except Exception as error:
        print(f'Could not load previous reviewer rating notes for Paper{previous_submission.number}: {error}')
        rating_notes = []
    for rating_note in rating_notes:
        if 'resubmission_auto_assignment' not in (rating_note.get('content') or {}):
            continue
        has_rating_selection_field = True
        if not truthy_content_value(content_value(rating_note, 'resubmission_auto_assignment')):
            continue
        profile_id = content_value(rating_note, 'reviewer_profile_id')
        if not profile_id:
            anon_id = content_value(rating_note, 'reviewer_anon_id') or reviewer_anon_id_from_rating_invitation_id((rating_note.get('invitations') or [''])[0])
            profile_id = previous_reviewer_profile_id(client, journal, previous_submission, anon_id)
        if profile_id and profile_id not in selected_profile_ids:
            selected_profile_ids.append(profile_id)
    try:
        for rating_invitation in client.get_all_invitations(prefix=f'{journal.venue_id}/Paper{previous_submission.number}/Reviewer_'):
            if (
                rating_invitation.id.endswith('/-/Rating')
                and not getattr(rating_invitation, 'ddate', None)
                and reviewer_rating_invitation_has_selection_field(rating_invitation)
            ):
                has_rating_selection_field = True
                break
    except Exception as error:
        print(f'Could not load previous reviewer rating invitations for Paper{previous_submission.number}: {error}')
    return selected_profile_ids, has_rating_selection_field


def current_reviewer_anon_by_profile(client, journal, submission):
    by_profile = {}
    try:
        groups = client.get_groups(prefix=f'{journal.venue_id}/Paper{submission.number}/Reviewer_')
    except Exception as error:
        print(f'Could not load current reviewer groups for Paper{submission.number}: {error}')
        groups = []
    for group in groups:
        anon_id = reviewer_anon_id_from_group_id(group.id)
        if not anon_id or is_reviewer_scoring_input_anon_id(anon_id):
            continue
        for member in group.members or []:
            by_profile[member] = anon_id
    return by_profile


def active_reviewer_assignment_tails(client, journal, submission):
    assignment_invitations = [
        journal.get_reviewer_assignment_id(),
        journal.get_reviewer_assignment_id(number=submission.number)
    ]
    tails = set()
    for assignment_invitation in assignment_invitations:
        try:
            tails.update(
                edge.tail
                for edge in client.get_edges(invitation=assignment_invitation, head=submission.id)
                if getattr(edge, 'tail', None) and not getattr(edge, 'ddate', None)
            )
        except Exception as error:
            print(f'Could not load current reviewer assignments for Paper{submission.number} from {assignment_invitation}: {error}')
    return tails


def load_reviewer_identity_continuity(submission):
    metadata = parse_json(content_value(submission, metadata_field_name()), {})
    if not metadata:
        metadata = parse_json(content_value(submission, legacy_metadata_field_name()), {})
    rows = metadata.get('reviewers', []) if isinstance(metadata, dict) else []
    by_profile = {}
    by_previous_anon = {}
    by_current_anon = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        stable_number = stable_reviewer_number_from_row(row)
        if stable_number:
            row['stable_number'] = stable_number
            row['stable_label'] = stable_reviewer_label(stable_number)
        if row.get('reviewer_profile_id'):
            by_profile[row['reviewer_profile_id']] = row
        if row.get('previous_anon_id'):
            by_previous_anon[row['previous_anon_id']] = row
        if row.get('current_anon_id'):
            by_current_anon[row['current_anon_id']] = row
    return {
        'reviewers': rows,
        'by_profile': by_profile,
        'by_previous_anon': by_previous_anon,
        'by_current_anon': by_current_anon
    }


def reviewer_display_label(submission, reviewer_profile_id='', previous_anon_id='', current_anon_id=''):
    metadata = load_reviewer_identity_continuity(submission)
    row = None
    if reviewer_profile_id:
        row = metadata['by_profile'].get(reviewer_profile_id)
    if not row and current_anon_id:
        row = metadata['by_current_anon'].get(current_anon_id)
    if not row and previous_anon_id:
        row = metadata['by_previous_anon'].get(previous_anon_id)
    if row:
        stable_number = stable_reviewer_number_from_row(row)
        return reviewer_anon_display_label(
            current_anon_id or row.get('current_anon_id', ''),
            stable_number,
            previous_anon_id or row.get('previous_anon_id', '')
        )
    if current_anon_id:
        return f'Reviewer {current_anon_id}'
    if previous_anon_id:
        return f'Reviewer {previous_anon_id}'
    return 'Reviewer'


def compact_reviewer_display_label(submission, reviewer_profile_id='', previous_anon_id='', current_anon_id=''):
    metadata = load_reviewer_identity_continuity(submission)
    row = None
    if reviewer_profile_id:
        row = metadata['by_profile'].get(reviewer_profile_id)
    if not row and current_anon_id:
        row = metadata['by_current_anon'].get(current_anon_id)
    if not row and previous_anon_id:
        row = metadata['by_previous_anon'].get(previous_anon_id)
    if row:
        stable_number = stable_reviewer_number_from_row(row)
        return stable_reviewer_label(stable_number) or reviewer_anon_display_label(
            current_anon_id or row.get('current_anon_id', ''),
            stable_number,
            previous_anon_id or row.get('previous_anon_id', '')
        )
    if current_anon_id:
        return f'Reviewer {current_anon_id}'
    if previous_anon_id:
        return f'Reviewer {previous_anon_id}'
    return 'Reviewer'


def store_reviewer_identity_continuity(client, journal, submission, rows):
    import json

    payload = {
        'version': 1,
        'reviewers': rows
    }
    client.post_note_edit(
        invitation=journal.get_meta_invitation_id(),
        signatures=[journal.venue_id],
        note=openreview.api.Note(
            id=submission.id,
            content={
                metadata_field_name(): {
                    'value': json.dumps(payload, sort_keys=True),
                    'readers': internal_readers(journal, submission)
                }
            }
        )
    )


def merge_continuity_rows(existing_rows, new_rows):
    by_profile = {
        row.get('reviewer_profile_id'): dict(row)
        for row in existing_rows
        if isinstance(row, dict) and row.get('reviewer_profile_id')
    }
    for row in new_rows:
        profile_id = row.get('reviewer_profile_id')
        if not profile_id:
            continue
        merged = by_profile.get(profile_id, {})
        merged.update({key: value for key, value in row.items() if value not in (None, '')})
        stable_number = stable_reviewer_number_from_row(merged)
        if stable_number:
            merged['stable_number'] = stable_number
            merged['stable_label'] = stable_reviewer_label(stable_number)
        by_profile[profile_id] = merged
    return list(by_profile.values())


def max_stable_reviewer_number(rows):
    maximum = 0
    for row in rows or []:
        number = stable_reviewer_number_from_row(row)
        if number and number > maximum:
            maximum = number
    return maximum


def previous_reviewer_rows_for_submission(client, journal, previous_submission):
    if not previous_submission:
        return []
    metadata = load_reviewer_identity_continuity(previous_submission)
    metadata_by_profile = metadata.get('by_profile', {})
    metadata_by_previous_anon = metadata.get('by_previous_anon', {})
    metadata_by_current_anon = metadata.get('by_current_anon', {})
    seen_profiles = set()
    rows = []
    assignment_invitations = [
        journal.get_reviewer_assignment_id(),
        journal.get_reviewer_assignment_id(archived=True),
        journal.get_reviewer_assignment_id(number=previous_submission.number)
    ]
    assignments = []
    for assignment_invitation in assignment_invitations:
        try:
            assignments.extend(
                edge for edge in client.get_edges(invitation=assignment_invitation, head=previous_submission.id)
                if not getattr(edge, 'ddate', None)
            )
        except Exception:
            continue
    assignments = sorted(assignments, key=lambda edge: (getattr(edge, 'cdate', 0) or 0, getattr(edge, 'tail', '') or ''))
    for assignment in assignments:
        profile_id = assignment.tail
        if not profile_id or profile_id in seen_profiles:
            continue
        previous_anon_id = ''
        try:
            for group in client.get_groups(prefix=f'{journal.venue_id}/Paper{previous_submission.number}/Reviewer_'):
                group_anon_id = reviewer_anon_id_from_group_id(group.id)
                if is_reviewer_scoring_input_anon_id(group_anon_id):
                    continue
                if profile_id in (group.members or []):
                    previous_anon_id = group_anon_id
                    break
        except Exception:
            previous_anon_id = ''
        prior_row = (
            metadata_by_profile.get(profile_id)
            or metadata_by_current_anon.get(previous_anon_id)
            or metadata_by_previous_anon.get(previous_anon_id)
            or {}
        )
        stable_number = stable_reviewer_number_from_row(prior_row) or (len(rows) + 1)
        rows.append({
            'stable_number': stable_number,
            'stable_label': stable_reviewer_label(stable_number),
            'previous_submission_number': str(previous_submission.number),
            'previous_submission_id': previous_submission.id,
            'previous_anon_id': previous_anon_id,
            'reviewer_profile_id': profile_id
        })
        seen_profiles.add(profile_id)
    return rows


def ensure_stable_reviewer_number_for_assignment(client, journal, submission, reviewer_profile_id):
    if not is_valid_reviewer_profile_id(journal, reviewer_profile_id):
        return None
    try:
        submission = client.get_note(submission.id)
    except Exception as error:
        print(f'Could not refresh submission before stable reviewer numbering for Paper{submission.number}: {error}')
    metadata = load_reviewer_identity_continuity(submission)
    rows = [dict(row) for row in metadata.get('reviewers', []) if isinstance(row, dict)]
    by_profile = {
        row.get('reviewer_profile_id'): row
        for row in rows
        if row.get('reviewer_profile_id')
    }
    row = dict(by_profile.get(reviewer_profile_id) or {'reviewer_profile_id': reviewer_profile_id})
    previous_submission = resolve_previous_submission(client, journal, submission)
    previous_rows = previous_reviewer_rows_for_submission(client, journal, previous_submission)
    previous_row = None
    for candidate in previous_rows:
        if candidate.get('reviewer_profile_id') == reviewer_profile_id:
            previous_row = candidate
            break
    if previous_row:
        row.update({key: value for key, value in previous_row.items() if value not in (None, '')})
        row['copied_from_previous_reviewer_number'] = True
        row['suggested_for_reassignment'] = True
    stable_number = stable_reviewer_number_from_row(row)
    if not stable_number:
        previous_max_stable_number = max_stable_reviewer_number(previous_rows)
        current_max_stable_number = max_stable_reviewer_number(rows)
        stable_number = max(previous_max_stable_number, current_max_stable_number) + 1
        row['new_reviewer_number'] = True
    row['stable_number'] = stable_number
    row['stable_label'] = stable_reviewer_label(stable_number)
    row['current_anon_id'] = current_reviewer_anon_by_profile(client, journal, submission).get(
        reviewer_profile_id,
        row.get('current_anon_id', '')
    )
    merged_rows = merge_continuity_rows(rows, [row])
    store_reviewer_identity_continuity(client, journal, submission, merged_rows)
    return row


def record_selected_previous_reviewer_suggestions(client, journal, submission):
    previous_submission = resolve_previous_submission(client, journal, submission)
    selected_profile_ids, rating_selection_is_authoritative = selected_previous_reviewer_profile_ids_from_ratings(client, journal, previous_submission)
    selected_anon_ids = []
    if not rating_selection_is_authoritative:
        previous_decision = get_eligible_previous_decision(client, journal, previous_submission)
        selected_anon_ids = selected_previous_reviewer_anon_ids(previous_decision)
        selected_profile_ids = [
            previous_reviewer_profile_id(client, journal, previous_submission, previous_anon_id)
            for previous_anon_id in selected_anon_ids
        ]
        selected_profile_ids = [profile_id for profile_id in selected_profile_ids if profile_id]
    if not previous_submission or not selected_profile_ids:
        return []

    existing_metadata = load_reviewer_identity_continuity(submission)
    previous_rows_by_anon = {
        row.get('previous_anon_id'): row
        for row in previous_reviewer_rows_for_submission(client, journal, previous_submission)
        if row.get('previous_anon_id')
    }
    rows = []
    for index, reviewer_profile_id in enumerate(selected_profile_ids, start=1):
        previous_anon_id = previous_reviewer_anon_id(client, journal, previous_submission, reviewer_profile_id)
        previous_row = previous_rows_by_anon.get(previous_anon_id, {})
        stable_number = stable_reviewer_number_from_row(previous_row) or index
        rows.append({
            'stable_number': stable_number,
            'stable_label': stable_reviewer_label(stable_number),
            'previous_submission_number': str(previous_submission.number),
            'previous_submission_id': previous_submission.id,
            'previous_anon_id': previous_anon_id,
            'reviewer_profile_id': reviewer_profile_id,
            'current_anon_id': '',
            'suggested_for_reassignment': True,
            'auto_assigned': False
        })

    current_anon_by_profile = current_reviewer_anon_by_profile(client, journal, submission)
    for row in rows:
        row['current_anon_id'] = current_anon_by_profile.get(row.get('reviewer_profile_id'), '')

    merged_rows = merge_continuity_rows(existing_metadata['reviewers'], rows)
    if merged_rows:
        try:
            store_reviewer_identity_continuity(client, journal, submission, merged_rows)
        except Exception as error:
            print(f'Could not store reviewer identity continuity metadata for Paper{submission.number}: {error}')

    return rows


def prepare_selected_previous_reviewers_for_assignment(client, journal, submission):
    candidates = record_selected_previous_reviewer_suggestions(client, journal, submission)
    if not candidates:
        return {'candidates': []}

    try:
        existing_metadata = load_reviewer_identity_continuity(submission)
        current_anon_by_profile = current_reviewer_anon_by_profile(client, journal, submission)
        updated_rows = []
        for row in merge_continuity_rows(existing_metadata['reviewers'], candidates):
            profile_id = row.get('reviewer_profile_id')
            row['current_anon_id'] = current_anon_by_profile.get(profile_id, row.get('current_anon_id', ''))
            row['suggested_for_reassignment'] = True
            row['prepared_for_assignment_page'] = True
            row.pop('auto_assignment_result', None)
            row.pop('auto_assignment_error', None)
            updated_rows.append(row)
        if updated_rows:
            store_reviewer_identity_continuity(client, journal, submission, updated_rows)
    except Exception as error:
        print(f'Could not prepare reviewer identity continuity metadata for Paper{submission.number}: {error}')

    return {'candidates': candidates}


def refresh_current_reviewer_identity_metadata(client, journal, submission):
    metadata = load_reviewer_identity_continuity(submission)
    rows = metadata.get('reviewers', [])
    if not rows:
        return []
    current_anon_by_profile = current_reviewer_anon_by_profile(client, journal, submission)
    changed = False
    for row in rows:
        profile_id = row.get('reviewer_profile_id')
        current_anon_id = current_anon_by_profile.get(profile_id, '')
        if current_anon_id and row.get('current_anon_id') != current_anon_id:
            row['current_anon_id'] = current_anon_id
            changed = True
    if changed:
        store_reviewer_identity_continuity(client, journal, submission, rows)
    return rows


def mark_previous_reviewers_auto_assigned(client, journal, submission, reviewer_profile_ids):
    reviewer_profile_ids = set(reviewer_profile_ids or [])
    if not reviewer_profile_ids:
        return []
    metadata = load_reviewer_identity_continuity(submission)
    rows = metadata.get('reviewers', [])
    if not rows:
        return []
    current_anon_by_profile = current_reviewer_anon_by_profile(client, journal, submission)
    changed = False
    for row in rows:
        profile_id = row.get('reviewer_profile_id')
        if profile_id not in reviewer_profile_ids:
            continue
        row['auto_assigned'] = True
        row['auto_assignment_result'] = 'assigned'
        row['suggested_for_reassignment'] = True
        current_anon_id = current_anon_by_profile.get(profile_id, '')
        if current_anon_id and row.get('current_anon_id') != current_anon_id:
            row['current_anon_id'] = current_anon_id
        changed = True
    if changed:
        store_reviewer_identity_continuity(client, journal, submission, rows)
    return rows


def refresh_reviewer_continuity_display_surfaces(client, journal, submission, reviewer_assignment_duedate=None, refreshers=None):
    for refresher in refreshers or []:
        try:
            refresher(client, journal, submission, reviewer_assignment_duedate)
        except Exception as error:
            print(f'Could not refresh reviewer continuity display surface for Paper{submission.number}: {error}')


def format_previous_reviewer_assignment_prep_for_email(previous_reviewer_assignment_prep_results):
    results = previous_reviewer_assignment_prep_results or {}
    candidates = results.get('candidates') or []
    if not candidates:
        return ''
    lines = [
        'Previous reviewer continuity',
        '',
        'This resubmission has previous reviewers selected for continuity. When the EIC setup action can complete the checked reviewer-assignment flow, these reviewers may already be assigned. Otherwise, they are prepared on the Assign Reviewers page and should be checked by default there when they are not already assigned:'
    ]
    for row in candidates:
        label = row.get('stable_label') or stable_reviewer_label(stable_reviewer_number_from_row(row)) or 'Reviewer'
        previous_anon = row.get('previous_anon_id') or 'unknown'
        profile_id = row.get('reviewer_profile_id') or 'unknown profile'
        lines.append(f'- {label}: previously Reviewer {previous_anon}; reviewer profile {profile_id}.')
    lines.extend([
        '',
        'Please open the Assign Reviewers page to inspect the current assignments, confirm any carried-forward reviewers, and add or adjust reviewers as needed.'
    ])
    return '\n'.join(lines)


def format_previous_reviewer_suggestions_for_email(previous_reviewer_suggestions):
    return format_previous_reviewer_assignment_prep_for_email({'candidates': previous_reviewer_suggestions or []})
