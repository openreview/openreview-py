PREVIOUS_AE_CONFLICT_OVERRIDE_LABEL = "Previous AE Conflict Override"


def active_ae_for_paper(client, journal, note):
    assignment_id = f"{journal.venue_id}/Paper{note.number}/Action_Editors/-/Assignment"
    try:
        edges = client.get_edges(invitation=assignment_id, head=note.id, domain=journal.venue_id)
    except Exception:
        edges = []
    active = [edge for edge in edges or [] if not getattr(edge, "ddate", None)]
    return active[0].tail if active else None


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


def previous_forum_id_from_list(content_value, note):
    import re
    value = content_value(note, "previous_JMLR_submissions", "") or ""
    match = re.search(r"forum\?id=([A-Za-z0-9_-]+)", str(value))
    return match.group(1) if match else None


def previous_forum_id(client, journal, content_value, note):
    previous_submission_url = content_value(note, "previous_JMLR_submission_URL", "")
    if previous_submission_url and previous_submission_url != "N/A":
        return parse_forum_id(previous_submission_url)
    previous_submission_number = content_value(note, "previous_JMLR_submission_number", "")
    if previous_submission_number and str(previous_submission_number).strip().upper() != "N/A":
        try:
            previous_notes = client.get_notes(
                invitation=f"{journal.venue_id}/-/Submission",
                number=int(str(previous_submission_number).strip()),
            )
            return previous_notes[0].id if previous_notes else None
        except Exception:
            return None
    return previous_forum_id_from_list(content_value, note)


def previous_ae_assignment(client, journal, previous_submission):
    previous_assignment_invitation_ids = [
        f"{journal.venue_id}/Paper{previous_submission.number}/Action_Editors/-/Assignment",
        journal.get_ae_assignment_id(),
        journal.get_ae_assignment_id(archived=True),
    ]
    for assignment_invitation_id in previous_assignment_invitation_ids:
        try:
            edges = client.get_edges(
                invitation=assignment_invitation_id,
                head=previous_submission.id,
                domain=journal.venue_id,
            )
        except Exception:
            edges = []
        active = [edge for edge in edges or [] if getattr(edge, "tail", None) and not getattr(edge, "ddate", None)]
        if active:
            return active[0]
    return None


def post_previous_ae_continuity_assignment(client, journal, note, previous_ae):
    return client.post_edge(openreview.api.Edge(
        invitation=f"{journal.venue_id}/Paper{note.number}/Action_Editors/-/Assignment",
        signatures=[journal.get_editors_in_chief_id()],
        head=note.id,
        tail=previous_ae,
        weight=1,
        label=PREVIOUS_AE_CONFLICT_OVERRIDE_LABEL,
    ))


def auto_assign_previous_ae_after_setup(client, journal, content_value, classify_assignment_setup_state, note):
    if content_value(note, "venueid", "") != f"{journal.venue_id}/Submitted":
        return {"status": "skipped", "reason": "paper_not_submitted_no_ae"}
    if active_ae_for_paper(client, journal, note):
        return {"status": "skipped", "reason": "active_ae_exists"}
    setup_state = classify_assignment_setup_state(client, journal, note)
    if setup_state.get("status") != "complete":
        return {"status": "skipped", "reason": "setup_not_complete", "setup_state": setup_state.get("status")}
    previous_id = previous_forum_id(client, journal, content_value, note)
    if not previous_id:
        return {"status": "skipped", "reason": "previous_submission_not_resolved"}
    try:
        previous_submission = client.get_note(previous_id)
    except Exception as error:
        return {"status": "skipped", "reason": "previous_submission_load_failed", "error": str(error)}
    previous_assignment = previous_ae_assignment(client, journal, previous_submission)
    previous_ae = getattr(previous_assignment, "tail", None)
    if not previous_ae:
        return {"status": "skipped", "reason": "previous_ae_not_found"}
    try:
        edge = post_previous_ae_continuity_assignment(client, journal, note, previous_ae)
        return {"status": "assigned", "previous_ae": previous_ae, "edge_id": getattr(edge, "id", None)}
    except Exception as error:
        return {"status": "failed", "reason": "checked_assignment_rejected", "previous_ae": previous_ae, "error": str(error)}
