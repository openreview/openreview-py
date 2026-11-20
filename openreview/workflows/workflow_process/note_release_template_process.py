def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    meta_invitation_id = domain.content.get('meta_invitation_id', {}).get('value')

    stage_name = edit.content['name']['value']

    edit_invitations_builder = openreview.workflows.EditInvitationsBuilder(client, domain.id)
    review_release_invitation_id = f'{domain.id}/-/{stage_name}'

    edit_invitations_builder.set_review_release_reply_readers_invitation(review_release_invitation_id)
    preprocess_file = None
    if edit.content.get('stage_name', {}).get('value') == domain.get_content_value('decision_name', 'Decision'):
        preprocess_file = 'workflow_process/edit_decision_release_dates_preprocess.py'
    edit_invitations_builder.set_edit_dates_one_level_invitation(review_release_invitation_id, preprocess_file=preprocess_file)