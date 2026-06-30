def process(client, edit, invitation):
    from Crypto.Hash import HMAC, SHA256
    import datetime
    import openreview
    import re
    import urllib.parse

    SHORT_PHRASE = "JMLR"
    ROLE_NAME = "Reviewer"
    ACCEPTED_ID = "JMLR/Reviewers"
    RECRUITMENT_INVITE_ID = "JMLR/Reviewers/-/Recruitment_Invite"
    HASH_SEED = "4567"
    JOURNAL_REQUEST_ID = "ZHVA1iLGAf"
    VENUE_ID = "JMLR"
    BULK_INVITE_ACCEPT_EMAIL_TEMPLATE = {{EMAIL_TEMPLATE_JSON:recruitment/bulk_invite_accept.txt}}
    RESPONSE_RECORDED_EMAIL_TEMPLATE = {{EMAIL_TEMPLATE_JSON:recruitment/response_recorded.txt}}
    INTERNAL_ERROR_EMAIL_TEMPLATE = {{EMAIL_TEMPLATE_JSON:recruitment/internal_error.txt}}
    journal = openreview.journal.JournalRequest.get_journal(client, "{{PROD_JOURNAL_ID}}")

    helper_namespace = {"openreview": openreview}
    exec("{{PYTHON_SCRIPT_JSON:invitations/recruitment/profile_resolution.py}}", helper_namespace)
    exec("{{PYTHON_SCRIPT_JSON:invitations/recruitment/invite_edges.py}}", helper_namespace)
    publication_expertise_namespace = {"openreview": openreview, "re": re}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/reviewer_publication_expertise.py}}", publication_expertise_namespace)

    note = edit.note if hasattr(edit, "note") else edit

    def content_value(field):
        value = note.content[field]
        if isinstance(value, dict) and "value" in value:
            return value["value"]
        return value

    user = urllib.parse.unquote(content_value("user"))
    edge_id = content_value("edge_id")
    key = content_value("key")
    response_value = content_value("response")

    hashkey = HMAC.new(HASH_SEED.encode(), f"{edge_id}:{user}".encode(), digestmod=SHA256).hexdigest()
    if hashkey != key:
        raise openreview.OpenReviewException(f"Invalid key for user: {user}")

    def group_has_member(group_id, member):
        try:
            return bool(client.get_groups(id=group_id, member=member))
        except Exception:
            return False

    def set_group_member(group_id, member, include):
        group = client.get_group(group_id)
        members = list(group.members or [])
        has_member = member in members
        if include and not has_member:
            members.append(member)
        elif not include and has_member:
            members = [item for item in members if item != member]
        else:
            return False
        client.post_group_edit(
            invitation=f"{VENUE_ID}/-/Edit",
            signatures=[VENUE_ID],
            group=openreview.api.Group(id=group_id, members=members),
        )
        return True

    def publish_generic_receipt(profile_id):
        receipt_content = {
            "title": {"value": f"{ROLE_NAME} recruitment response recorded"},
            "user": {"value": "redacted"},
            "edge_id": {"value": edge_id},
            "key": {"value": ""},
            "response": {"value": response_value},
        }
        if profile_id:
            receipt_content["profile_id"] = {"value": profile_id}
        client.post_note_edit(
            invitation=f"{VENUE_ID}/-/Edit",
            signatures=[VENUE_ID],
            note=openreview.api.Note(
                id=getattr(note, "id", None),
                readers=[f"{VENUE_ID}/Editors_In_Chief"],
                writers=[VENUE_ID],
                content=receipt_content,
            ),
        )

    def expire_response_note():
        if not getattr(note, "id", None):
            return
        client.post_note_edit(
            invitation=f"{VENUE_ID}/-/Edit",
            signatures=[VENUE_ID],
            note=openreview.api.Note(
                id=note.id,
                ddate=openreview.tools.datetime_millis(datetime.datetime.now(datetime.timezone.utc)),
            ),
        )

    def post_action_failed_email(recipient, error):
        post_status_email(
            f"[{SHORT_PHRASE}] {SHORT_PHRASE} {ROLE_NAME} invitation response needs follow-up",
            [recipient],
            INTERNAL_ERROR_EMAIL_TEMPLATE.format(
                recipient_name="{{fullname}}",
                short_name=SHORT_PHRASE,
                failure_context="the role update",
            ),
        )

    def post_status_email(subject, recipients, message, parent_group=None):
        client.post_message(
            subject,
            recipients,
            message,
            invitation=journal.get_meta_invitation_id(),
            signature=VENUE_ID,
            sender=journal.get_message_sender(),
            parentGroup=parent_group,
        )

    def recorded_response_email(response_summary, next_steps, recipient_name="{{fullname}}"):
        return RESPONSE_RECORDED_EMAIL_TEMPLATE.format(
            recipient_name=recipient_name,
            response_summary=response_summary,
            next_steps=next_steps,
        )

    def bulk_invite_accept_email():
        return BULK_INVITE_ACCEPT_EMAIL_TEMPLATE.format(
            recipient_name="{{fullname}}",
            role_phrase=f"a {ROLE_NAME}",
            short_name=SHORT_PHRASE,
        )

    def publish_reviewer_recruitment_by_ae_comment(action, profile_id):
        if not JOURNAL_REQUEST_ID:
            return
        journal_request = client.get_note(JOURNAL_REQUEST_ID)
        support_group = (journal_request.invitations[0].split("/-/")[0] if journal_request.invitations else "")
        if not support_group:
            return
        recruitment_notes = list(openreview.tools.iterget_notes(
            client,
            invitation=f"{support_group}/Journal_Request{journal_request.number}/-/Reviewer_Recruitment_by_AE",
            replyto=JOURNAL_REQUEST_ID,
            sort="number:desc",
        ))
        for recruitment_note in recruitment_notes:
            invitee = recruitment_note.content["invitee_email"]["value"].strip()
            invitee_ids = [invitee]
            invitee_profile = openreview.tools.get_profile(client, invitee)
            if invitee_profile:
                invitee_ids.append(invitee_profile.id)
            if user not in invitee_ids and profile_id not in invitee_ids:
                continue
            comment_inv = client.get_invitation(id=f"{support_group}/Journal_Request{journal_request.number}/-/Comment")
            comment_content = f"The user {invitee} has {action} an invitation to be a reviewer for {SHORT_PHRASE}."
            recruitment_response_notes = list(openreview.tools.iterget_notes(client, replyto=recruitment_note.id, sort="number:desc"))
            if recruitment_response_notes and "New Recruitment Response" in recruitment_response_notes[0].content["title"]["value"]:
                posted_recruitment_response = recruitment_response_notes[0]
                client.post_note_edit(
                    invitation=comment_inv.id,
                    signatures=[VENUE_ID],
                    note=openreview.api.Note(
                        id=posted_recruitment_response.id,
                        replyto=posted_recruitment_response.replyto,
                        readers=posted_recruitment_response.readers,
                        content={
                            "title": posted_recruitment_response.content["title"],
                            "comment": {"value": comment_content},
                        },
                    ),
                )
            else:
                client.post_note_edit(
                    invitation=comment_inv.id,
                    signatures=[VENUE_ID],
                    note=openreview.api.Note(
                        replyto=recruitment_note.id,
                        readers=recruitment_note.readers,
                        content={
                            "title": {"value": "New Recruitment Response"},
                            "comment": {"value": comment_content},
                        },
                    ),
                )

    response_profile = helper_namespace["resolved_logged_in_profile_for_invited_user"](client, edit, note, user)
    profile_id = getattr(response_profile, "id", None)
    identities = []
    helper_namespace["add_identity"](identities, user)
    for identity in helper_namespace["profile_identities"](response_profile):
        helper_namespace["add_identity"](identities, identity)
    edge, matching_edges = helper_namespace["select_edge_by_id_or_pending"](
        client,
        RECRUITMENT_INVITE_ID,
        ACCEPTED_ID,
        edge_id,
        identities,
    )
    if not edge:
        raise openreview.OpenReviewException(f"Invalid key or user not invited: {user}")
    if helper_namespace["is_final"](edge):
        expire_response_note()
        return

    if response_value == "Yes":
        if not response_profile:
            print(f"Accept not recorded for unresolved invited {user}")
            expire_response_note()
            return
        invited_profile = content_value("invited_profile") if "invited_profile" in note.content else None
        accept_rejection_reason = helper_namespace["invited_user_accept_rejection_reason"](response_profile, user, invited_profile)
        if accept_rejection_reason:
            raise openreview.OpenReviewException(accept_rejection_reason)
        accept_identity_warning = helper_namespace["invited_user_accept_warning"](response_profile, user, invited_profile)
        if accept_identity_warning:
            print(accept_identity_warning)

        helper_namespace["store_resolved_profile_on_invite_edge"](edge, profile_id)
        try:
            routed_group = publication_expertise_namespace["route_reviewer_pool_by_publication_expertise"](
                client,
                VENUE_ID,
                profile_id,
                ACCEPTED_ID,
                {{REVIEWER_BULK_RECRUITMENT_MIN_PUBLICATION_EFFECTIVE_COUNT}},
            )
        except Exception as error:
            helper_namespace["mark_action_failed"](client, edge, signature=VENUE_ID)
            post_action_failed_email(profile_id, error)
            expire_response_note()
            raise error
        helper_namespace["mark_accepted"](client, edge, signature=VENUE_ID)
        helper_namespace["supersede_older_pending_edges"](client, edge, matching_edges, signature=VENUE_ID)
        publish_generic_receipt(profile_id)
        publish_reviewer_recruitment_by_ae_comment("accepted", profile_id)

        if routed_group == "reviewer":
            subject = f"[{SHORT_PHRASE}] {SHORT_PHRASE} {ROLE_NAME} invitation accepted"
            message = bulk_invite_accept_email()
            post_status_email(subject, [profile_id], message, parent_group=ACCEPTED_ID)
        else:
            subject = f"[{SHORT_PHRASE}] {SHORT_PHRASE} {ROLE_NAME.lower()} invitation response recorded"
            message = recorded_response_email(
                f"Thank you for responding to the {SHORT_PHRASE} {ROLE_NAME.lower()} invitation.",
                f"At this time, your OpenReview publication profile does not yet meet the publication-expertise threshold for the {SHORT_PHRASE} reviewer pool. Your profile has not been added to {ACCEPTED_ID}. You may try again later after your OpenReview publication profile is updated.",
                "{{fullname}}",
            )
            post_status_email(subject, [profile_id], message, parent_group=VENUE_ID)
    elif response_value == "No":
        declined_member = profile_id or user
        if profile_id:
            helper_namespace["store_resolved_profile_on_invite_edge"](edge, profile_id)
        helper_namespace["mark_declined"](client, edge, signature=VENUE_ID)
        helper_namespace["supersede_older_pending_edges"](client, edge, matching_edges, signature=VENUE_ID)
        publish_generic_receipt(profile_id)
        publish_reviewer_recruitment_by_ae_comment("declined", profile_id)

        subject = f"[{SHORT_PHRASE}] {SHORT_PHRASE} {ROLE_NAME} invitation declined"
        message = recorded_response_email(
            f"You have declined the invitation to serve as a {ROLE_NAME} for {SHORT_PHRASE}.",
            "No action is needed.",
            "{{fullname}}",
        )

        post_status_email(subject, [declined_member], message)
    else:
        raise openreview.OpenReviewException(f"Invalid response: {response_value}")
