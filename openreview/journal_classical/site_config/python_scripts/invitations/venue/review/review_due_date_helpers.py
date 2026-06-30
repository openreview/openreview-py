DAY_MILLIS = 86400000
WEEK_MILLIS = 7 * DAY_MILLIS
REVIEW_REMINDER_WEEK_COUNT = 26
REVIEW_REMINDER_OFFSETS_MILLIS = [DAY_MILLIS] + [
    week * WEEK_MILLIS for week in range(1, REVIEW_REMINDER_WEEK_COUNT + 1)
]
REVIEW_REMINDER_SCRIPT = globals().get('REVIEW_REMINDER_SCRIPT')


def _content_value(content, key):
    value = (content or {}).get(key)
    if isinstance(value, dict) and 'value' in value:
        return value.get('value')
    return value


def _int_or_none(value):
    if value is None:
        return None
    try:
        return int(value)
    except Exception:
        return None


def edge_time_millis(edge):
    return (
        getattr(edge, 'cdate', None)
        or getattr(edge, 'tcdate', None)
        or getattr(edge, 'tmdate', None)
    )


def active_reviewer_assignment_edges(client, journal, submission):
    edges = []
    seen = set()
    invitation_ids = [
        journal.get_reviewer_assignment_id(number=submission.number),
        journal.get_reviewer_assignment_id()
    ]
    for invitation_id in invitation_ids:
        try:
            candidates = client.get_edges(invitation=invitation_id, head=submission.id)
        except Exception as error:
            print(f'Could not load reviewer assignments for Paper{submission.number}: {error}')
            continue
        for edge in candidates:
            if getattr(edge, 'ddate', None) or not getattr(edge, 'tail', None):
                continue
            if edge.tail in seen:
                continue
            seen.add(edge.tail)
            edges.append(edge)
    return edges


def reviewer_due_date_edge_invitation_id(journal):
    return f'{journal.venue_id}/Reviewers/-/Review_Due_Date'


def active_reviewer_due_date_edges_by_tail(client, journal, submission):
    try:
        edges = client.get_edges(
            invitation=reviewer_due_date_edge_invitation_id(journal),
            head=submission.id
        )
    except Exception as error:
        print(f'Could not load reviewer due-date edges for Paper{submission.number}: {error}')
        return {}
    by_tail = {}
    for edge in edges:
        if getattr(edge, 'ddate', None) or not getattr(edge, 'tail', None):
            continue
        if edge.tail not in by_tail or (edge_time_millis(edge) or 0) > (edge_time_millis(by_tail[edge.tail]) or 0):
            by_tail[edge.tail] = edge
    return by_tail


def reviewer_due_date_edge_millis(edge):
    return _int_or_none(getattr(edge, 'weight', None))


def reviewer_assignment_due_date_millis(journal, submission, edge, reviewer_due_date=None):
    stored_due_date = _int_or_none(reviewer_due_date)
    if stored_due_date is not None:
        return stored_due_date
    assigned_at = _int_or_none(edge_time_millis(edge))
    if not assigned_at:
        return None
    weeks = journal.get_review_period_length(submission)
    return assigned_at + int(weeks * 7 * 24 * 60 * 60 * 1000)


def effective_review_due_date_millis(journal, submission, edge, reviewer_due_date=None):
    return reviewer_assignment_due_date_millis(journal, submission, edge, reviewer_due_date)


def effective_review_due_date_for_edge(client, journal, submission, edge, due_date_edges_by_tail=None):
    due_date_edges_by_tail = due_date_edges_by_tail or active_reviewer_due_date_edges_by_tail(client, journal, submission)
    reviewer_due_date = reviewer_due_date_edge_millis(due_date_edges_by_tail.get(edge.tail))
    return effective_review_due_date_millis(
        journal,
        submission,
        edge,
        reviewer_due_date
    )


def effective_review_due_date_for_reviewer(client, journal, submission, reviewer_profile_id, fallback_due_date=None):
    if reviewer_profile_id:
        due_date_edges_by_tail = active_reviewer_due_date_edges_by_tail(client, journal, submission)
        for edge in active_reviewer_assignment_edges(client, journal, submission):
            if edge.tail == reviewer_profile_id:
                return effective_review_due_date_for_edge(
                    client,
                    journal,
                    submission,
                    edge,
                    due_date_edges_by_tail
                )
    return fallback_due_date


def reviewer_signature_members(client, journal, submission):
    members_by_signature = {}
    signatures_by_member = {}
    try:
        groups = client.get_groups(prefix=f'{journal.venue_id}/Paper{submission.number}/Reviewer_')
    except Exception as error:
        print(f'Could not load reviewer signatures for Paper{submission.number}: {error}')
        return members_by_signature, signatures_by_member
    for group in groups:
        for member in getattr(group, 'members', None) or []:
            members_by_signature[group.id] = member
            signatures_by_member[member] = group.id
    return members_by_signature, signatures_by_member


def submitted_reviewer_members(client, journal, submission, review_invitation_id):
    members_by_signature, _signatures_by_member = reviewer_signature_members(client, journal, submission)
    submitted = set()
    try:
        reviews = client.get_notes(forum=submission.id, invitation=review_invitation_id)
    except Exception as error:
        print(f'Could not load reviews for Paper{submission.number}: {error}')
        return submitted
    for review in reviews:
        if getattr(review, 'ddate', None):
            continue
        for signature in getattr(review, 'signatures', None) or []:
            submitted.add(members_by_signature.get(signature, signature))
    return submitted


def review_reminder_dates_for_assignments(client, journal, submission):
    dates = set()
    due_date_edges_by_tail = active_reviewer_due_date_edges_by_tail(client, journal, submission)
    for edge in active_reviewer_assignment_edges(client, journal, submission):
        effective_due = effective_review_due_date_for_edge(
            client,
            journal,
            submission,
            edge,
            due_date_edges_by_tail
        )
        if not effective_due:
            continue
        for offset in REVIEW_REMINDER_OFFSETS_MILLIS:
            dates.add(effective_due + offset)
    return sorted(dates)


def update_review_invitation_due_date_and_reminders(client, journal, submission, review_invitation):
    active_edges = active_reviewer_assignment_edges(client, journal, submission)
    due_date_edges_by_tail = active_reviewer_due_date_edges_by_tail(client, journal, submission)
    effective_due_dates = [
        due_date for due_date in [
            effective_review_due_date_for_edge(
                client,
                journal,
                submission,
                edge,
                due_date_edges_by_tail
            )
            for edge in active_edges
        ]
        if due_date
    ]
    if effective_due_dates:
        review_invitation.duedate = max(effective_due_dates)
    else:
        review_invitation.duedate = {'delete': True}
    reminder_dates = review_reminder_dates_for_assignments(
        client,
        journal,
        submission
    )
    if reminder_dates and REVIEW_REMINDER_SCRIPT:
        review_invitation.date_processes = [
            {
                'dates': reminder_dates,
                'script': REVIEW_REMINDER_SCRIPT
            }
        ]
    elif hasattr(review_invitation, 'date_processes'):
        review_invitation.date_processes = {'delete': True}
    return review_invitation


def scheduled_review_reminder_date(invitation, date_index):
    date_processes = (
        getattr(invitation, 'date_processes', None)
        or getattr(invitation, 'dateprocesses', None)
        or []
    )
    if not date_processes:
        return None
    dates = date_processes[0].get('dates') or []
    try:
        return _int_or_none(dates[date_index])
    except Exception:
        return None


def reminder_offset_label(offset):
    if offset == DAY_MILLIS:
        return '1'
    if offset == WEEK_MILLIS:
        return 'one week'
    if offset % WEEK_MILLIS == 0:
        weeks = offset // WEEK_MILLIS
        if weeks == 2:
            return 'two weeks'
        if weeks == 4:
            return 'four weeks'
        return f'{weeks} weeks'
    if offset == 1209600000:
        return 'two weeks'
    if offset == 2592000000:
        return 'one month'
    return None


def late_reviewer_reminder_rows(client, journal, submission, invitation, date_index, now_millis=None):
    now_millis = now_millis or openreview.tools.datetime_millis(datetime.datetime.now())
    scheduled_date = scheduled_review_reminder_date(invitation, date_index)
    review_invitation_id = journal.get_review_id(number=submission.number)
    submitted = submitted_reviewer_members(client, journal, submission, review_invitation_id)
    due_date_edges_by_tail = active_reviewer_due_date_edges_by_tail(client, journal, submission)
    rows = []
    for edge in active_reviewer_assignment_edges(client, journal, submission):
        if edge.tail in submitted:
            continue
        effective_due = effective_review_due_date_for_edge(
            client,
            journal,
            submission,
            edge,
            due_date_edges_by_tail
        )
        if not effective_due:
            continue
        matched_offset = None
        for offset in REVIEW_REMINDER_OFFSETS_MILLIS:
            reminder_date = effective_due + offset
            if scheduled_date is not None:
                if reminder_date == scheduled_date:
                    matched_offset = offset
                    break
            elif now_millis >= reminder_date:
                matched_offset = offset
        if matched_offset is None:
            continue
        days_late = reminder_offset_label(matched_offset)
        if days_late is None:
            days_late = abs((now_millis - effective_due) // 86400000)
        rows.append({
            'reviewer': edge.tail,
            'effective_due_date': effective_due,
            'reminder_offset': matched_offset,
            'days_late': days_late
        })
    return rows
