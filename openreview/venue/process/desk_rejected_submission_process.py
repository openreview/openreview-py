def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    short_name = domain.content['subtitle']['value']
    desk_rejection_reversion_id = domain.content['desk_rejection_reversion_id']['value']
    desk_reject_expiration_id = domain.content['desk_reject_expiration_id']['value']
    desk_reject_committee = domain.content['desk_reject_committee']['value']
    desk_rejection_name = domain.content['desk_rejection_name']['value']
    submission_name = domain.content['submission_name']['value']
    authors_name = domain.content['authors_name']['value']
    reviewers_name = domain.content['reviewers_name']['value']
    area_chairs_name = domain.content.get('area_chairs_name', {}).get('value')
    senior_area_chairs_name = domain.content.get('senior_area_chairs_name', {}).get('value')
    reviewers_id = domain.content['reviewers_id']['value']
    area_chairs_id = domain.content.get('area_chairs_id', {}).get('value')
    senior_area_chairs_id = domain.content.get('senior_area_chairs_id', {}).get('value')
    program_chairs_id = domain.content['program_chairs_id']['value']

    submission = client.get_note(edit.note.id)
    paper_group_id=f'{venue_id}/{submission_name}{submission.number}'

    invitations = client.get_invitations(replyForum=submission.id, prefix=paper_group_id)

    now = openreview.tools.datetime_millis(datetime.datetime.utcnow())

    for invitation in invitations:
        print(f'Expiring invitation {invitation.id}')
        client.post_invitation_edit(
            invitations=desk_reject_expiration_id,
            invitation=openreview.api.Invitation(id=invitation.id,
                expdate=now
            )
        )

    desk_rejection_notes = client.get_notes(forum=submission.id, invitation=f'{paper_group_id}/-/{desk_rejection_name}')
    if desk_rejection_notes:
        print(f'Create desk-rejection reversion invitation')
        client.post_invitation_edit(
            invitations=desk_rejection_reversion_id,
            content={
                'noteId': {
                    'value': submission.id
                },
                'deskRejectionId': {
                    'value': desk_rejection_notes[0].id
                }
            }
        )

    print(f'Remove {paper_group_id}/{authors_name} from {venue_id}/{authors_name}')
    client.remove_members_from_group(f'{venue_id}/{authors_name}', f'{paper_group_id}/{authors_name}')

    recipients = [f'{paper_group_id}/{authors_name}']

    reviewers_paper_id = f'{paper_group_id}/{reviewers_name}'
    if reviewers_name and (reviewers_paper_id in submission.readers or reviewers_id in submission.readers or 'everyone' in submission.readers):
        if openreview.tools.get_group(client, reviewers_paper_id):
            recipients.append(reviewers_paper_id)

    area_chairs_paper_id = f'{paper_group_id}/{area_chairs_name}'
    if area_chairs_name and (area_chairs_paper_id in submission.readers or area_chairs_id in submission.readers or 'everyone' in submission.readers):
        if openreview.tools.get_group(client, area_chairs_paper_id):
            recipients.append(area_chairs_paper_id)

    senior_area_chairs_paper_id = f'{paper_group_id}/{senior_area_chairs_name}'
    if senior_area_chairs_name and (senior_area_chairs_paper_id in submission.readers or senior_area_chairs_id in submission.readers or 'everyone' in submission.readers):
        if openreview.tools.get_group(client, senior_area_chairs_paper_id):
            recipients.append(senior_area_chairs_paper_id)

    if program_chairs_id:
        recipients.append(program_chairs_id)

    email_subject = f'''[{short_name}]: Paper #{submission.number} desk-rejected by program chairs'''
    email_body = f'''The {short_name} paper "{submission.content.get('title', {}).get('value', '#'+str(submission.number))}" has been desk-rejected by the program chairs.

For more information, click here https://openreview.net/forum?id={submission.id}
'''

    client.post_message(email_subject, recipients, email_body)