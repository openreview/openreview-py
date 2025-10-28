def process(client, invitation):

    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    support_user = invitation.invitations[0].split('Template')[0] + 'Support'

    decision_csv = invitation.get_content_value('decision_CSV')
    upload_date = invitation.get_content_value('upload_date')

    cdate = invitation.cdate

    now = openreview.tools.datetime_millis(datetime.datetime.utcnow())
    if cdate > now:
        ## invitation is in the future, do not process
        print('invitation is not yet active', cdate)
        return

    if not upload_date:
        raise openreview.OpenReviewException('Select a valid date to upload paper decisions')

    if not decision_csv:
        # post comment to request form
        raise openreview.OpenReviewException('No decision CSV was uploaded')
    
    decisions_file = client.get_attachment(field_name='decision_CSV', invitation_id=invitation.id)
    
    venue = openreview.helpers.get_venue(client, venue_id, support_user)

    results, errors = venue.post_decisions(
        decisions_file=decisions_file
    )

    print(f'{len(results)} decisions posted')

    if errors:
        print(errors)