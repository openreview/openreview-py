def refresh_reviewer_assignment_invitation(client, journal, note, duedate):
    refresh_reviewer_invite_assignment_process(client, journal)
    required_reviewers_namespace = {'openreview': openreview}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/review/required_reviewers.py}}", required_reviewers_namespace)
    required_reviewers_namespace['refresh_required_reviewers_edge_invitation'](client, journal, note)

    reviewer_assignment_invitation = client.get_invitation(journal.get_reviewer_assignment_id(number=note.number))
    reviewer_assignment_id = journal.get_reviewer_assignment_id(number=note.number)
    assignment_readers = [
        journal.get_action_editors_id(note.number),
        journal.get_editors_in_chief_id()
    ]
    reviewer_assignment_invitation.readers = assignment_readers
    reviewer_assignment_invitation.invitees = list(dict.fromkeys(
        list(reviewer_assignment_invitation.invitees or []) + [
            journal.get_action_editors_id(note.number),
            journal.get_editors_in_chief_id()
        ]
    ))
    selected_tail_param = "$" + "{2/tail}"
    reviewer_assignment_edge_schema = {
        "id": {"param": {"withInvitation": reviewer_assignment_id, "optional": True}},
        "ddate": {"param": {"range": [0, 9999999999999], "optional": True, "deletable": True}},
        "cdate": {"param": {"range": [0, 9999999999999], "optional": True, "deletable": True}},
        "readers": [
            journal.get_editors_in_chief_id(),
            journal.get_action_editors_id(note.number),
            selected_tail_param,
        ],
        "nonreaders": [journal.get_authors_id(note.number)],
        "writers": [
            journal.get_editors_in_chief_id(),
            journal.get_action_editors_id(note.number),
        ],
        "signatures": {
            "param": {
                "items": [
                    {"value": journal.venue_id, "optional": True},
                    {"value": journal.get_editors_in_chief_id(), "optional": True},
                    {
                        "prefix": f"{journal.venue_id}/Paper{note.number}/Action_Editor_",
                        "optional": True,
                    },
                ]
            }
        },
        "head": {"param": {"type": "note", "const": note.id}},
        "tail": {
            "param": {
                "type": "profile",
                "options": {"group": journal.get_reviewers_id()},
            }
        },
        "weight": {"param": {"minimum": -1}},
        "label": {"param": {"optional": True, "deletable": True, "minLength": 1}},
    }
    reviewer_assignment_invitation.type = "Edge"
    reviewer_assignment_invitation.signatures = [journal.venue_id]
    reviewer_assignment_invitation.edge = reviewer_assignment_edge_schema
    if isinstance(getattr(reviewer_assignment_invitation, 'edit', None), dict):
        reviewer_assignment_invitation.edit = reviewer_assignment_edge_schema
    reviewer_assignment_invitation.preprocess = client.get_invitation(journal.get_reviewer_assignment_id()).preprocess
    reviewer_assignment_invitation.process = client.get_invitation(journal.get_reviewer_assignment_id()).process
    required_reviewers_source = "{{PYTHON_SCRIPT_JSON:invitations/venue/review/required_reviewers.py}}"
    reviewer_assignment_reminder_script = f"""def process(client, invitation):
    journal = openreview.journal.JournalRequest.get_journal(client, {journal.request_form_id!r})
    submission = client.get_note({note.id!r})
    reviewer_assignment_id = journal.get_reviewer_assignment_id(number={note.number})
    active_assignments = [
        edge for edge in client.get_edges(invitation=reviewer_assignment_id, head=submission.id)
        if not getattr(edge, 'ddate', None)
    ]
    required_reviewers_namespace = {{'openreview': openreview}}
    exec({required_reviewers_source!r}, required_reviewers_namespace)
    required_reviewers = required_reviewers_namespace['get_required_reviewers'](client, journal, submission)
    if len(active_assignments) >= required_reviewers:
        return
    decisions = client.get_notes(forum=submission.id, invitation=journal.get_ae_decision_id(number={note.number}))
    if decisions:
        return
    ae_group = client.get_group(journal.get_action_editors_id())
    template = ae_group.content.get('assign_reviewers_reminder_email_template_script', {{}}).get('value')
    if not template:
        return
    client.post_message(
        invitation=journal.get_meta_invitation_id(),
        recipients=[journal.get_action_editors_id(number=submission.number)],
        subject=f'''[{{journal.short_name}}] Assign reviewers reminder for {{journal.short_name}} submission {{submission.number}}: {{submission.content['title']['value']}}''',
        message=template.format(
            short_name=journal.short_name,
            submission_number=submission.number,
            submission_title=submission.content['title']['value'],
            assigned_count=len(active_assignments),
            required_reviewers=required_reviewers,
            reviewer_assignment_duedate={duedate.strftime("%b %d")!r},
            assign_reviewers_url=f'{{SITE_URL}}/invitation?id={{reviewer_assignment_id}}',
            contact_info=journal.contact_info
        ),
        replyTo=journal.contact_info,
        signature=journal.venue_id,
        sender=journal.get_message_sender()
    )
    """
    reviewer_assignment_reminder_dates = [
        int((duedate.timestamp() + (week * 7 * 24 * 60 * 60)) * 1000)
        for week in range(26)
    ]
    reviewer_assignment_invitation.dateprocesses = [
        {
            'dates': reviewer_assignment_reminder_dates,
            'script': reviewer_assignment_reminder_script
        }
    ]
    client.post_invitation_edit(
        invitations=journal.get_meta_invitation_id(),
        signatures=[journal.venue_id],
        invitation=reviewer_assignment_invitation,
        replacement=True
    )
    return reviewer_assignment_invitation


def refresh_reviewer_invite_assignment_process(client, journal):
    invite_assignment_id = journal.get_reviewer_invite_assignment_id()
    try:
        invite_assignment = client.get_invitation(invite_assignment_id)
    except Exception as error:
        print(f'Could not load reviewer invite assignment invitation {invite_assignment_id}: {error}')
        return

    process = invite_assignment.process or ''
    updated_process = process
    updated_process = updated_process.replace(
        "inviter_preferred_name=inviter_profile.get_preferred_name(pretty=True) if inviter_profile else edge.signatures[0]",
        "inviter_identity = inviter_profile.id if inviter_profile else edge.signatures[0]\n"
        "        inviter_preferred_name=inviter_profile.get_preferred_name(pretty=True) if inviter_profile else openreview.tools.pretty_id(edge.signatures[0])\n"
        "        inviter_reply_to = inviter_profile.get_preferred_email() if inviter_profile else journal.contact_info"
    )
    encoded_invitation_url = (
        "site_url = \"{{SITE_URL}}\".rstrip(\"/\")\n"
        "        from urllib.parse import urlencode\n"
        "        invitation_query = urlencode({\n"
        "            'id': recruitment_invitation_id,\n"
        "            'user': user_profile.id,\n"
        "            'key': hashkey,\n"
        "            'submission_id': submission.id,\n"
        "            'inviter': inviter_identity,\n"
        "            'edge_id': edge.id,\n"
        "        })\n"
        "        invitation_url = f'{site_url}/invitation?{invitation_query}'"
    )
    raw_invitation_url_variants = [
        "invitation_url = f'{baseurl}/invitation?id={recruitment_invitation_id}&user={user_profile.id}&key={hashkey}&submission_id={submission.id}&inviter={inviter_profile.id}'",
        "invitation_url = f'{baseurl}/invitation?id={recruitment_invitation_id}&user={user_profile.id}&key={hashkey}&submission_id={submission.id}&inviter={inviter_identity}'",
        "invitation_url = f'{site_url}/invitation?id={recruitment_invitation_id}&user={user_profile.id}&key={hashkey}&submission_id={submission.id}&inviter={inviter_identity}'",
    ]
    for raw_invitation_url in raw_invitation_url_variants:
        updated_process = updated_process.replace(raw_invitation_url, encoded_invitation_url)
    encoded_invitation_url_without_edge_id = (
        "site_url = \"{{SITE_URL}}\".rstrip(\"/\")\n"
        "        from urllib.parse import urlencode\n"
        "        invitation_query = urlencode({\n"
        "            'id': recruitment_invitation_id,\n"
        "            'user': user_profile.id,\n"
        "            'key': hashkey,\n"
        "            'submission_id': submission.id,\n"
        "            'inviter': inviter_identity,\n"
        "        })\n"
        "        invitation_url = f'{site_url}/invitation?{invitation_query}'"
    )
    updated_process = updated_process.replace(encoded_invitation_url_without_edge_id, encoded_invitation_url)
    legacy_inviter_reply_to_name = (
        "response = client.post_message(subject, [user_profile.id], message, invitation=journal.get_meta_invitation_id(), "
        "signature=journal.venue_id, replyTo=inviter_profile."
        "get_preferred_name(), sender=journal.get_message_sender())"
    )
    updated_process = updated_process.replace(
        legacy_inviter_reply_to_name,
        "response = client.post_message(subject, [user_profile.id], message, invitation=journal.get_meta_invitation_id(), signature=journal.venue_id, replyTo=inviter_reply_to, sender=journal.get_message_sender())"
    )
    updated_process = updated_process.replace(
        "response = client.post_message(subject, [inviter_profile.id], message_AE, invitation=journal.get_meta_invitation_id(), signature=journal.venue_id, replyTo=reply_to, sender=journal.get_message_sender())",
        "response = client.post_message(subject, [inviter_identity], message_AE, invitation=journal.get_meta_invitation_id(), signature=journal.venue_id, replyTo=reply_to, sender=journal.get_message_sender())"
    )
    updated_process = updated_process.replace(
        "reply_to = user_profile.get_preferred_name() if user_profile else user",
        "reply_to = user_profile.get_preferred_email() if user_profile else user"
    )
    updated_process = updated_process.replace(
        "    if edge.ddate is None and edge.label == invite_label:",
        "    if edge.label == invite_label:"
    )
    updated_process = updated_process.replace(
        "        edge.readers=[r if r != edge.tail else user_profile.id for r in edge.readers]\n"
        "        edge.tail=user_profile.id\n"
        "        edge.cdate=None \n"
        "        client.post_edge(edge)",
        "        edge.cdate=None \n"
        "        client.post_edge(edge)"
    )
    if "review_duedate=review_due_date" not in updated_process:
        updated_process = updated_process.replace(
            "        # format the message defined above\n"
            "        subject=f'[{short_phrase}] Invitation to review paper titled \"{submission.content[\"title\"][\"value\"]}\"'",
            "        review_due_date = ''\n"
            "        try:\n"
            "            review_due_date_millis = int(getattr(edge, 'weight', None) or 0)\n"
            "            if review_due_date_millis > 0:\n"
            "                import datetime\n"
            "                review_due_date = datetime.datetime.fromtimestamp(review_due_date_millis / 1000, datetime.timezone.utc).strftime('%b %d')\n"
            "        except Exception as error:\n"
            "            print(f'Could not format reviewer invite due date for {edge.id}: {error}')\n\n"
            "        # format the message defined above\n"
            "        subject=f'[{short_phrase}] Invitation to review paper titled \"{submission.content[\"title\"][\"value\"]}\"'"
        )
        updated_process = updated_process.replace(
            "            invitation_links=invitation_links,\n"
            "            inviter_id=inviter_id,\n"
            "            inviter_preferred_name=inviter_preferred_name\n"
            "        )",
            "            invitation_links=invitation_links,\n"
            "            inviter_id=inviter_id,\n"
            "            inviter_preferred_name=inviter_preferred_name,\n"
            "            review_duedate=review_due_date\n"
            "        )"
        )
    preprocess = invite_assignment.preprocess or ''
    updated_preprocess = preprocess.replace(
        """        print(f'Check conflicts for {user_profile.id}')
        ## - Check conflicts
        authorids = submission.content['authorids']['value']
        author_profiles = openreview.tools.get_profiles(client, authorids, with_publications=True, with_relations=True)
        conflicts=openreview.tools.get_conflicts(author_profiles, user_profile, policy=conflict_policy, n_years=conflict_n_years)
        if conflicts:
            print('Conflicts detected', conflicts)
            raise openreview.OpenReviewException(f'Conflict detected for {user_profile.get_preferred_name(pretty=True)}')
""",
        """        print(f'Check author conflicts for {user_profile.id}')
        import re

        def content_value(field):
            field_value = submission.content.get(field)
            if isinstance(field_value, dict):
                return field_value.get('value')
            return field_value

        def extract_profile_ids(value):
            values = value if isinstance(value, list) else [value]
            profile_ids = []
            for item in values:
                for token in re.split(r'[\\s,;|()[\\]<>]+', str(item or '')):
                    if re.match(r'^~[A-Za-z0-9_]+[0-9]*$', token) and token not in profile_ids:
                        profile_ids.append(token)
            return profile_ids

        authorids = content_value('authorids') or []
        author_list = content_value('author_list') or ''
        conflict_of_interests = content_value('conflict_of_interests') or ''
        author_profile_ids = list(dict.fromkeys(list(authorids) + extract_profile_ids(author_list)))
        declared_conflict_profile_ids = extract_profile_ids(conflict_of_interests)
        if user_profile.id in author_profile_ids or user_profile.id in declared_conflict_profile_ids:
            print('Author conflict detected for external reviewer invite')
            raise openreview.OpenReviewException(f'Author conflict detected for {user_profile.get_preferred_name(pretty=True)}')
	"""
    )
    invite_assignment_edit = getattr(invite_assignment, 'edit', None)
    invite_assignment_schema_changed = False
    if isinstance(invite_assignment_edit, dict):
        desired_head = {
            'param': {
                'type': 'string',
            }
        }
        live_head = invite_assignment_edit.get('head', {})
        live_head_param = live_head.get('param', {}) if isinstance(live_head, dict) else {}
        if live_head_param.get('type') != 'string' or 'withInvitation' in live_head_param:
            invite_assignment_edit['head'] = desired_head
            invite_assignment_schema_changed = True
        live_tail = invite_assignment_edit.get('tail', {})
        live_tail_param = live_tail.get('param', {}) if isinstance(live_tail, dict) else {}
        invite_assignment_edit.setdefault('tail', {})
        desired_tail = {
            'param': {
                'type': 'string',
            }
        }
        if live_tail_param.get('type') != 'string' or 'minLength' in live_tail_param:
            invite_assignment_edit['tail'] = desired_tail
            invite_assignment_schema_changed = True
        invite_assignment.edit = invite_assignment_edit
    if updated_process == process and updated_preprocess == preprocess:
        if not invite_assignment_schema_changed:
            return

    invite_assignment.process = updated_process
    invite_assignment.preprocess = updated_preprocess
    try:
        client.post_invitation_edit(
            invitations=journal.get_meta_invitation_id(),
            signatures=[journal.venue_id],
            invitation=invite_assignment,
            replacement=True
        )
    except Exception as error:
        print(f'Could not update reviewer invite assignment process for {invite_assignment_id}: {error}')
