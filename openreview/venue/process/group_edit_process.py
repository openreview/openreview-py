def process(client, invitation):

    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    submission_venue_id = domain.content['submission_venue_id']['value']

    now = openreview.tools.datetime_millis(datetime.datetime.utcnow())
    cdate = invitation.cdate

    if cdate > now:
        ## invitation is in the future, do not process
        print('invitation is not yet active', cdate)
        return    

    def post_group_edit(submission):

        client.post_group_edit(
            invitation=invitation.id,
            content={
                'noteId': { 'value': submission.id },
                'noteNumber': { 'value': submission.number },
            },
            group=openreview.api.Group()
        )
    
    ## Release the submissions to specified readers if venueid is still submission
    submissions = client.get_all_notes(content= { 'venueid': submission_venue_id })
    print(f'update {len(submissions)} submissions')
    openreview.tools.concurrent_requests(post_group_edit, submissions, desc='post_group_edit')    