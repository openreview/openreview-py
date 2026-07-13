ACTION_EDITOR_ANONYMITY_ENABLED = "{{AE_ANONYMITY_JSON}}" != "false"


def anonymous_action_editor_signature_prefix(journal, paper_number):
    return f'{journal.venue_id}/Paper{paper_number}/Action_Editor_'


def anonymous_reviewer_signature_prefix(journal, paper_number):
    return f'{journal.venue_id}/Paper{paper_number}/Reviewer_'


def eic_signature_item(journal):
    return {
        'value': journal.get_editors_in_chief_id(),
        'optional': True
    }


def anonymous_action_editor_signature_item(journal, paper_number):
    return {
        'prefix': anonymous_action_editor_signature_prefix(journal, paper_number),
        'optional': True
    }


def action_editor_signature_item(journal, paper_number):
    if ACTION_EDITOR_ANONYMITY_ENABLED:
        return anonymous_action_editor_signature_item(journal, paper_number)
    return {
        'value': journal.get_action_editors_id(number=paper_number),
        'optional': True
    }


def assigned_action_editor_signature_item(signature):
    return {
        'value': signature,
        'optional': True
    }


def anonymous_reviewer_signature_item(journal, paper_number):
    return {
        'prefix': anonymous_reviewer_signature_prefix(journal, paper_number),
        'optional': True
    }


def selectable_signature_schema(items):
    return {
        'param': {
            'items': items
        }
    }


def eic_or_anonymous_action_editor_signature_schema(journal, paper_number):
    return selectable_signature_schema([
        eic_signature_item(journal),
        action_editor_signature_item(journal, paper_number)
    ])


def eic_or_assigned_action_editor_signature_schema(journal, signature):
    return selectable_signature_schema([
        eic_signature_item(journal),
        assigned_action_editor_signature_item(signature)
    ])


def anonymous_action_editor_signature_schema(journal, paper_number):
    return selectable_signature_schema([
        action_editor_signature_item(journal, paper_number)
    ])


def anonymous_reviewer_signature_schema(journal, paper_number):
    return selectable_signature_schema([
        anonymous_reviewer_signature_item(journal, paper_number)
    ])


def apply_eic_or_anonymous_action_editor_signatures(invitation, journal, paper_number):
    if not isinstance(invitation.edit, dict):
        invitation.edit = {}
    invitation.signatures = [journal.venue_id]
    invitation.edit['signatures'] = eic_or_anonymous_action_editor_signature_schema(journal, paper_number)
    return invitation


def apply_eic_or_assigned_action_editor_signatures(invitation, journal, signature):
    if not isinstance(invitation.edit, dict):
        invitation.edit = {}
    invitation.signatures = [journal.venue_id]
    invitation.edit['signatures'] = eic_or_assigned_action_editor_signature_schema(journal, signature)
    return invitation


def apply_anonymous_action_editor_signatures(invitation, journal, paper_number):
    if not isinstance(invitation.edit, dict):
        invitation.edit = {}
    invitation.edit['signatures'] = anonymous_action_editor_signature_schema(journal, paper_number)
    return invitation
