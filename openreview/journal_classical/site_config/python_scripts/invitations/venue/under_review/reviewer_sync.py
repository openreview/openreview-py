def get_paper_reviewer_maps(paper_reviewers_group):
    reviewer_signature_by_member = {}
    tail_by_anon = {}
    for index, member in enumerate(paper_reviewers_group.members or []):
        anon_member = (paper_reviewers_group.anon_members or [])[index] if index < len(paper_reviewers_group.anon_members or []) else None
        if anon_member:
            reviewer_signature_by_member[member] = anon_member
            tail_by_anon[anon_member] = member
    return reviewer_signature_by_member, tail_by_anon


def reviewer_display_label(client, member, anon_member):
    try:
        profile = openreview.tools.get_profile(client, member)
        name = profile.get_preferred_name(pretty=True) if profile else member
    except Exception:
        name = member
    if anon_member:
        return f'{name} ({member}; {anon_member})'
    return f'{name} ({member})'


def active_reviewer_assignment_tails(client, journal, submission):
    tails = []
    invitation_ids = [
        journal.get_reviewer_assignment_id(number=submission.number),
        journal.get_reviewer_assignment_id()
    ]
    for invitation_id in invitation_ids:
        try:
            for edge in client.get_edges(invitation=invitation_id, head=submission.id):
                if edge.ddate or not edge.tail or edge.tail in tails:
                    continue
                tails.append(edge.tail)
        except Exception as error:
            print(f'Could not load active reviewer assignments for Paper{submission.number} from {invitation_id}: {error}')
    return tails


def get_submitted_reviewer_tails(client, journal, submission, tail_by_anon):
    try:
        reviews = client.get_notes(
            invitation=journal.get_review_id(number=submission.number),
            forum=submission.id
        )
    except Exception as error:
        print(f'Could not load reviews for Paper{submission.number}: {error}')
        reviews = []
    return {
        tail_by_anon[signature]
        for review in reviews
        for signature in (review.signatures or [])
        if signature in tail_by_anon
    }


def get_reviewer_lookup(client, journal, submission):
    paper_reviewers_group = client.get_group(journal.get_reviewers_id(number=submission.number))
    reviewer_signature_by_member, _tail_by_anon = get_paper_reviewer_maps(paper_reviewers_group)
    reviewer_lookup = {}
    for member in active_reviewer_assignment_tails(client, journal, submission):
        reviewer_lookup[member] = member
        anon_member = reviewer_signature_by_member.get(member)
        reviewer_lookup[reviewer_display_label(client, member, anon_member)] = member
        reviewer_lookup[reviewer_display_label(client, member, None)] = member
        if anon_member:
            anon_label = anon_member.split('/')[-1]
            reviewer_lookup[anon_member] = member
            reviewer_lookup[anon_label] = member
            reviewer_lookup[anon_label.replace('_', ' ', 1)] = member
    return reviewer_lookup


def refresh_editorial_comment_reader_items(client, journal, submission):
    editorial_comment_id = f'{journal.venue_id}/Paper{submission.number}/-/Editorial_Comment'
    try:
        editorial_comment_invitation = client.get_invitation(editorial_comment_id)
    except Exception as error:
        print(f'Could not load {editorial_comment_id} to refresh reader choices: {error}')
        return
    try:
        latest_reviewers_group = client.get_group(journal.get_reviewers_id(number=submission.number))
    except Exception as error:
        print(f'Could not load reviewer group for {editorial_comment_id}: {error}')
        return
    reviewer_reader_items = [
        {'value': anon_member, 'optional': True}
        for anon_member in (getattr(latest_reviewers_group, 'anon_members', None) or [])
        if anon_member
    ]
    editorial_comment_invitation.edit['note']['readers'] = {
        'param': {
            'items': [
                {'value': journal.get_editors_in_chief_id(), 'optional': False},
                {'value': journal.get_action_editors_id(number=submission.number), 'optional': False},
                {'value': journal.get_reviewers_id(number=submission.number), 'optional': True}
            ] + reviewer_reader_items + [
                {'value': journal.get_authors_id(number=submission.number), 'optional': True}
            ]
        }
    }
    client.post_invitation_edit(
        invitations=journal.get_meta_invitation_id(),
        signatures=[journal.venue_id],
        invitation=editorial_comment_invitation,
        replacement=True
    )


def refresh_review_signature_choices(client, journal, submission):
    review_invitation_id = journal.get_review_id(number=submission.number)
    try:
        review_invitation = client.get_invitation(review_invitation_id)
    except Exception as error:
        print(f'Could not load {review_invitation_id} to refresh reviewer signatures: {error}')
        return
    try:
        latest_reviewers_group = client.get_group(journal.get_reviewers_id(number=submission.number))
    except Exception as error:
        print(f'Could not load reviewer group for {review_invitation_id}: {error}')
        return
    reviewer_signature_by_member, _tail_by_anon = get_paper_reviewer_maps(latest_reviewers_group)
    active_assignment_tails = active_reviewer_assignment_tails(client, journal, submission)
    signature_items = [
        {'value': reviewer_signature_by_member[member], 'optional': True}
        for member in active_assignment_tails
        if reviewer_signature_by_member.get(member)
    ]
    assigned_signature_values = [item['value'] for item in signature_items]
    if not isinstance(review_invitation.edit, dict):
        review_invitation.edit = {}
    review_invitation.edit['signatures'] = {'param': {'items': signature_items}}
    review_invitation.noninvitees = [
        signature for signature in (getattr(review_invitation, 'noninvitees', None) or [])
        if signature in assigned_signature_values
    ]
    review_invitation.maxReplies = max(getattr(review_invitation, 'maxReplies', 0) or 0, len(signature_items))
    client.post_invitation_edit(
        invitations=journal.get_meta_invitation_id(),
        signatures=[journal.venue_id],
        invitation=review_invitation,
        replacement=True
    )


def refresh_contact_action_editor_signature_choices(client, journal, submission):
    contact_action_editor_id = f'{journal.venue_id}/Paper{submission.number}/-/Contact_Action_Editor'
    try:
        contact_invitation = client.get_invitation(contact_action_editor_id)
    except Exception as error:
        print(f'Could not load {contact_action_editor_id} to refresh reviewer comment signatures: {error}')
        return
    try:
        latest_reviewers_group = client.get_group(journal.get_reviewers_id(number=submission.number))
    except Exception as error:
        print(f'Could not load reviewer group for {contact_action_editor_id}: {error}')
        return
    reviewer_signature_by_member, _tail_by_anon = get_paper_reviewer_maps(latest_reviewers_group)
    active_assignment_tails = active_reviewer_assignment_tails(client, journal, submission)
    signature_items = [
        {'value': reviewer_signature_by_member[member], 'optional': True}
        for member in active_assignment_tails
        if reviewer_signature_by_member.get(member)
    ]
    if not isinstance(contact_invitation.edit, dict):
        contact_invitation.edit = {}
    contact_invitation.edit['signatures'] = {'param': {'items': signature_items}}
    contact_invitation.process = f'''def process(client, edit, invitation):
    journal = openreview.journal.JournalRequest.get_journal(client, "{journal.request_form_id}")
    note = client.get_note(edit.note.id)
    submission = client.get_note(note.forum)
    reviewer_signature = note.signatures[0]
    paper_reviewers_group = client.get_group(journal.get_reviewers_id(number=submission.number))
    assigned_reviewer_signatures = set(paper_reviewers_group.anon_members or [])
    if reviewer_signature not in assigned_reviewer_signatures:
        raise openreview.OpenReviewException('Only an assigned anonymous reviewer can contact the Action Editor.')
    required_readers = [
        journal.get_action_editors_id(number=submission.number),
        journal.get_editors_in_chief_id(),
        f'{{journal.venue_id}}/Editors_In_Chief',
        reviewer_signature
    ]
    missing_required_readers = [reader for reader in required_readers if reader not in (note.readers or [])]
    if missing_required_readers:
        raise openreview.OpenReviewException('Reviewer note is missing required paper-note readers.')
    ae_group = client.get_group(journal.get_action_editors_id())
    template = ae_group.content.get('reviewer_contact_email_template_script', {{}}).get('value')
    if not template:
        return
    contact_title = note.content.get('title', {{}}).get('value', 'Reviewer note about changes')
    contact_message = note.content.get('message', {{}}).get('value', '')
    client.post_message(
        invitation=journal.get_meta_invitation_id(),
        recipients=[journal.get_action_editors_id(number=submission.number)],
        subject=f"[{{journal.short_name}}] Reviewer note for Action Editor on paper {{submission.number}}: {{submission.content['title']['value']}}",
        message=template.format(
            short_name=journal.short_name,
            submission_number=submission.number,
            submission_title=submission.content['title']['value'],
            contact_title=contact_title,
            contact_message=contact_message,
            reviewer_signature=reviewer_signature,
            paper_url=f'{{SITE_URL}}/forum?id={{submission.id}}',
            contact_info=journal.contact_info
        ),
        replyTo=journal.contact_info,
        signature=journal.venue_id,
        sender=journal.get_message_sender()
    )
'''
    client.post_invitation_edit(
        invitations=journal.get_meta_invitation_id(),
        signatures=[journal.venue_id],
        invitation=contact_invitation,
        replacement=True
    )


def refresh_paper_reviewer_sync_surfaces(client, journal, submission):
    refresh_review_signature_choices(client, journal, submission)
    refresh_contact_action_editor_signature_choices(client, journal, submission)
    refresh_editorial_comment_reader_items(client, journal, submission)
    status_namespace = {'openreview': openreview, 'datetime': datetime}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/status/paper_status_refresh.py}}", status_namespace)
    status_namespace['refresh_paper_status_note'](client, journal, submission)


def ensure_paper_reviewer_anonids(client, journal, paper_reviewers_group):
    if paper_reviewers_group.anonids:
        return paper_reviewers_group
    print(f'Enable anonymous reviewer ids for {paper_reviewers_group.id}')
    client.post_group_edit(
        invitation=journal.get_meta_invitation_id(),
        signatures=[journal.venue_id],
        readers=[journal.venue_id],
        writers=[journal.venue_id],
        group=openreview.api.Group(
            id=paper_reviewers_group.id,
            anonids=True
        )
    )
    return client.get_group(paper_reviewers_group.id)


def sync_add_paper_reviewer(client, journal, submission, reviewer_id):
    paper_reviewers_group = client.get_group(journal.get_reviewers_id(number=submission.number))
    paper_reviewers_group = ensure_paper_reviewer_anonids(client, journal, paper_reviewers_group)
    changed = reviewer_id not in (paper_reviewers_group.members or [])
    if changed:
        print(f'Add member {reviewer_id} to {paper_reviewers_group.id}')
        client.add_members_to_group(paper_reviewers_group.id, reviewer_id)
    refresh_paper_reviewer_sync_surfaces(client, journal, submission)
    return changed


def sync_remove_paper_reviewer(client, journal, submission, reviewer_id):
    paper_reviewers_group = client.get_group(journal.get_reviewers_id(number=submission.number))
    changed = reviewer_id in (paper_reviewers_group.members or [])
    if changed:
        print(f'Remove member {reviewer_id} from {paper_reviewers_group.id}')
        client.remove_members_from_group(paper_reviewers_group.id, reviewer_id)
    refresh_paper_reviewer_sync_surfaces(client, journal, submission)
    return changed
