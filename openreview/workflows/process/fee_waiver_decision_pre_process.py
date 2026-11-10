def process(client, edit, invitation):

    domain = client.get_group(invitation.domain)
    submission_name = domain.get_content_value('submission_name')
    request_name = invitation.get_content_value('request_name')

    request = client.get_note(edit.note.id)
    request_invitation_id = request.invitations[0]

    is_submission_invitation = request_invitation_id.startswith(f'{domain.id}/{submission_name}')
    is_request_invitation = request_invitation_id.endswith(f'/-/{request_name}')
    if not is_submission_invitation or not is_request_invitation:
        raise openreview.OpenReviewException(f'The note {request.id} is not a fee waiver request.')
