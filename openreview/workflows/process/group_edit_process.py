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

    def get_children_notes():
        source = invitation.content.get('source', {}).get('value', 'all_submissions') if invitation.content else 'all_submissions'
        source_submissions = client.get_all_notes(content={ 'venueid': submission_venue_id }, sort='number:asc')
        
        if source == 'all_submissions':
            return source_submissions
        if source == 'flagged_for_ethics_review':
            children_notes = [s for s in source_submissions if s.content.get('flagged_for_ethics_review', {}).get('value', False)]
            return children_notes

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
    submissions = get_children_notes()
    print(f'update {len(submissions)} submissions')
    openreview.tools.concurrent_requests(post_group_edit, submissions, desc='post_group_edit')    