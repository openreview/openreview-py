def process(client, invitation):

    now = openreview.tools.datetime_millis(datetime.datetime.utcnow())
    cdate = invitation.cdate

    if cdate > now:
        ## invitation is in the future, do not process
        print('invitation is not yet active', cdate)
        return

    domain = client.get_group(invitation.domain)
    venue_id = domain.id

    support_user = invitation.invitations[0].split('Template')[0] + 'Support'

    decision_csv = invitation.get_content_value('decision_CSV')
    if not decision_csv:
        # log the failure so PCs can see it in the workflow timeline
        print('Decisions were not posted: no decision CSV was uploaded. Upload a CSV under "Decision CSV" to run this step.')
        return
    
    decisions_file = client.get_attachment(field_name='decision_CSV', invitation_id=invitation.id)
    
    venue = openreview.helpers.get_venue(client, venue_id, support_user)

    results, errors = venue.post_decisions(
        decisions_file=decisions_file
    )

    print(f'{len(results)} decisions posted')

    if errors:
        print(errors)