def process(client, edge, invitation):

    journal = openreview.journal.JournalRequest.get_journal(client, "{{PROD_JOURNAL_ID}}")
    assignment_conflict_namespace = {}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/assignment_conflicts.py}}", assignment_conflict_namespace)
    cooldown_days = {{ACTION_EDITOR_NEW_ASSIGNMENT_COOLDOWN_DAYS}}
    action_editors_max_papers = {{ACTION_EDITORS_MAX_PAPERS}}
    oss_action_editors_enabled = "{{OSS_ACTION_EDITORS_ENABLED_JSON}}" == "true"
    oss_action_editors_id = "{{OSS_ACTION_EDITOR_GROUP_ID}}"
    oss_action_editors_max_papers = {{OSS_ACTION_EDITORS_MAX_PAPERS}}

    submission = client.get_note(edge.head)
    ae_assignment_id = getattr(invitation, "id", None)

    def get_current_paper_assignment_edges(**kwargs):
        return client.get_edges(invitation=ae_assignment_id, **kwargs)

    def is_action_editor_assignment_edge(assignment_edge):
        assignment_invitation = getattr(assignment_edge, "invitation", "") or ""
        return (
            assignment_invitation == ae_assignment_id or
            assignment_invitation == journal.get_ae_assignment_id(archived=True) or
            assignment_invitation.endswith("/Action_Editors/-/Assignment")
        )

    def get_action_editor_assignment_edges(**kwargs):
        try:
            assignment_edges = client.get_all_edges(domain=journal.venue_id, **kwargs)
        except Exception:
            assignment_edges = client.get_edges(domain=journal.venue_id, **kwargs)
        return [
            assignment_edge
            for assignment_edge in assignment_edges
            if is_action_editor_assignment_edge(assignment_edge)
        ]

    def group_has_member(group_id, member_id):
        try:
            return bool(client.get_groups(id=group_id, member=member_id))
        except Exception as error:
            if 'Group Not Found' in str(error) or 'NotFoundError' in str(error):
                return False
            raise

    def add_identity(identities, value):
        if value and isinstance(value, str) and value not in identities:
            identities.append(value)

    def add_profile_identities(identities, value):
        add_identity(identities, value)
        if not value or not isinstance(value, str):
            return
        if not value.startswith('~') and '@' not in value:
            return
        try:
            profiles = openreview.tools.get_profiles(client, [value])
            profile = profiles[0] if profiles else None
        except Exception:
            profile = None
        if not profile:
            return
        add_identity(identities, getattr(profile, 'id', None))
        try:
            add_identity(identities, profile.get_preferred_email())
        except Exception:
            pass
        profile_content = getattr(profile, 'content', {}) or {}
        add_identity(identities, profile_content.get('preferredEmail'))
        for email in profile_content.get('emails', []) or []:
            add_identity(identities, email)
        for email in profile_content.get('preferredEmails', []) or []:
            add_identity(identities, email)

    def actor_identities():
        identities = []
        add_profile_identities(identities, getattr(edge, 'tauthor', None))
        for edge_signature in getattr(edge, 'signatures', None) or []:
            add_profile_identities(identities, edge_signature)
        return identities

    def format_month(timestamp):
        month_start = datetime.datetime.fromtimestamp(timestamp / 1000, datetime.timezone.utc)
        return f'{month_start.strftime("%B")} {month_start.day}, {month_start.year}'

    def unavailable_message(role, profile_id, availability_edge, now):
        if availability_edge and availability_edge.weight and availability_edge.weight > now:
            return f'{role} {profile_id} is unavailable until {format_month(availability_edge.weight)}.'
        return f'{role} {profile_id} is unavailable indefinitely.'

    def is_available(availability_edge, now):
        if not availability_edge:
            return True
        if availability_edge.label != 'Unavailable':
            return True
        if availability_edge.weight and availability_edge.weight <= now:
            return True
        return False

    def is_oss_action_editor(profile_id):
        if not oss_action_editors_enabled:
            return False
        return group_has_member(oss_action_editors_id, profile_id)

    def is_oss_submission(note):
        if not oss_action_editors_enabled:
            return False
        return bool(note.content.get('open_source_software', {}).get('value'))

    def assignment_paper_has_decision(assignment):
        try:
            assigned_submission = client.get_note(assignment.head)
            decisions = client.get_notes(
                invitation=journal.get_ae_decision_id(number=assigned_submission.number),
                forum=assigned_submission.id
            )
            return any(not decision.ddate for decision in decisions)
        except Exception:
            return False

    authors_group_id = journal.get_authors_id(number=submission.number)
    authorids = submission.content.get('authorids', {}).get('value') or []
    actor_ids = actor_identities()
    if any(actor_id in authorids or group_has_member(authors_group_id, actor_id) for actor_id in actor_ids):
        raise openreview.OpenReviewException(f'Authors can not edit assignments for this submission: {submission.number}')

    for actor_id in actor_ids:
        if not (actor_id.startswith('~') or '@' in actor_id):
            continue
        try:
            hard_actor_conflict = assignment_conflict_namespace['get_assignment_conflict'](client, journal, submission, actor_id)
            if hard_actor_conflict:
                raise openreview.OpenReviewException(f'Conflicted users can not edit assignments for this submission: {submission.number}')
            openreview_actor_conflict = assignment_conflict_namespace['get_assignment_conflict'](client, journal, submission, actor_id, conflict_type='openreview')
            if openreview_actor_conflict:
                print(
                    f'OpenReview-computed actor conflict for {actor_id} on submission {submission.number} '
                    'is advisory for assignment operations.'
                )
        except openreview.OpenReviewException:
            raise
        except Exception:
            pass

    venue_id = submission.content.get('venueid', {}).get('value')
    if not journal.is_active_submission(submission):
        raise openreview.OpenReviewException(f'Can not edit assignments for this submission: {venue_id}')

    # Invitation availability is not lifecycle state; only an active Decision note is.
    # This blocks stale assignment forms even if the paper status or invitation cache lags.
    def decision_made():
        return any(
            not decision.ddate
            for decision in client.get_notes(invitation=journal.get_ae_decision_id(number=submission.number))
        )

    if edge.ddate:
        if decision_made():
            raise openreview.OpenReviewException(f'Can not remove assignment, the user {edge.tail} already posted a decision.')
        return
    if decision_made():
        raise openreview.OpenReviewException(f'Can not add assignment, a decision has already been posted for this submission: {submission.number}.')

    if not group_has_member(journal.get_action_editors_id(), edge.tail):
        raise openreview.OpenReviewException(f'Can not add assignment, previous action editor {edge.tail} is no longer a current member of {journal.get_action_editors_id()}.')

    oss_submission = is_oss_submission(submission)
    oss_action_editor = is_oss_action_editor(edge.tail)
    if oss_submission and not oss_action_editor:
        raise openreview.OpenReviewException('OSS submissions must be assigned to an OSS Action Editor.')
    if not oss_submission and oss_action_editor:
        raise openreview.OpenReviewException('Regular submissions must be assigned to a regular Action Editor, not an OSS Action Editor.')

    existing_assignments = get_current_paper_assignment_edges(
        head=edge.head,
        tail=edge.tail
    )
    if any(not assignment.ddate for assignment in existing_assignments):
        raise openreview.OpenReviewException(f'Action editor {edge.tail} is already assigned to this paper.')

    now = openreview.tools.datetime_millis(datetime.datetime.now())

    def get_previous_forum_id(note):
        def parse_forum_id(url):
            if not url or url == "N/A":
                return None
            try:
                from urllib.parse import parse_qs, urlparse
                parsed = urlparse(str(url))
                forum_ids = parse_qs(parsed.query).get("id")
                if forum_ids and forum_ids[0]:
                    return forum_ids[0]
            except Exception:
                pass
            try:
                return str(url).split("forum?id=", 1)[1].split("&", 1)[0]
            except Exception:
                return None

        def previous_forum_id_from_list(note):
            import re
            value = note.content.get("previous_JMLR_submissions", {}).get("value") or ""
            match = re.search(r"forum\?id=([A-Za-z0-9_-]+)", str(value))
            return match.group(1) if match else None

        previous_submission_url = note.content.get("previous_JMLR_submission_URL", {}).get("value")
        if not previous_submission_url or previous_submission_url == "N/A":
            previous_submission_number = note.content.get("previous_JMLR_submission_number", {}).get("value")
            if not previous_submission_number or str(previous_submission_number).strip().upper() == "N/A":
                return previous_forum_id_from_list(note)
            try:
                previous_notes = client.get_notes(
                    invitation=f"{journal.venue_id}/-/Submission",
                    number=int(str(previous_submission_number).strip())
                )
                return previous_notes[0].id if previous_notes else None
            except Exception:
                return None
        return parse_forum_id(previous_submission_url)

    def is_resubmission_reassignment(note, action_editor_id):
        previous_forum_id = get_previous_forum_id(note)
        if not previous_forum_id:
            return False
        previous_paper_assignment_id = None
        try:
            previous_submission = client.get_note(previous_forum_id)
            previous_paper_assignment_id = f'{journal.venue_id}/Paper{previous_submission.number}/Action_Editors/-/Assignment'
        except Exception:
            pass
        previous_assignments = []
        if previous_paper_assignment_id:
            previous_assignments += client.get_edges(
                invitation=previous_paper_assignment_id,
                head=previous_forum_id,
                tail=action_editor_id
            )
        previous_assignments += get_action_editor_assignment_edges(
            head=previous_forum_id,
            tail=action_editor_id
        )
        previous_assignments += client.get_edges(
            invitation=journal.get_ae_assignment_id(archived=True),
            head=previous_forum_id,
            tail=action_editor_id
        )
        return bool(previous_assignments)

    hard_conflict = assignment_conflict_namespace['get_assignment_conflict'](client, journal, submission, edge.tail)
    if hard_conflict:
        raise openreview.OpenReviewException(f'Can not add assignment, {edge.tail} appears in the submission {hard_conflict["reason"]}.')

    resubmission_reassignment = is_resubmission_reassignment(submission, edge.tail)
    conflict_override_label = 'Previous AE Conflict Override'
    eic_openreview_conflict_override_label = 'EIC OpenReview Conflict Override'
    eic_legacy_conflict_override_label = 'EIC Conflict Override'
    openreview_conflict = assignment_conflict_namespace['get_assignment_conflict'](client, journal, submission, edge.tail, conflict_type='openreview')
    if resubmission_reassignment:
        if openreview_conflict and edge.label != conflict_override_label:
            raise openreview.OpenReviewException(f'Can not add assignment, conflict detected for {edge.tail}.')
        return

    if openreview_conflict and edge.label not in [eic_openreview_conflict_override_label, eic_legacy_conflict_override_label]:
       raise openreview.OpenReviewException(f'Can not add assignment, conflict detected for {edge.tail}.')

    edges = client.get_edges(invitation=journal.get_ae_availability_id(), tail=edge.tail)
    availability_edge = edges[0] if edges else None
    if not is_available(availability_edge, now):
       raise openreview.OpenReviewException(unavailable_message('Action Editor', edge.tail, availability_edge, now))

    active_assignments = get_action_editor_assignment_edges(
        tail=edge.tail
    )
    active_load = 0
    for assignment in active_assignments:
        if assignment.ddate or assignment.head == edge.head:
            continue
        if assignment_paper_has_decision(assignment):
            continue
        active_load += 1

    max_papers = action_editors_max_papers
    role_label = 'Action Editor'
    if oss_submission:
        max_papers = oss_action_editors_max_papers
        role_label = 'OSS Action Editor'
    else:
        custom_max_edges = client.get_edges(
            invitation=journal.get_action_editors_id() + '/-/Custom_Max_Papers',
            head=journal.get_action_editors_id(),
            tail=edge.tail
        )
        if custom_max_edges:
            max_papers = custom_max_edges[0].weight

    if active_load >= max_papers:
        raise openreview.OpenReviewException(
            f'{role_label} {edge.tail} already has {active_load} active paper(s), '
            f'which reaches the {role_label} max load of {max_papers}.'
        )

    cooldown_millis = cooldown_days * 24 * 60 * 60 * 1000
    min_assignment_date = now - cooldown_millis
    recent_assignment_edges = get_action_editor_assignment_edges(
        tail=edge.tail
    )

    for recent_assignment in recent_assignment_edges:
        if recent_assignment.ddate:
            continue
        if recent_assignment.head == edge.head:
            continue
        if not recent_assignment.cdate or recent_assignment.cdate < min_assignment_date:
            continue

        recent_submission = client.get_note(recent_assignment.head)
        if is_resubmission_reassignment(recent_submission, edge.tail):
            continue

        recent_assignment_date = datetime.datetime.fromtimestamp(recent_assignment.cdate / 1000).strftime("%Y-%m-%d")
        next_assignment_date = datetime.datetime.fromtimestamp((recent_assignment.cdate + cooldown_millis) / 1000).strftime("%Y-%m-%d")
        raise openreview.OpenReviewException(
            f'Action editor {edge.tail} was assigned new paper {recent_submission.number} on {recent_assignment_date}. '
            f'Please wait until {next_assignment_date} before assigning another new paper. '
            'Resubmission reassignment to the previous action editor is allowed and does not count toward this limit.'
        )
