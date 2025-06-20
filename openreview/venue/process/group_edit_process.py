def process(client, invitation):

    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    submission_venue_id = domain.content['submission_venue_id']['value']

    now = openreview.tools.datetime_millis(datetime.datetime.now())
    cdate = invitation.cdate

    if cdate > now:
        ## invitation is in the future, do not process
        print('invitation is not yet active', cdate)
        return    

    def get_children_notes():
        source = openreview.tools.get_invitation_source(invitation, domain)

        ## TODO: use tools.should_match_invitation_source when "all_submissions" is removed
        def filter_by_source(source):

            venueids = source.get('venueid', [submission_venue_id]) ## we should always have a venueid
            source_submissions = client.get_all_notes(content={ 'venueid': ','.join([venueids] if isinstance(venueids, str) else venueids) }, sort='number:asc', details='replies')

            if 'readers' in source:
                source_submissions = [s for s in source_submissions if set(source['readers']).issubset(set(s.readers))]

            if 'content' in source:
                for key, value in source.get('content', {}).items():
                    source_submissions = [s for s in source_submissions if value == s.content.get(key, {}).get('value')]

            return source_submissions

        return filter_by_source(source)        

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