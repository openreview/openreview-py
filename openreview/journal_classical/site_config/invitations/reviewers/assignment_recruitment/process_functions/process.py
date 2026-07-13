def process(client, edit, invitation):
    from Crypto.Hash import HMAC, SHA256
    import urllib.parse
    from datetime import datetime, timezone
    import re

    journal = openreview.journal.JournalRequest.get_journal(client, "{{PROD_JOURNAL_ID}}")

    venue_id = journal.venue_id
    short_phrase = journal.short_name
    committee_name = journal.reviewers_name
    hash_seed = journal.secret_key
    invite_assignment_invitation_id = journal.get_reviewer_invite_assignment_id()
    legacy_assignment_invitation_id = journal.get_reviewer_assignment_id()
    invited_label = 'Invitation Sent'
    accepted_label = 'Accepted'
    declined_label = 'Declined'
    conflict_label = 'Conflict Detected'
    action_failed_label = 'Accepted - Action Failed'
    expired_label = 'Expired'
    superseded_label = 'Superseded'
    external_acceptance_assignment_label = 'External Reviewer Acceptance'
    unavailable_invitation_message = "{{MESSAGE_TEMPLATE_JSON:recruitment/invitation_unavailable.txt}}"
    response_recorded_email_template = {{EMAIL_TEMPLATE_JSON:recruitment/response_recorded.txt}}
    internal_error_email_template = {{EMAIL_TEMPLATE_JSON:recruitment/internal_error.txt}}
    note = edit.note
    helper_namespace = {"openreview": openreview}
    exec("{{PYTHON_SCRIPT_JSON:invitations/recruitment/profile_resolution.py}}", helper_namespace)
    exec("{{PYTHON_SCRIPT_JSON:invitations/recruitment/invite_edges.py}}", helper_namespace)

    user = urllib.parse.unquote(note.content['user']['value'])
    hashkey = HMAC.new(hash_seed.encode(), digestmod=SHA256).update(user.encode()).hexdigest()
    if hashkey != note.content['key']['value']:
        raise openreview.OpenReviewException(f'Invalid key or user: {user}')

    response_profile = helper_namespace["resolved_logged_in_profile_for_invited_user"](client, edit, note, user)

    submission = client.get_notes(note.content['submission_id']['value'])[0]
    assignment_invitation_id = journal.get_reviewer_assignment_id(number=submission.number)
    identities = []
    helper_namespace["add_identity"](identities, user)
    for identity in helper_namespace["profile_identities"](response_profile):
        helper_namespace["add_identity"](identities, identity)
    edge_id = note.content.get('edge_id', {}).get('value') if isinstance(note.content.get('edge_id'), dict) else None
    edge, invitation_edges = helper_namespace["select_edge_by_id_or_pending"](
        client,
        invite_assignment_invitation_id,
        submission.id,
        edge_id,
        identities,
        allow_edge_id_without_identity=True,
    )
    if not edge:
        raise openreview.OpenReviewException(unavailable_invitation_message)

    allowed_labels = [invited_label, accepted_label, conflict_label, action_failed_label, expired_label, superseded_label]
    if edge.label not in allowed_labels and not edge.label.startswith(declined_label):
        raise openreview.OpenReviewException(unavailable_invitation_message)

    def update_invite_edge(label):
        edge.label = label
        edge.cdate = None
        edge.ddate = None
        client.post_edge(edge)

    default_reply_to = None

    def post_status_email(subject, recipients, message, reply_to=None):
        client.post_message(
            subject,
            recipients,
            message,
            invitation=journal.get_meta_invitation_id(),
            signature=venue_id,
            replyTo=reply_to or default_reply_to or journal.contact_info,
            sender=journal.get_message_sender()
        )

    def post_accept_identity_warning_on_reply(warning, readers):
        if not warning or not getattr(note, 'id', None):
            return
        warning_readers = []
        for reader in [venue_id, journal.get_editors_in_chief_id()] + list(readers or []):
            if reader and reader not in warning_readers:
                warning_readers.append(reader)
        try:
            client.post_note_edit(
                invitation=journal.get_meta_invitation_id(),
                signatures=[venue_id],
                note=openreview.api.Note(
                    id=note.id,
                    content={
                        'accept_identity_warning': {
                            'value': warning,
                            'readers': warning_readers
                        }
                    }
                )
            )
        except Exception as error:
            print(f'Could not record accept identity warning on response note {note.id}: {error}')

    def consume_invite_for_accept():
        if getattr(edge, 'id', None):
            latest_edges = client.get_edges(id=edge.id, trash=True)
            latest_edge = latest_edges[0] if latest_edges else edge
        else:
            latest_edge = edge
        latest_label = getattr(latest_edge, 'label', None)
        if helper_namespace["is_deleted"](latest_edge) or latest_label not in [invited_label, action_failed_label]:
            raise openreview.OpenReviewException(unavailable_invitation_message)
        return helper_namespace["mark_accepted"](client, latest_edge)

    def consume_invite_for_decline(comment=None):
        if getattr(edge, 'id', None):
            latest_edges = client.get_edges(id=edge.id, trash=True)
            latest_edge = latest_edges[0] if latest_edges else edge
        else:
            latest_edge = edge
        latest_label = getattr(latest_edge, 'label', None)
        if latest_label and latest_label.startswith(declined_label):
            return latest_edge
        if helper_namespace["is_deleted"](latest_edge) or latest_label != invited_label:
            raise openreview.OpenReviewException(unavailable_invitation_message)
        return helper_namespace["mark_declined"](client, latest_edge, comment)

    def consume_already_assigned_invite_for_accept():
        try:
            accepted_edge = consume_invite_for_accept()
            safely_supersede_older_pending_edges(accepted_edge)
            expire_response_note()
            return True
        except openreview.OpenReviewException:
            raise
        except Exception as error:
            print(f'Could not consume already-assigned external reviewer invite {getattr(edge, "id", None)}: {error}')
            post_status_email(
                f'[{short_phrase}] {committee_name} invitation response needs follow-up for paper {submission.number}: {submission.content["title"]["value"]}',
                [profile_id],
                internal_error_email("{{fullname}}", "the invitation response update")
            )
            post_status_email(
                f'[{short_phrase}] {committee_name} invitation action failed for paper {submission.number}: {submission.content["title"]["value"]}',
                inviter_recipients,
                internal_error_email("{{fullname}}", "the invitation response update")
            )
            expire_response_note()
            return True

    def safely_supersede_older_pending_edges(selected_edge):
        try:
            helper_namespace["supersede_older_pending_edges"](client, selected_edge, invitation_edges)
        except Exception as error:
            print(f'Could not supersede older pending external reviewer invites for {getattr(selected_edge, "id", None)}: {error}')

    def recorded_response_email(recipient_name, response_summary, next_steps):
        return response_recorded_email_template.format(
            recipient_name=recipient_name,
            response_summary=response_summary,
            next_steps=next_steps,
        )

    def internal_error_email(recipient_name, failure_context):
        return internal_error_email_template.format(
            recipient_name=recipient_name,
            short_name=short_phrase,
            failure_context=failure_context,
        )

    def expire_response_note():
        if not getattr(note, 'id', None):
            return
        client.post_note_edit(
            invitation=journal.get_meta_invitation_id(),
            signatures=[venue_id],
            note=openreview.api.Note(
                id=note.id,
                ddate=openreview.tools.datetime_millis(datetime.now(timezone.utc))
                )
            )

    def content_value_from_note(candidate_note, field):
        field_value = (candidate_note.content or {}).get(field)
        if isinstance(field_value, dict):
            return field_value.get('value')
        return field_value

    def int_or_none(value):
        if value is None:
            return None
        try:
            return int(value)
        except Exception:
            return None

    def invite_review_due_date_millis(invite_edge):
        due_date = int_or_none(getattr(invite_edge, 'weight', None))
        if due_date and due_date > 0:
            return due_date
        return None

    def post_invite_review_due_date(profile_id, invite_edge):
        due_date = invite_review_due_date_millis(invite_edge)
        if not due_date:
            return
        client.post_edge(openreview.api.Edge(
            invitation=f'{venue_id}/Reviewers/-/Review_Due_Date',
            signatures=[venue_id],
            head=submission.id,
            tail=profile_id,
            weight=due_date,
            label='Review Due Date'
        ))

    def extract_profile_ids(value):
        values = value if isinstance(value, list) else [value]
        profile_ids = []
        for item in values:
            for token in re.split(r'[\s,;|()[\]<>]+', str(item or '')):
                if re.match(r'^~[A-Za-z0-9_]+[0-9]*$', token) and token not in profile_ids:
                    profile_ids.append(token)
        return profile_ids

    def hard_author_conflict_reason(profile_id):
        authorids = content_value_from_note(submission, 'authorids') or []
        author_list = content_value_from_note(submission, 'author_list') or ''
        conflict_of_interests = content_value_from_note(submission, 'conflict_of_interests') or ''
        author_profile_ids = list(dict.fromkeys(list(authorids) + extract_profile_ids(author_list)))
        declared_conflict_profile_ids = extract_profile_ids(conflict_of_interests)
        if profile_id in author_profile_ids:
            return 'Author list'
        if profile_id in declared_conflict_profile_ids:
            return 'Author-declared conflict list'
        return None

    def matching_no_response_count():
        try:
            response_notes = client.get_notes(
                invitation=invitation.id,
                content={'user': user},
            )
        except Exception as error:
            print(f'Could not count duplicate decline response notes for {user}: {error}')
            return 0
        count = 0
        for response_note in response_notes:
            if content_value_from_note(response_note, 'response') != 'No':
                continue
            if content_value_from_note(response_note, 'submission_id') != submission.id:
                continue
            count += 1
        return count

    def add_recipient(recipients, recipient):
        if not recipient:
            return
        recipient = str(recipient).strip()
        if not recipient or recipient in recipients:
            return
        if recipient.startswith(f'{venue_id}/Paper{submission.number}/Action_Editor_'):
            return
        recipients.append(recipient)

    def resolve_inviter_recipients():
        recipients = []
        add_recipient(recipients, content_value_from_note(note, 'inviter'))
        add_recipient(recipients, getattr(edge, 'tauthor', None))
        for signature in edge.signatures or []:
            add_recipient(recipients, signature)
        if not recipients:
            add_recipient(recipients, journal.get_action_editors_id(number=submission.number))
        return recipients or [venue_id]

    def profile_email(identity):
        if not identity:
            return None
        identity = str(identity).strip()
        if not identity or identity.startswith(f'{venue_id}/') or identity == venue_id:
            return None
        if '@' in identity and not identity.startswith('~'):
            return identity
        try:
            profile = openreview.tools.get_profiles(
                client,
                ids_or_emails=[identity.split(',')[0]],
                with_preferred_emails=journal.get_preferred_emails_invitation_id()
            )[0]
            return profile.get_preferred_email() if profile else None
        except Exception as error:
            print(f'Could not load preferred email for {identity}: {error}')
        return None

    def resolve_assigned_ae_reply_to():
        candidates = [
            content_value_from_note(note, 'inviter'),
            getattr(edge, 'tauthor', None),
        ]
        candidates.extend(edge.signatures or [])
        try:
            candidates.extend(client.get_group(journal.get_action_editors_id(number=submission.number)).members or [])
        except Exception as error:
            print(f'Could not load assigned action editor group for Paper{submission.number}: {error}')
        for candidate in candidates:
            email = profile_email(candidate)
            if email:
                return email
        return None

    preferred_name = response_profile.get_preferred_name(pretty=True) if response_profile else edge.tail
    inviter_recipients = resolve_inviter_recipients()
    default_reply_to = resolve_assigned_ae_reply_to()

    if edge.label.startswith(declined_label) and note.content['response']['value'] == 'No':
        if matching_no_response_count() <= 2:
            expire_response_note()
            return
        raise openreview.OpenReviewException(unavailable_invitation_message)

    if helper_namespace["is_deleted"](edge) or edge.label == accepted_label or edge.label == conflict_label or edge.label == expired_label or edge.label == superseded_label or edge.label.startswith(declined_label):
        raise openreview.OpenReviewException(unavailable_invitation_message)

    if note.content['response']['value'] == 'Yes':
        print('Invitation accepted', edge.tail, submission.number)

        if not response_profile:
            print(f'Accept not recorded for unresolved invited reviewer {edge.tail}')
            expire_response_note()
            return
        invited_profile = note.content.get('invited_profile', {}).get('value') if isinstance(note.content.get('invited_profile'), dict) else None
        accept_rejection_reason = helper_namespace["invited_user_accept_rejection_reason"](response_profile, user, invited_profile)
        if accept_rejection_reason:
            raise openreview.OpenReviewException(accept_rejection_reason)
        accept_identity_warning = helper_namespace["invited_user_accept_warning"](response_profile, user, invited_profile)
        post_accept_identity_warning_on_reply(accept_identity_warning, inviter_recipients)

        profile_id = response_profile.id
        if not (profile_id and profile_id.startswith('~')):
            print(f'Accept not recorded for unresolved profile id {profile_id}')
            expire_response_note()
            return
        helper_namespace["store_resolved_profile_on_invite_edge"](edge, profile_id)
        assignment_edges = (
            client.get_edges(invitation=assignment_invitation_id, head=submission.id, tail=profile_id) +
            client.get_edges(invitation=legacy_assignment_invitation_id, head=submission.id, tail=profile_id)
        )
        active_assignment_exists = any(not assignment_edge.ddate for assignment_edge in assignment_edges)
        if active_assignment_exists:
            print('User already assigned to paper', submission.id, profile_id)
            if consume_already_assigned_invite_for_accept():
                return

        author_conflict_reason = hard_author_conflict_reason(profile_id)
        if author_conflict_reason:
            print('Author conflict detected', author_conflict_reason)
            helper_namespace["store_resolved_profile_on_invite_edge"](edge, profile_id)
            helper_namespace["mark_conflict"](client, edge)
            subject = f'[{short_phrase}] Conflict detected for paper {submission.number}: {submission.content["title"]["value"]}'
            message = recorded_response_email(
                "{{fullname}}",
                f"You have accepted the invitation to review the paper number: {submission.number}, title: {submission.content['title']['value']}.",
                f"An author conflict was detected from the paper {author_conflict_reason} and the assignment can not be done.",
            )
            post_status_email(subject, [profile_id], message)
            post_status_email(
                f'[{short_phrase}] Conflict detected for reviewer {preferred_name} and paper {submission.number}: {submission.content["title"]["value"]}',
                inviter_recipients,
                recorded_response_email(
                    "{{fullname}}",
                    f"{preferred_name} accepted the invitation to review paper {submission.number}, but an author conflict was detected from the paper {author_conflict_reason} and the reviewer was not assigned.",
                    ("No assignment was created by this invitation."
                     + (f"\n\nWarning: {accept_identity_warning}" if accept_identity_warning else "")),
                )
            )
            return

        try:
            edge = consume_invite_for_accept()
            safely_supersede_older_pending_edges(edge)
        except openreview.OpenReviewException as error:
            if str(error) == unavailable_invitation_message or unavailable_invitation_message in str(error):
                raise
            print(f'Could not consume accepted external reviewer invite {edge.id}: {error}')
            post_status_email(
                f'[{short_phrase}] {committee_name} invitation response needs follow-up for paper {submission.number}: {submission.content["title"]["value"]}',
                [profile_id],
                internal_error_email("{{fullname}}", "the invitation response update")
            )
            post_status_email(
                f'[{short_phrase}] {committee_name} invitation action failed for paper {submission.number}: {submission.content["title"]["value"]}',
                inviter_recipients,
                internal_error_email("{{fullname}}", "the invitation response update")
            )
            expire_response_note()
            return
        except Exception as error:
            print(f'Could not consume accepted external reviewer invite {edge.id}: {error}')
            post_status_email(
                f'[{short_phrase}] {committee_name} invitation response needs follow-up for paper {submission.number}: {submission.content["title"]["value"]}',
                [profile_id],
                internal_error_email("{{fullname}}", "the invitation response update")
            )
            post_status_email(
                f'[{short_phrase}] {committee_name} invitation action failed for paper {submission.number}: {submission.content["title"]["value"]}',
                inviter_recipients,
                internal_error_email("{{fullname}}", "the invitation response update")
            )
            expire_response_note()
            return

        try:
            reviewer_group = client.get_group(journal.get_reviewers_id())
            if profile_id not in (reviewer_group.members or []):
                client.add_members_to_group(journal.get_reviewers_id(), profile_id)
        except Exception as error:
            print(f'Could not add accepted external reviewer {profile_id} to {journal.get_reviewers_id()}: {error}')
            helper_namespace["mark_action_failed"](client, edge)
            post_status_email(
                f'[{short_phrase}] {committee_name} invitation response needs follow-up for paper {submission.number}: {submission.content["title"]["value"]}',
                [profile_id],
                internal_error_email("{{fullname}}", "the reviewer role or paper assignment update")
            )
            post_status_email(
                f'[{short_phrase}] {committee_name} invitation action failed for paper {submission.number}: {submission.content["title"]["value"]}',
                inviter_recipients,
                internal_error_email("{{fullname}}", "the reviewer role or paper assignment update")
            )
            expire_response_note()
            return
        assignment_edges = (
            client.get_edges(invitation=assignment_invitation_id, head=submission.id, tail=profile_id) +
            client.get_edges(invitation=legacy_assignment_invitation_id, head=submission.id, tail=profile_id)
        )
        if not any(not assignment_edge.ddate for assignment_edge in assignment_edges):
            print('post assignment edge', profile_id)
            try:
                post_invite_review_due_date(profile_id, edge)
                client.post_edge(openreview.api.Edge(
                    invitation=assignment_invitation_id,
                    head=edge.head,
                    tail=profile_id,
                    weight=1,
                    label=external_acceptance_assignment_label,
                    signatures=[venue_id]
                ))
            except Exception as error:
                print(f'Could not assign accepted external reviewer {profile_id} to Paper{submission.number}: {error}')
                helper_namespace["mark_action_failed"](client, edge)
                post_status_email(
                    f'[{short_phrase}] {committee_name} invitation response needs follow-up for paper {submission.number}: {submission.content["title"]["value"]}',
                    [profile_id],
                    internal_error_email("{{fullname}}", "the paper assignment update")
                )
                post_status_email(
                    f'[{short_phrase}] {committee_name} invitation action failed for paper {submission.number}: {submission.content["title"]["value"]}',
                    inviter_recipients,
                    internal_error_email("{{fullname}}", "the paper assignment update")
                )
                expire_response_note()
                return

            subject = f'[{short_phrase}] {committee_name} Invitation accepted for paper {submission.number}: {submission.content["title"]["value"]}'
            message = recorded_response_email(
                "{{fullname}}",
                f"Thank you for accepting the invitation to review the paper number: {submission.number}, title: {submission.content['title']['value']}.",
                f"Your response has been recorded, your OpenReview profile is active in the {short_phrase} {committee_name} group, and you are assigned to this paper.\n\nPlease complete the review in OpenReview.\n\nYou can adjust your reviewer availability and reviewing load at any time from the {short_phrase} {committee_name} Console. This external paper invitation path can bypass the standard reviewer max-load and cooldown checks. If the assignment is not manageable, please contact the Action Editor.",
            )
            post_status_email(subject, [profile_id], message)
            post_status_email(
                f'[{short_phrase}] Reviewer {preferred_name} accepted to review paper {submission.number}: {submission.content["title"]["value"]}',
                inviter_recipients,
                recorded_response_email(
                    "{{fullname}}",
                    f"{preferred_name} accepted your invitation to review paper {submission.number} and is now assigned to the paper.",
                    ("No action is needed."
                     + (f"\n\nWarning: {accept_identity_warning}" if accept_identity_warning else "")),
                )
            )
            return

    else:
        print('Invitation declined', edge.tail, submission.number)
        assignment_tail = response_profile.id if response_profile else edge.tail
        if response_profile:
            helper_namespace["store_resolved_profile_on_invite_edge"](edge, response_profile.id)

        label = declined_label
        if 'comment' in note.content:
            label = label + ': ' + note.content['comment']['value']
        edge = consume_invite_for_decline(note.content.get('comment', {}).get('value') if isinstance(note.content.get('comment'), dict) else None)
        safely_supersede_older_pending_edges(edge)

        subject = f'[{short_phrase}] {committee_name} Invitation declined for paper {submission.number}: {submission.content["title"]["value"]}'
        message = recorded_response_email(
            "{{fullname}}",
            f"You have declined the invitation to review the paper number: {submission.number}, title: {submission.content['title']['value']}.",
            "Your response has been recorded, and you are not assigned to this paper by this invitation.",
        )
        post_status_email(subject, [assignment_tail], message)
        post_status_email(
            f'[{short_phrase}] Reviewer {preferred_name} declined to review paper {submission.number}: {submission.content["title"]["value"]}',
            inviter_recipients,
            recorded_response_email(
                "{{fullname}}",
                f"{preferred_name} declined your invitation to review paper {submission.number} and is not assigned by this invitation.",
                f"To read their response, please click here: {{SITE_URL}}/forum?id={note.id}",
            )
        )
