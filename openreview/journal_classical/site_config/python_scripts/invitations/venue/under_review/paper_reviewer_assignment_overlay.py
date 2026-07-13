def setup_paper_reviewer_assignment_overlay(
    client,
    journal,
    note,
    active_action_editor_tail=None,
    wait_for_hub_refresh=True,
    require_hub_refresh=True,
):
    import datetime
    import html
    import json
    import re
    import time

    def reviewer_assignment_hub_ready():
        readiness = {
            "assignment_invitation_web": False,
            "paper_reviewers_group_web": False,
        }
        try:
            reviewer_assignment_invitation = client.get_invitation(
                journal.get_reviewer_assignment_id(number=note.number)
            )
            readiness["assignment_invitation_web"] = (
                "var AUTO_ASSIGN_CONFIG = " in (reviewer_assignment_invitation.web or "")
            )
        except Exception as error:
            print(f"Could not load reviewer assignment invitation for Paper{note.number}: {error}")
        try:
            paper_reviewers_group = client.get_group(journal.get_reviewers_id(number=note.number))
            readiness["paper_reviewers_group_web"] = (
                "var AUTO_ASSIGN_CONFIG = " in (paper_reviewers_group.web or "")
            )
        except Exception as error:
            print(f"Could not load paper reviewers group for Paper{note.number}: {error}")
        return readiness

    def ensure_reviewer_assignment_hub_ready():
        if not require_hub_refresh:
            return
        attempts = 80 if wait_for_hub_refresh else 1
        last_readiness = {}
        for attempt in range(attempts):
            last_readiness = reviewer_assignment_hub_ready()
            if all(last_readiness.values()):
                return
            if attempt + 1 < attempts:
                time.sleep(2)
        missing = [
            name for name, ready in sorted(last_readiness.items())
            if not ready
        ]
        raise openreview.OpenReviewException(
            "Assign Reviewers hub refresh did not produce the custom "
            f"reviewer hub for Paper{note.number}; missing: {', '.join(missing)}."
        )

    def refresh_reviewer_assignment_hub_from_initializer_chunks():
        venue_group = client.get_group(journal.venue_id)
        venue_content = getattr(venue_group, "content", {}) or {}
        hub_initializer_chunks = []
        missing_hub_initializer_chunks = []
        for chunk_index in range(1, 9):
            chunk_key = f"reviewer_assignment_hub_initializer_script_chunk_{chunk_index:02d}"
            chunk_value = venue_content.get(chunk_key, {}).get("value")
            if chunk_value is None:
                missing_hub_initializer_chunks.append(chunk_key)
            else:
                hub_initializer_chunks.append(chunk_value)
        if missing_hub_initializer_chunks:
            raise openreview.OpenReviewException(
                f"Reviewer assignment hub initializer script chunks are missing from {journal.venue_id}.content: "
                f"{', '.join(missing_hub_initializer_chunks)}."
            )
        hub_namespace = {"openreview": openreview}
        exec("".join(hub_initializer_chunks), hub_namespace)
        required_reviewers_namespace = {"openreview": openreview}
        exec("{{PYTHON_SCRIPT_JSON:invitations/venue/review/required_reviewers.py}}", required_reviewers_namespace)
        hub_namespace["refresh_reviewer_assignment_hub"](
            client,
            journal,
            note,
            reviewer_assignment_duedate,
            required_reviewers_namespace["get_required_reviewers"](client, journal, note),
            journal.get_reviewers_max_papers(),
            json,
            html,
            re,
        )

    def resolve_action_editor_signature(paper_action_editor_group):
        attempts = 6 if wait_for_hub_refresh else 1
        last_error = None
        for attempt in range(attempts):
            try:
                return reviewer_namespace["resolve_active_action_editor_signature"](
                    client,
                    journal,
                    note,
                    paper_action_editor_group,
                )
            except Exception as error:
                last_error = error
                if attempt + 1 < attempts:
                    time.sleep(1.5)
        raise last_error

    reviewer_namespace = {
        "openreview": openreview,
        "datetime": datetime,
    }
    for reviewer_script in [
        "{{PYTHON_SCRIPT_JSON:invitations/venue/under_review/reviewer_assignment_invitation_refresh.py}}",
        "{{PYTHON_SCRIPT_JSON:invitations/venue/under_review/reviewer_assignment_hub_refresh_trigger.py}}",
        "{{PYTHON_SCRIPT_JSON:invitations/venue/under_review/signature_helpers.py}}",
    ]:
        exec(reviewer_script, reviewer_namespace)

    reviewer_assignment_duedate = journal.get_due_date(weeks=journal.get_reviewer_assignment_period_length())
    try:
        journal.invitation_builder.set_reviewer_assignment_invitation(note, reviewer_assignment_duedate)
    except Exception as error:
        print(f"Could not set reviewer assignment invitation for Paper{note.number}: {error}")

    reviewer_namespace["refresh_reviewer_assignment_invitation"](
        client,
        journal,
        note,
        reviewer_assignment_duedate,
    )
    reviewer_namespace["trigger_reviewer_assignment_hub_refresh"](
        client,
        journal,
        note,
        await_process=False,
        raise_on_error=require_hub_refresh,
    )
    try:
        ensure_reviewer_assignment_hub_ready()
    except Exception:
        if not wait_for_hub_refresh:
            raise
        refresh_reviewer_assignment_hub_from_initializer_chunks()
        ensure_reviewer_assignment_hub_ready()

    paper_authors_id = journal.get_authors_id(number=note.number)
    paper_authorids = [
        authorid for authorid in note.content.get("authorids", {}).get("value", [])
        if isinstance(authorid, str) and authorid
    ]
    author_nonreaders = [paper_authors_id] + paper_authorids
    paper_action_editor_group = client.get_group(id=journal.get_action_editors_id(number=note.number))
    if active_action_editor_tail:
        paper_action_editor_group.members = [active_action_editor_tail]
        print(
            f"Using checked Action Editor assignment edge tail for Paper{note.number} "
            "while paper Action Editors group membership catches up."
        )
    elif not paper_action_editor_group.members:
        try:
            active_action_editor_tails = [
                assignment.tail
                for assignment in client.get_edges(
                    invitation=f"{journal.venue_id}/Paper{note.number}/Action_Editors/-/Assignment",
                    head=note.id,
                )
                if getattr(assignment, "tail", None) and not getattr(assignment, "ddate", None)
            ]
            if active_action_editor_tails:
                paper_action_editor_group.members = active_action_editor_tails
                print(
                    f"Using active Action Editor assignment edge for Paper{note.number} "
                    "while paper Action Editors group membership catches up."
                )
        except Exception as error:
            print(f"Could not load active Action Editor assignment for Paper{note.number}: {error}")
    if not paper_action_editor_group.members:
        print(
            f"Skipping reviewer assignment hub setup for Paper{note.number}: "
            "no active Action Editor is assigned yet."
        )
