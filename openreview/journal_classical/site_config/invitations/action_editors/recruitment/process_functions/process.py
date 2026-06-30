def process(client, edit, invitation):
    from Crypto.Hash import HMAC, SHA256
    import datetime
    import openreview
    import urllib.parse

    SHORT_PHRASE = "JMLR"
    ROLE_NAME = "Action Editor"
    ACCEPTED_ID = "JMLR/Action_Editors"
    RECRUITMENT_INVITE_ID = "JMLR/Action_Editors/-/Recruitment_Invite"
    HASH_SEED = "4567"
    VENUE_ID = "JMLR"
    BULK_INVITE_ACCEPT_EMAIL_TEMPLATE = {{EMAIL_TEMPLATE_JSON:recruitment/bulk_invite_accept.txt}}
    RESPONSE_RECORDED_EMAIL_TEMPLATE = {{EMAIL_TEMPLATE_JSON:recruitment/response_recorded.txt}}
    INTERNAL_ERROR_EMAIL_TEMPLATE = {{EMAIL_TEMPLATE_JSON:recruitment/internal_error.txt}}
    journal = openreview.journal.JournalRequest.get_journal(client, "{{PROD_JOURNAL_ID}}")

    helper_namespace = {"openreview": openreview}
    exec("{{PYTHON_SCRIPT_JSON:invitations/recruitment/profile_resolution.py}}", helper_namespace)
    exec("{{PYTHON_SCRIPT_JSON:invitations/recruitment/invite_edges.py}}", helper_namespace)

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
            role_phrase=f"an {ROLE_NAME}",
            short_name=SHORT_PHRASE,
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
            set_group_member(ACCEPTED_ID, profile_id, True)
        except Exception as error:
            helper_namespace["mark_action_failed"](client, edge, signature=VENUE_ID)
            post_action_failed_email(profile_id, error)
            expire_response_note()
            raise error
        helper_namespace["mark_accepted"](client, edge, signature=VENUE_ID)
        helper_namespace["supersede_older_pending_edges"](client, edge, matching_edges, signature=VENUE_ID)
        publish_generic_receipt(profile_id)

        subject = f"[{SHORT_PHRASE}] {SHORT_PHRASE} {ROLE_NAME} invitation accepted"
        message = bulk_invite_accept_email()

        post_status_email(subject, [profile_id], message, parent_group=ACCEPTED_ID)
    elif response_value == "No":
        declined_member = profile_id or user
        if profile_id:
            helper_namespace["store_resolved_profile_on_invite_edge"](edge, profile_id)
        helper_namespace["mark_declined"](client, edge, signature=VENUE_ID)
        helper_namespace["supersede_older_pending_edges"](client, edge, matching_edges, signature=VENUE_ID)
        publish_generic_receipt(profile_id)

        subject = f"[{SHORT_PHRASE}] {SHORT_PHRASE} {ROLE_NAME} invitation declined"
        message = recorded_response_email(
            f"You have declined the invitation to serve as an {ROLE_NAME} for {SHORT_PHRASE}.",
            "No action is needed.",
            "{{fullname}}",
        )

        post_status_email(subject, [declined_member], message)
    else:
        raise openreview.OpenReviewException(f"Invalid response: {response_value}")
