SETUP_STATUS_IN_PROGRESS = "Setup in progress"
SETUP_STATUS_READY = "Assignment pages created"
SETUP_STATUS_FAILED = "Setup failed"
SETUP_IN_PROGRESS_TTL_MS = 60 * 60 * 1000


def _now_millis():
    try:
        datetime = __import__("datetime")
        return openreview.tools.datetime_millis(datetime.datetime.now())
    except Exception:
        time = __import__("time")
        return int(time.time() * 1000)


def content_value(obj, field, default=None):
    try:
        content = getattr(obj, "content", {}) or {}
        value = content.get(field, default)
        if isinstance(value, dict) and "value" in value:
            return value.get("value", default)
        return value
    except Exception:
        return default


def assignment_setup_invitation_ids(journal, note):
    venue_id = journal.venue_id
    return [
        f"{venue_id}/Paper{note.number}/Action_Editors/-/Assignment",
        f"{venue_id}/Paper{note.number}/Reviewers/-/Assignment",
        f"{venue_id}/Paper{note.number}/-/Assign_Action_Editor",
    ]


def active_invitation(client, invitation_id, now_ms):
    try:
        candidate_invitation = client.get_invitation(invitation_id)
    except Exception:
        return False
    if getattr(candidate_invitation, "ddate", None):
        return False
    expdate = getattr(candidate_invitation, "expdate", None)
    if expdate and int(expdate) <= int(now_ms):
        return False
    return True


def _note_matches_paper(candidate_note, submission_note):
    candidate_note_id = content_value(candidate_note, "note_id")
    candidate_paper_number = content_value(candidate_note, "paper_number")
    if candidate_note_id and str(candidate_note_id) == str(submission_note.id):
        return True
    if candidate_paper_number:
        try:
            return int(candidate_paper_number) == int(submission_note.number)
        except Exception:
            return False
    return False


def setup_notes_for_paper(client, journal, note):
    try:
        setup_notes = client.get_notes(invitation=f"{journal.venue_id}/-/Setup_Assignments", sort="tcdate:desc") or []
    except TypeError:
        try:
            setup_notes = client.get_notes(invitation=f"{journal.venue_id}/-/Setup_Assignments") or []
        except Exception as error:
            print(f"Could not load setup notes for Paper{note.number}: {error}")
            return []
    except Exception as error:
        print(f"Could not load setup notes for Paper{note.number}: {error}")
        return []
    return [
        setup_note for setup_note in setup_notes
        if not getattr(setup_note, "ddate", None) and _note_matches_paper(setup_note, note)
    ]


def _note_timestamp(note):
    for field in ("tcdate", "cdate", "mdate"):
        value = getattr(note, field, None)
        if value:
            try:
                return int(value)
            except Exception:
                pass
    return 0


def _latest_status_note(setup_notes, status):
    latest_note = None
    latest_stamp = None
    for setup_note in setup_notes:
        if content_value(setup_note, "setup_readiness_status") != status:
            continue
        stamp = _note_timestamp(setup_note)
        if latest_stamp is None or stamp >= latest_stamp:
            latest_note = setup_note
            latest_stamp = stamp
    return latest_note


def _latest_in_progress_setup_note(setup_notes):
    latest_note = None
    latest_started_at = None
    for setup_note in setup_notes:
        if content_value(setup_note, "setup_readiness_status") != SETUP_STATUS_IN_PROGRESS:
            continue
        started_at = content_value(setup_note, "setup_started_at")
        if not started_at:
            continue
        try:
            started_at = int(started_at)
        except Exception:
            continue
        if latest_started_at is None or started_at > latest_started_at:
            latest_note = setup_note
            latest_started_at = started_at
    return latest_note, latest_started_at


def classify_assignment_setup_state(client, journal, note, now_ms=None):
    if now_ms is None:
        now_ms = _now_millis()
    setup_notes = setup_notes_for_paper(client, journal, note)
    invitation_ids = assignment_setup_invitation_ids(journal, note)
    missing_invitations = [
        invitation_id for invitation_id in invitation_ids
        if not active_invitation(client, invitation_id, now_ms)
    ]
    ready_note = _latest_status_note(setup_notes, SETUP_STATUS_READY)
    failed_note = _latest_status_note(setup_notes, SETUP_STATUS_FAILED)
    in_progress_note, in_progress_started_at = _latest_in_progress_setup_note(setup_notes)
    state = {
        "status": "needed",
        "complete": False,
        "missing_invitations": missing_invitations,
    }
    if ready_note:
        state["ready_note_id"] = getattr(ready_note, "id", None)
    if failed_note:
        state["failed_note_id"] = getattr(failed_note, "id", None)
    if in_progress_note:
        age_ms = int(now_ms) - int(in_progress_started_at)
        state.update({
            "in_progress_note_id": getattr(in_progress_note, "id", None),
            "in_progress_started_at": in_progress_started_at,
            "age_ms": age_ms,
        })

    if ready_note and not missing_invitations:
        state["status"] = "complete"
        state["complete"] = True
    elif in_progress_note and state.get("age_ms", SETUP_IN_PROGRESS_TTL_MS) < SETUP_IN_PROGRESS_TTL_MS:
        state["status"] = "in_progress"
    elif in_progress_note:
        state["status"] = "stale_in_progress"
    elif failed_note:
        state["status"] = "failed"
    else:
        state["status"] = "needed"
    return state
