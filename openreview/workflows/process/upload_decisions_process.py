def process(client, invitation):

    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    support_user = invitation.invitations[0].split('Template')[0] + 'Support'

    decision_csv = invitation.get_content_value('decision_CSV')
    upload_date = invitation.get_content_value('upload_date')
    status_invitation_id = domain.get_content_value('status_invitation_id')

    cdate = invitation.cdate

    now = openreview.tools.datetime_millis(datetime.datetime.utcnow())
    if cdate > now:
        ## invitation is in the future, do not process
        print('invitation is not yet active', cdate)
        return

    if not decision_csv:
        if status_invitation_id:
            # post status to request form
            client.post_note_edit(
                invitation=status_invitation_id,
                signatures=[venue_id],
                note=openreview.api.Note(
                    signatures=[venue_id],
                    content={
                        'title': { 'value': 'Decision Upload Failed' },
                        'comment': { 'value': f'The process "{invitation.id.split("/")[-1].replace("_", " ").title()}" was scheduled to run, but we found no valid decision CSV to upload. Please select a valid file and re-schedule this process to run at a later time.' }
                    }
                )
            )
        return
    
    decisions_file = client.get_attachment(field_name='decision_CSV', invitation_id=invitation.id)
    
    venue = openreview.helpers.get_venue(client, venue_id, support_user)

    results, errors = venue.post_decisions(
        decisions_file=decisions_file
    )

    print(f'{len(results)} decisions posted')

    if errors:
        print(errors)