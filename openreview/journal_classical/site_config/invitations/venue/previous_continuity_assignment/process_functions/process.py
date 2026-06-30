def process(client, edit, invitation):
    TIMEOUT_SECONDS = 60 * 60
    journal = openreview.journal.JournalRequest.get_journal(client, "{{PROD_JOURNAL_ID}}")
    venue_id = journal.venue_id
    setup_state_namespace = {"openreview": openreview}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/setup_assignments/setup_state.py}}", setup_state_namespace)
    continuity_namespace = {"openreview": openreview}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/setup_assignments/previous_ae_continuity.py}}", continuity_namespace)
    content_value = setup_state_namespace["content_value"]
    datetime = __import__("datetime")

    def now_millis():
        return openreview.tools.datetime_millis(datetime.datetime.now())

    def note_content_value(note, field, default=""):
        return content_value(note, field, default)

    def edit_signatures():
        signatures = []
        signatures.extend(getattr(edit, "signatures", None) or [])
        signatures.extend(getattr(edit.note, "signatures", None) or [])
        try:
            trigger = client.get_note(edit.note.id)
            signatures.extend(getattr(trigger, "signatures", None) or [])
        except Exception:
            pass
        return [signature for signature in signatures if isinstance(signature, str)]

    def require_allowed_actor():
        signatures = edit_signatures()
        if venue_id in signatures or journal.get_editors_in_chief_id() in signatures:
            return
        raise openreview.OpenReviewException("Only the venue process or Editors-in-Chief can request previous continuity assignment.")

    def load_trigger_note():
        try:
            return client.get_note(edit.note.id)
        except Exception:
            return edit.note

    def lock_invitation_for_note(note):
        lock_invitation_id = f"{venue_id}/Paper{note.number}/-/Assignment_Setup_Automation"
        try:
            return client.get_invitation(lock_invitation_id)
        except Exception:
            return openreview.api.Invitation(
                id=lock_invitation_id,
                readers=[venue_id, journal.get_editors_in_chief_id()],
                writers=[venue_id],
                signatures=[venue_id],
                invitees=[],
                content={
                    "noteId": {"value": note.id},
                    "noteNumber": {"value": note.number},
                    "setupInvitationId": {"value": f"{venue_id}/-/Setup_Assignments"},
                },
            )

    def lock_value(current_invitation, field, default=""):
        return content_value(current_invitation, field, default)

    def post_lock_status(lock_invitation, status, operation_key, extra_content=None):
        content = {
            "previousAeAssignmentStatus": {"value": status},
            "previousAeAssignmentOperationKey": {"value": operation_key},
            "previousAeAssignmentUpdatedAt": {"value": now_millis()},
        }
        if extra_content:
            for key, value in extra_content.items():
                content[key] = {"value": value}
        client.post_invitation_edit(
            invitations=journal.get_meta_invitation_id(),
            signatures=[venue_id],
            invitation=openreview.api.Invitation(
                id=lock_invitation.id,
                content=content,
            ),
            replacement=False,
        )

    def claim_lock(note):
        lock_invitation = lock_invitation_for_note(note)
        status = lock_value(lock_invitation, "previousAeAssignmentStatus", "")
        if status in {"in_progress", "success", "failed"}:
            return None, status, lock_invitation
        operation_key = f"{note.id}:{now_millis()}"
        post_lock_status(lock_invitation, "in_progress", operation_key, {
            "previousAeAssignmentPaperNumber": note.number,
        })
        try:
            refreshed_invitation = client.get_invitation(lock_invitation.id)
        except Exception:
            refreshed_invitation = lock_invitation
        if (
            lock_value(refreshed_invitation, "previousAeAssignmentStatus", "") == "in_progress"
            and lock_value(refreshed_invitation, "previousAeAssignmentOperationKey", "") == operation_key
        ):
            return operation_key, "claimed", refreshed_invitation
        return None, lock_value(refreshed_invitation, "previousAeAssignmentStatus", "in_progress"), refreshed_invitation

    def run_with_timeout(operation):
        try:
            signal = __import__("signal")
        except Exception:
            return operation()
        previous_handler = None

        def timeout_handler(_signum, _frame):
            raise TimeoutError("previous continuity assignment timed out after 1 hour")

        try:
            previous_handler = signal.getsignal(signal.SIGALRM)
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(TIMEOUT_SECONDS)
            return operation()
        finally:
            try:
                signal.alarm(0)
                if previous_handler is not None:
                    signal.signal(signal.SIGALRM, previous_handler)
            except Exception:
                pass

    require_allowed_actor()
    trigger_note = load_trigger_note()
    note_id = note_content_value(trigger_note, "note_id", "")
    note_number = note_content_value(trigger_note, "paper_number", "")
    if not note_id:
        raise openreview.OpenReviewException("Previous continuity assignment requires note_id.")
    note = client.get_note(note_id)
    if note_number and int(note_number) != int(note.number):
        raise openreview.OpenReviewException("Previous continuity assignment paper_number does not match note_id.")

    operation_key, lock_status, lock_invitation = claim_lock(note)
    if not operation_key:
        print(f"Previous continuity assignment skipped Paper{note.number}; lock status is {lock_status}.")
        return

    try:
        result = run_with_timeout(
            lambda: continuity_namespace["auto_assign_previous_ae_after_setup"](
                client,
                journal,
                content_value,
                setup_state_namespace["classify_assignment_setup_state"],
                note,
            )
        )
    except TimeoutError as error:
        result = {"status": "failed", "reason": "timeout", "error": str(error)}
    except Exception as error:
        result = {"status": "failed", "reason": "unexpected_exception", "error": str(error)}

    try:
        status = result.get("status")
        if status == "assigned":
            post_lock_status(lock_invitation, "success", operation_key, {
                "previousAeAssignmentResult": result.get("previous_ae"),
            })
            print(
                f"Previous continuity assignment posted {result.get('previous_ae')} for Paper{note.number}. "
                "Selected previous reviewer assignment, when available, is handled best-effort by the AE assignment process."
            )
        elif status == "failed":
            post_lock_status(lock_invitation, "failed", operation_key, {
                "previousAeAssignmentResult": result.get("previous_ae") or "",
                "previousAeAssignmentError": result.get("error") or result.get("reason") or "failed",
            })
            print(
                f"Previous continuity assignment failed for Paper{note.number} with {result.get('previous_ae')}: "
                f"{result.get('error') or result.get('reason')}"
            )
        else:
            post_lock_status(lock_invitation, "failed", operation_key, {
                "previousAeAssignmentError": result.get("reason") or "skipped",
            })
            detail = result.get("setup_state") or result.get("error") or result.get("reason")
            print(f"Previous continuity assignment skipped Paper{note.number}; {result.get('reason')}: {detail}.")
    except Exception as terminal_error:
        print(
            f"Previous continuity assignment for Paper{note.number} could not write terminal lock status "
            f"for operation {operation_key}: {terminal_error}"
        )
