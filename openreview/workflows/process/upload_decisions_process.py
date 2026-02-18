def process(client, invitation):

    now = openreview.tools.datetime_millis(datetime.datetime.utcnow())
    cdate = invitation.cdate

    if cdate > now:
        ## invitation is in the future, do not process
        print('invitation is not yet active', cdate)
        return

    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    status_invitation_id = domain.get_content_value('status_invitation_id')

    support_user = invitation.invitations[0].split('Template')[0] + 'Support'

    decision_csv = invitation.get_content_value('decision_CSV')
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
                        'comment': { 'value': f'The process "{invitation.id.split("/")[-1].replace("_", " ")}" was scheduled to run, but we found no valid CSV file. Please re-schedule this process to run at a later time and then upload a CSV file with decisions.\n1. To re-schedule this process for a later time, go to the [workflow timeline UI](https://openreview.net/group/edit?={venue_id}), find and expand the "Create {invitation.id.split("/-/")[-1].replace("_", " ")}" invitation, and click on "Edit" next to "Dates". Set the activation date to a later time and click "Submit".\n2. Once the process has been re-scheduled, click "Edit" next to the "Decision CSV" invitation, upload a valid CSV file with decisions and click "Submit".\n\nIf you would like this process to run now, you can skip step 1 and just upload a valid CSV file. Once you have uploaded the file, click "Submit" and the process will automatically be scheduled to run shortly.' }
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