def process(client, edit, invitation):
    import openreview
    import re

    venue_id = "JMLR"
    reviewers_id = f"{venue_id}/Reviewers"
    response_recorded_email_template = {{EMAIL_TEMPLATE_JSON:recruitment/response_recorded.txt}}
    journal = openreview.journal.JournalRequest.get_journal(client, "{{PROD_JOURNAL_ID}}")
    publication_expertise_namespace = {"openreview": openreview, "re": re}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/reviewer_publication_expertise.py}}", publication_expertise_namespace)
    note = edit.note

    signatures = []
    signatures.extend(getattr(edit, "signatures", None) or [])
    signatures.extend(getattr(note, "signatures", None) or [])
    profile_id = next((signature for signature in signatures if isinstance(signature, str) and signature.startswith("~")), None)
    if not profile_id:
        raise openreview.OpenReviewException("You must be signed in with an OpenReview profile to volunteer as a JMLR reviewer.")

    confirmation = note.content.get("confirmation", {}).get("value") if getattr(note, "content", None) else None
    if confirmation != "Yes, I am willing to review for JMLR":
        raise openreview.OpenReviewException("Please confirm that you are willing to review for JMLR.")

    reviewer_group = client.get_group(reviewers_id)
    members = list(reviewer_group.members or [])
    if profile_id in members:
        return

    routed_group = publication_expertise_namespace["route_reviewer_pool_by_publication_expertise"](
        client,
        venue_id,
        profile_id,
        reviewers_id,
        {{REVIEWER_SELF_VOLUNTEER_MIN_PUBLICATION_EFFECTIVE_COUNT}},
    )
    if routed_group == "reviewer":
        subject = "[JMLR] JMLR reviewer volunteer response recorded"
        next_steps = "Your profile has been added to the JMLR reviewer pool. You can use the JMLR reviewer console in OpenReview to manage reviewing availability and active assignments."
        parent_group = reviewers_id
    else:
        subject = "[JMLR] JMLR reviewer volunteer response recorded"
        next_steps = "At this time, your OpenReview publication profile does not yet meet the publication-expertise threshold for the JMLR reviewer pool. Your profile has not been added to JMLR/Reviewers. You may try again later after your OpenReview publication profile is updated."
        parent_group = venue_id
    client.post_message(
        subject,
        [profile_id],
        response_recorded_email_template.format(
            recipient_name="{{fullname}}",
            response_summary="Thank you for volunteering to serve as a reviewer for JMLR.",
            next_steps=next_steps,
        ),
        invitation=journal.get_meta_invitation_id(),
        signature=venue_id,
        sender=journal.get_message_sender(),
        parentGroup=parent_group,
    )
