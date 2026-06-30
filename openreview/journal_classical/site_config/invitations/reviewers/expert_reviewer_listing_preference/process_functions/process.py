def process(client, edge, invitation):
    import json

    journal = openreview.journal.JournalRequest.get_journal(client, "{{PROD_JOURNAL_ID}}")
    venue_id = journal.venue_id
    expert_reviewers_id = f"{venue_id}/Expert_Reviewers"
    expert_reviewer_state_id = f"{venue_id}/Expert_Reviewer_State"
    reviewer_id = getattr(edge, "tail", None)
    preference = getattr(edge, "label", None)

    if getattr(edge, "ddate", None):
        return

    if not reviewer_id:
        raise openreview.OpenReviewException("Top Reviewer listing preference requires a reviewer profile tail.")
    if preference not in ["List", "Opt_Out"]:
        raise openreview.OpenReviewException("Top Reviewer listing preference must be List or Opt_Out.")

    def normalize_json_map(value):
        if isinstance(value, dict):
            return dict(value)
        if isinstance(value, str) and value.strip():
            try:
                loaded = json.loads(value)
                return dict(loaded) if isinstance(loaded, dict) else {}
            except Exception:
                return {}
        return {}

    state_group = client.get_group(expert_reviewer_state_id)
    state_content = getattr(state_group, "content", None) or {}
    last_qualified_value = state_content.get("last_qualified_at", {}).get("value", "{}")
    listing_opt_out = normalize_json_map(state_content.get("listing_opt_out", {}).get("value", "{}"))

    if preference == "Opt_Out":
        listing_opt_out[reviewer_id] = True
    else:
        listing_opt_out.pop(reviewer_id, None)

    client.post_group_edit(
        invitation=journal.get_meta_invitation_id(),
        signatures=[venue_id],
        group=openreview.api.Group(
            id=expert_reviewer_state_id,
            content={
                "description": {
                    "value": (
                        "Internal Top Reviewer maintenance state. "
                        "last_qualified_at maps reviewer profile IDs to the most recent "
                        "time they satisfied the configured Top Reviewer criteria. "
                        "listing_opt_out maps reviewer profile IDs that opted out of public listing."
                    )
                },
                "last_qualified_at": {"value": last_qualified_value},
                "listing_opt_out": {"value": json.dumps(listing_opt_out, sort_keys=True)},
            },
        ),
    )

    if preference != "Opt_Out":
        return

    expert_reviewers_group = client.get_group(expert_reviewers_id)
    members = list(getattr(expert_reviewers_group, "members", None) or [])
    if reviewer_id not in members:
        return

    client.post_group_edit(
        invitation=journal.get_meta_invitation_id(),
        signatures=[venue_id],
        group=openreview.api.Group(
            id=expert_reviewers_id,
            members=sorted(member for member in members if member != reviewer_id),
        ),
    )
