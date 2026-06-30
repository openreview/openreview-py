ACTION_EDITOR_ANONYMITY_ENABLED = "{{AE_ANONYMITY_JSON}}" != "false"


def resolve_active_action_editor_signature(client, journal, note, paper_action_editor_group):
    if not ACTION_EDITOR_ANONYMITY_ENABLED:
        return journal.get_action_editors_id(number=note.number)
    current_action_editors = set(paper_action_editor_group.members or [])
    action_editor_signature_groups = []
    for group in client.get_groups(prefix=f'{journal.venue_id}/Paper{note.number}/Action_Editor_'):
        if group.ddate:
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

    raise openreview.OpenReviewException(
        f'Expected exactly one active action editor signature for Paper{note.number}.'
    )


def paper_editorial_action_signatures(journal, fixed_action_editor_signature):
    if not fixed_action_editor_signature:
        raise openreview.OpenReviewException('Expected an assigned action editor signature.')
    return [fixed_action_editor_signature]


def paper_editorial_signature_items(journal, fixed_action_editor_signature):
    return [
        {'value': signature, 'optional': True}
        for signature in paper_editorial_action_signatures(journal, fixed_action_editor_signature)
    ]
