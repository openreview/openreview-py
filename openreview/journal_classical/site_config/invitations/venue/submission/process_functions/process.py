def process(client, edit, invitation):
    source_invitation_id = getattr(invitation, "id", None) or "JMLR/-/Submission"
    source_invitation = client.get_invitation(source_invitation_id)
    source_content = getattr(source_invitation, "content", {}) or {}
    process_script = source_content.get("process_script", {}).get("value")
    if not process_script:
        raise openreview.OpenReviewException(f"{source_invitation_id} is missing content.process_script.")
    funcs = {
        "openreview": openreview
    }
    exec(process_script, funcs)
    funcs["process"](client, edit, invitation)
