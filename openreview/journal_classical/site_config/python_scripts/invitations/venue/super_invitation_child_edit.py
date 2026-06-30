ACTION_EDITOR_ANONYMITY_ENABLED = "{{AE_ANONYMITY_JSON}}" != "false"


def get_paper_super_invitation_child_edit_envelope(journal, invitation_id):
    envelope = {
        'readers': [journal.venue_id],
        'writers': [journal.venue_id],
        'signatures': [journal.venue_id]
    }
    if invitation_id in [
        journal.get_ae_decision_id(),
        journal.get_review_id(),
        journal.get_camera_ready_revision_id(),
        journal.get_camera_ready_verification_id()
    ]:
        envelope['readers'] = [journal.get_editors_in_chief_id()]
    return envelope


def post_paper_super_invitation_child_edit(client, journal, invitation_id, content, await_process=False):
    kwargs = {
        'invitations': invitation_id,
        'content': content,
        **get_paper_super_invitation_child_edit_envelope(journal, invitation_id)
    }
    if await_process:
        kwargs['await_process'] = True
    return client.post_invitation_edit(**kwargs)


def refresh_review_invitation(client, journal, note):
    duedate = journal.get_due_date(weeks=journal.get_review_period_length(note))
    return post_paper_super_invitation_child_edit(
        client,
        journal,
        journal.get_review_id(),
        {
            'noteId': {'value': note.id},
            'noteNumber': {'value': note.number},
            'duedate': {'value': openreview.tools.datetime_millis(duedate)}
        },
        await_process=True
    )


def refresh_decision_invitation_from_super(client, journal, note, cdate, duedate):
    edit = post_paper_super_invitation_child_edit(
        client,
        journal,
        journal.get_ae_decision_id(),
        {
            'noteId': {'value': note.id},
            'noteNumber': {'value': note.number},
            'cdate': {'value': openreview.tools.datetime_millis(cdate)},
            'duedate': {'value': openreview.tools.datetime_millis(duedate)}
        }
    )
    set_normal_decision_invitation_schema(client, journal, note, cdate, duedate)
    normalize_decision_invitation_signatures(client, journal, note)
    return edit


def post_decision_invitation_replacement(client, journal, decision_invitation):
    return client.post_invitation_edit(
        invitations=journal.get_meta_invitation_id(),
        readers=[journal.get_editors_in_chief_id()],
        writers=[journal.venue_id],
        signatures=[journal.venue_id],
        invitation=decision_invitation,
        replacement=True
    )


def resolve_assigned_action_editor_signature(client, journal, note):
    paper_action_editors_id = journal.get_action_editors_id(number=note.number)
    try:
        paper_action_editor_group = client.get_group(paper_action_editors_id)
    except Exception as error:
        print(f'Could not load paper Action Editors group for Paper{note.number}: {error}')
        return None

    current_action_editors = set(paper_action_editor_group.members or [])
    if not current_action_editors:
        return None
    if not ACTION_EDITOR_ANONYMITY_ENABLED:
        return paper_action_editors_id

    action_editor_signature_groups = []
    for group in client.get_groups(prefix=f'{journal.venue_id}/Paper{note.number}/Action_Editor_'):
        if getattr(group, 'ddate', None):
            continue
        if set(group.members or []).intersection(current_action_editors):
            action_editor_signature_groups.append(group)

    if len(action_editor_signature_groups) == 1:
        return action_editor_signature_groups[0].id

    venue_signed_groups = [
        group for group in action_editor_signature_groups
        if journal.venue_id in (group.signatures or [])
    ]
    if len(venue_signed_groups) == 1:
        return venue_signed_groups[0].id

    if action_editor_signature_groups:
        print(f'Could not resolve exactly one assigned anonymous action editor signature for Paper{note.number}.')
    return None


def set_normal_decision_invitation_schema(client, journal, note, cdate, duedate):
    decision_invitation_id = journal.get_ae_decision_id(number=note.number)
    try:
        decision_invitation = client.get_invitation(decision_invitation_id)
    except Exception as error:
        raise RuntimeError(f'Could not load decision invitation {decision_invitation_id} for schema refresh: {error}')

    paper_authors_id = journal.get_authors_id(number=note.number)
    paper_action_editors_id = journal.get_action_editors_id(number=note.number)
    paper_reviewers_id = journal.get_reviewers_id(number=note.number)
    assigned_action_editor_signature = resolve_assigned_action_editor_signature(client, journal, note)
    paper_authorids = [
        authorid for authorid in note.content.get('authorids', {}).get('value', [])
        if isinstance(authorid, str) and authorid
    ]
    author_nonreaders = [paper_authors_id] + paper_authorids
    editors_in_chief_id = journal.get_editors_in_chief_id()
    selected_signature_param = '$' + '{3/signatures}'

    decision_process_wrapper = "\n".join([
        "def process(client, edit, invitation):",
        "    script = None",
        "    for parent_invitation_id in invitation.invitations or []:",
        "        parent_invitation = client.get_invitation(parent_invitation_id)",
        "        parent_content = getattr(parent_invitation, 'content', {}) or {}",
        "        if 'process_script' in parent_content:",
        "            script = parent_content['process_script']['value']",
        "            break",
        "    if script is None:",
        "        raise openreview.OpenReviewException(f'Decision invitation {invitation.id} has no parent process_script.')",
        "    funcs = {",
        "        'openreview': openreview,",
        "        'datetime': datetime",
        "    }",
        "    exec(script, funcs)",
        "    funcs['process'](client, edit, invitation)",
    ])

    decision_invitation.invitations = [journal.get_ae_decision_id()]
    decision_invitation.cdate = openreview.tools.datetime_millis(cdate)
    decision_invitation.duedate = openreview.tools.datetime_millis(duedate)
    decision_invitation.ddate = None
    decision_invitation.expdate = None
    decision_invitees = [editors_in_chief_id, paper_action_editors_id]
    if assigned_action_editor_signature and assigned_action_editor_signature not in decision_invitees:
        decision_invitees.append(assigned_action_editor_signature)
    decision_invitation.invitees = decision_invitees
    decision_invitation.readers = list(decision_invitees)
    decision_invitation.nonreaders = author_nonreaders
    decision_invitation.writers = [journal.venue_id]
    decision_invitation.signatures = [journal.venue_id]
    decision_invitation.maxReplies = 1
    decision_invitation.minReplies = 1
    decision_invitation.edit = {
        'signatures': {
            'param': {
                'items': [
                    {
                        'value': editors_in_chief_id,
                        'optional': True
                    }
                ] + (
                    [
                        {
                            'value': assigned_action_editor_signature,
                            'optional': True
                        }
                    ]
                    if assigned_action_editor_signature
                    else [
                        {
                            'prefix': f'{journal.venue_id}/Paper{note.number}/Action_Editor_',
                            'optional': True
                        }
                    ]
                )
            }
        },
        'readers': [
            editors_in_chief_id,
            paper_action_editors_id
        ],
        'nonreaders': author_nonreaders,
        'writers': [
            editors_in_chief_id,
            paper_action_editors_id
        ],
        'note': {
            'forum': note.id,
            'replyto': note.id,
            'signatures': [
                selected_signature_param
            ],
            'readers': [
                editors_in_chief_id,
                paper_action_editors_id,
                paper_reviewers_id
            ],
            'nonreaders': author_nonreaders,
            'writers': [
                journal.venue_id
            ],
            'content': {
                'recommendation': {
                    'order': 1,
                    'value': {
                        'param': {
                            'type': 'string',
                            'enum': [
                                'Accept',
                                'Accept after minor revisions',
                                'Reject with encouragement to resubmit',
                                'Reject without resubmission'
                            ],
                            'input': 'radio'
                        }
                    },
                    'description': 'Please select the action editor decision for this work.'
                },
                'comment': {
                    'order': 2,
                    'description': 'AE Decision Comments. Provide details of the reasoning behind your decision. Also consider summarizing the discussion and recommendations of the reviewers for clarity. Reviewer recommendations are hidden from authors before review release and become visible when reviews are released. (max 200000 characters). Add formatting using Markdown and formulas using LaTeX.',
                    'value': {
                        'param': {
                            'type': 'string',
                            'maxLength': 200000,
                            'input': 'textarea',
                            'markdown': True,
                            'optional': True
                        }
                    }
                }
            }
        }
    }
    decision_invitation.preprocess = "{{PYTHON_SCRIPT_JSON:invitations/venue/decision/edit_preprocess.py}}"
    decision_invitation.process = decision_process_wrapper
    decision_invitation.dateprocesses = [
        {
            'dates': [
                '#{4/duedate} + 86400000',
                '#{4/duedate} + 604800000',
                '#{4/duedate} + 1209600000',
                '#{4/duedate} + 1814400000',
                '#{4/duedate} + 2419200000',
                '#{4/duedate} + 3024000000',
                '#{4/duedate} + 3628800000',
                '#{4/duedate} + 4233600000',
                '#{4/duedate} + 4838400000',
                '#{4/duedate} + 5443200000',
                '#{4/duedate} + 6048000000',
                '#{4/duedate} + 6652800000',
                '#{4/duedate} + 7257600000',
                '#{4/duedate} + 7862400000',
                '#{4/duedate} + 8467200000',
                '#{4/duedate} + 9072000000',
                '#{4/duedate} + 9676800000',
                '#{4/duedate} + 10281600000',
                '#{4/duedate} + 10886400000',
                '#{4/duedate} + 11491200000',
                '#{4/duedate} + 12096000000',
                '#{4/duedate} + 12700800000',
                '#{4/duedate} + 13305600000',
                '#{4/duedate} + 13910400000',
                '#{4/duedate} + 14515200000',
                '#{4/duedate} + 15120000000',
                '#{4/duedate} + 15724800000'
            ],
            'script': "{{PYTHON_SCRIPT_JSON:invitations/venue/decision/dateprocess_submit_decision_reminder.py}}"
        }
    ]
    post_decision_invitation_replacement(client, journal, decision_invitation)


def normalize_decision_invitation_signatures(client, journal, note):
    signature_namespace = {}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/anonymous_signature_helpers.py}}", signature_namespace)
    decision_invitation_id = journal.get_ae_decision_id(number=note.number)
    try:
        decision_invitation = client.get_invitation(decision_invitation_id)
    except Exception as error:
        raise RuntimeError(f'Could not load decision invitation {decision_invitation_id} for signature normalization: {error}')
    assigned_action_editor_signature = resolve_assigned_action_editor_signature(client, journal, note)
    if assigned_action_editor_signature:
        signature_namespace['apply_eic_or_assigned_action_editor_signatures'](
            decision_invitation,
            journal,
            assigned_action_editor_signature
        )
    else:
        signature_namespace['apply_eic_or_anonymous_action_editor_signatures'](decision_invitation, journal, note.number)
    try:
        post_decision_invitation_replacement(client, journal, decision_invitation)
    except Exception as error:
        raise RuntimeError(f'Could not normalize decision invitation signatures for Paper{note.number}: {error}')


def refresh_camera_ready_revision_invitation(client, journal, note, duedate):
    return post_paper_super_invitation_child_edit(
        client,
        journal,
        journal.get_camera_ready_revision_id(),
        {
            'noteId': {'value': note.id},
            'noteNumber': {'value': note.number},
            'duedate': {'value': openreview.tools.datetime_millis(duedate)}
        }
    )


def refresh_camera_ready_verification_invitation(client, journal, note, duedate):
    return post_paper_super_invitation_child_edit(
        client,
        journal,
        journal.get_camera_ready_verification_id(),
        {
            'noteId': {'value': note.id},
            'noteNumber': {'value': note.number},
            'duedate': {'value': openreview.tools.datetime_millis(duedate)}
        }
    )


def expire_invitation_with_deactivation(client, journal, invitation_id):
    try:
        client.get_invitation(invitation_id)
    except Exception:
        return

    now = openreview.tools.datetime_millis(datetime.datetime.now())
    client.post_invitation_edit(
        invitations=journal.get_meta_invitation_id(),
        signatures=[journal.venue_id],
        invitation=openreview.api.Invitation(
            id=invitation_id,
            signatures=[journal.venue_id],
            expdate=now,
            ddate=now
        ),
        replacement=True
    )


def setup_under_review_submission_with_eic_child_readers(client, journal, note):
    refresh_review_invitation(client, journal, note)
    journal.invitation_builder.set_note_solicit_review_invitation(note)
    journal.invitation_builder.release_submission_history(note)
    expire_invitation_with_deactivation(client, journal, journal.get_review_approval_id(note.number))
    paper_prefix = f'{journal.venue_id}/Paper{note.number}'
    expire_invitation_with_deactivation(client, journal, f'{paper_prefix}/-/Official_Recommendation_Enabling')
    expire_invitation_with_deactivation(client, journal, f'{paper_prefix}/-/Official_Recommendation')
    expire_invitation_with_deactivation(client, journal, journal.get_official_recommendation_enabling_id(note.number))
    expire_invitation_with_deactivation(client, journal, journal.get_reviewer_recommendation_id(note.number))
