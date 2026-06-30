def process(client, edit, invitation):
    journal = openreview.journal.JournalRequest.get_journal(client, "{{PROD_JOURNAL_ID}}")
    datetime = __import__("datetime")
    oss_action_editors_enabled = "{{OSS_ACTION_EDITORS_ENABLED_JSON}}" == "true"
    setup_state_namespace = {"openreview": openreview}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/setup_assignments/setup_state.py}}", setup_state_namespace)
    SETUP_STATUS_IN_PROGRESS = setup_state_namespace["SETUP_STATUS_IN_PROGRESS"]
    SETUP_STATUS_READY = setup_state_namespace["SETUP_STATUS_READY"]
    SETUP_STATUS_FAILED = setup_state_namespace["SETUP_STATUS_FAILED"]
    classify_assignment_setup_state = setup_state_namespace["classify_assignment_setup_state"]
    content_value = setup_state_namespace["content_value"]

    def now_millis():
        return openreview.tools.datetime_millis(datetime.datetime.now())

    def setup_note_content(submission_note, status, extra_content=None):
        content = {
            "note_id": {"value": submission_note.id},
            "paper_number": {"value": submission_note.number},
            "setup_readiness_status": {"value": status},
        }
        if extra_content:
            for key, value in extra_content.items():
                content[key] = {"value": value}
        return content

    def post_setup_status(submission_note, status, extra_content=None):
        client.post_note_edit(
            invitation=journal.get_meta_invitation_id(),
            signatures=[journal.venue_id],
            note=openreview.api.Note(
                id=trigger_note.id,
                signatures=[journal.get_editors_in_chief_id()],
                readers=[journal.get_editors_in_chief_id()],
                writers=[journal.get_editors_in_chief_id()],
                content=setup_note_content(submission_note, status, extra_content),
            ),
        )

    trigger_note = client.get_note(edit.note.id)
    note_id = trigger_note.content.get("note_id", {}).get("value")
    if not note_id:
        raise openreview.OpenReviewException("Assignment setup requires note_id.")

    note = client.get_note(note_id)
    expected_number = trigger_note.content.get("paper_number", {}).get("value")
    if expected_number and int(expected_number) != int(note.number):
        raise openreview.OpenReviewException("Assignment setup paper_number does not match note_id.")

    current_now_ms = now_millis()
    setup_state = classify_assignment_setup_state(client, journal, note, current_now_ms)
    if setup_state.get("complete"):
        print(f"Assignment setup already complete for Paper{note.number}; no setup work needed.")
        return
    if setup_state.get("status") == "in_progress":
        raise openreview.OpenReviewException(
            f"Assignment setup is already in progress for Paper{note.number} "
            f"on setup note {setup_state.get('in_progress_note_id')}; retry after one hour or after it completes."
        )
    if setup_state.get("status") == "stale_in_progress":
        print(
            f"Stale assignment setup in-progress note {setup_state.get('in_progress_note_id')} for Paper{note.number} "
            f"started at {setup_state.get('in_progress_started_at')} was superseded by setup note {trigger_note.id}."
        )

    def add_identity(identities, value):
        if value and isinstance(value, str) and value not in identities:
            identities.append(value)

    def add_profile_identities(identities, value):
        add_identity(identities, value)
        if not value or not isinstance(value, str):
            return
        if not value.startswith("~") and "@" not in value:
            return
        try:
            profiles = openreview.tools.get_profiles(client, [value])
            profile = profiles[0] if profiles else None
        except Exception:
            profile = None
        if not profile:
            return
        add_identity(identities, getattr(profile, "id", None))
        try:
            add_identity(identities, profile.get_preferred_email())
        except Exception:
            pass
        profile_content = getattr(profile, "content", {}) or {}
        add_identity(identities, profile_content.get("preferredEmail"))
        for email in profile_content.get("emails", []) or []:
            add_identity(identities, email)
        for email in profile_content.get("preferredEmails", []) or []:
            add_identity(identities, email)

    def actor_identities():
        identities = []
        edit_signatures = getattr(edit, "signatures", None) or []
        note_signatures = getattr(edit.note, "signatures", None) or []
        if journal.venue_id in edit_signatures or journal.venue_id in note_signatures:
            add_identity(identities, journal.venue_id)
            return identities
        add_profile_identities(identities, getattr(edit, "tauthor", None))
        for edit_signature in edit_signatures:
            add_profile_identities(identities, edit_signature)
        for note_signature in note_signatures:
            add_profile_identities(identities, note_signature)
        return identities

    def group_has_member(group_id, member_id):
        try:
            return bool(client.get_groups(id=group_id, member=member_id))
        except Exception as error:
            if "Group Not Found" in str(error) or "NotFoundError" in str(error):
                return False
            raise

    authors_group_id = journal.get_authors_id(number=note.number)
    authorids = note.content.get("authorids", {}).get("value") or []
    for actor_id in actor_identities():
        if actor_id in authorids or group_has_member(authors_group_id, actor_id):
            raise openreview.OpenReviewException(f"Authors can not set up Action Editor assignment for this submission: {note.number}")

    setup_started_at = now_millis()
    setup_actor = getattr(edit, "tauthor", None) or ",".join((getattr(edit, "signatures", None) or getattr(edit.note, "signatures", None) or []))
    setup_operation_key = f"{note.id}:{trigger_note.id}:{setup_started_at}"
    setup_in_progress_content = {
        "setup_started_at": setup_started_at,
        "setup_actor": setup_actor or journal.venue_id,
        "setup_operation_key": setup_operation_key,
    }
    if setup_state.get("status") == "stale_in_progress":
        setup_in_progress_content.update({
            "setup_superseded_note_id": setup_state.get("in_progress_note_id"),
            "setup_superseded_started_at": setup_state.get("in_progress_started_at"),
        })
    post_setup_status(
        note,
        SETUP_STATUS_IN_PROGRESS,
        setup_in_progress_content,
    )

    def is_oss_submission(submission_note):
        if not oss_action_editors_enabled:
            return False
        try:
            return submission_note.content.get("open_source_software", {}).get("value") is True
        except Exception:
            return False

    def active_track_compatible_action_editors():
        try:
            action_editors = set(client.get_group(journal.get_action_editors_id()).members or [])
        except Exception as error:
            print(f"Could not load action editors for Paper{note.number}: {error}")
            return []
        try:
            archived_action_editors = set(client.get_group(journal.get_action_editors_id(archived=True)).members or [])
        except Exception:
            archived_action_editors = set()
        candidates = [
            tail for tail in action_editors
            if tail and tail.startswith("~") and tail not in archived_action_editors
        ]
        if not oss_action_editors_enabled:
            return candidates
        try:
            oss_action_editors = set(client.get_group(journal.get_oss_action_editors_id()).members or [])
        except Exception:
            oss_action_editors = set()
        if is_oss_submission(note):
            return [tail for tail in candidates if tail in oss_action_editors]
        return [tail for tail in candidates if tail not in oss_action_editors]

    def active_reviewers():
        try:
            reviewers = set(client.get_group(journal.get_reviewers_id()).members or [])
        except Exception as error:
            print(f"Could not load reviewers for Paper{note.number}: {error}")
            return []
        indefinitely_unavailable = set()
        try:
            availability_edges = client.get_all_edges(invitation=journal.get_reviewer_availability_id())
        except Exception:
            try:
                availability_edges = client.get_edges(invitation=journal.get_reviewer_availability_id())
            except Exception as error:
                print(f"Could not load reviewer availability for Paper{note.number}: {error}")
                availability_edges = []
        for availability_edge in availability_edges or []:
            if (
                getattr(availability_edge, "tail", None)
                and not getattr(availability_edge, "ddate", None)
                and getattr(availability_edge, "label", None) == "Unavailable"
                and not getattr(availability_edge, "weight", None)
            ):
                indefinitely_unavailable.add(availability_edge.tail)
        return [
            tail for tail in reviewers
            if tail and tail.startswith("~") and tail not in indefinitely_unavailable
        ]

    try:
        assignment_conflict_namespace = {"openreview": openreview}
        exec("{{PYTHON_SCRIPT_JSON:invitations/venue/assignment_conflicts.py}}", assignment_conflict_namespace)
        assignment_conflict_materialization_namespace = {"openreview": openreview}
        exec(
            "{{PYTHON_SCRIPT_JSON:invitations/venue/assignment_conflict_materialization.py}}",
            assignment_conflict_materialization_namespace,
        )
        overlay_namespace = {"openreview": openreview}
        exec(
            "{{PYTHON_SCRIPT_JSON:invitations/venue/submission/paper_action_editor_assignment_overlay.py}}",
            overlay_namespace,
        )
        reviewer_overlay_namespace = {"openreview": openreview}
        exec(
            "{{PYTHON_SCRIPT_JSON:invitations/venue/under_review/paper_reviewer_assignment_overlay.py}}",
            reviewer_overlay_namespace,
        )
        materialize_openreview_conflicts = assignment_conflict_materialization_namespace["materialize_openreview_conflicts"]

        materialize_openreview_conflicts(
            client,
            journal,
            note,
            f"{journal.venue_id}/Action_Editors/-/Conflict",
            active_track_compatible_action_editors(),
            "AE",
            assignment_conflict_namespace,
        )
        materialize_openreview_conflicts(
            client,
            journal,
            note,
            f"{journal.venue_id}/Reviewers/-/Conflict",
            active_reviewers(),
            "reviewer",
            assignment_conflict_namespace,
        )

        assignment_invitation_existed = overlay_namespace["setup_paper_action_editor_assignment_overlay"](client, journal, note)
        reviewer_overlay_namespace["setup_paper_reviewer_assignment_overlay"](
            client,
            journal,
            note,
            wait_for_hub_refresh=False,
            require_hub_refresh=False,
        )
        overlay_namespace["ensure_action_editor_affinity_on_first_assignment_page_create"](
            client,
            journal,
            note,
            assignment_invitation_existed,
        )
        launcher_invitation_id = overlay_namespace["setup_paper_action_editor_forum_launcher"](client, journal, note)

        readiness_recorded_at = now_millis()
        post_setup_status(
            note,
            SETUP_STATUS_READY,
            {"setup_readiness_recorded_at": readiness_recorded_at},
        )
    except Exception as error:
        try:
            post_setup_status(
                note,
                SETUP_STATUS_FAILED,
                {
                    "setup_failed_at": now_millis(),
                    "setup_error": str(error)[:500],
                },
            )
        except Exception as status_error:
            print(f"Could not mark assignment setup failed for Paper{note.number}: {status_error}")
        raise
    print(
        f"Assignment setup completed for Paper{note.number}; "
        f"created {launcher_invitation_id}; "
        f"recorded EIC-only readiness 'Assignment pages created' on setup note {trigger_note.id}."
    )
