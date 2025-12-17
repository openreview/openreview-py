def process(client, invitation):

    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    submission_venue_id = domain.content['submission_venue_id']['value']
    venue_name = domain.content['title']['value']
    meta_invitation_id = domain.content['meta_invitation_id']['value']
    program_chairs_id = domain.content['program_chairs_id']['value']
    authors_name = domain.content['authors_name']['value']
    submission_name = domain.content['submission_name']['value']
    reviewers_name = domain.content['reviewers_name']['value']
    reviewers_submitted_name = domain.content['reviewers_submitted_name']['value']
    area_chairs_name = domain.content['area_chairs_name']['value']
    senior_area_chairs_name = domain.content['senior_area_chairs_name']['value']


    client_v1=openreview.Client(
        baseurl=openreview.tools.get_base_urls(client)[0],
        token=client.token
    )

    now = openreview.tools.datetime_millis(datetime.datetime.now())
    cdate = invitation.cdate

    if cdate > now:
        ## invitation is in the future, do not process
        print('invitation is not yet active', cdate)
        return

    def post_submission_edit(submission):

        updated_note = openreview.api.Note(
            id=submission.id,
            odate = now,
            content = {
                '_bibtex': {
                    'value': openreview.tools.generate_bibtex(
                        note=submission,
                        venue_fullname=venue_name,
                        year=str(datetime.datetime.now().year),
                        url_forum=submission.forum,
                        paper_status='under review',
                        anonymous=True
                    )
                }                
            }
        )

        client.post_note_edit(
            invitation=invitation.id,
            note=updated_note,
            signatures=[venue_id]
        )

        paper_link = submission.content.get('previous_URL', {}).get('value')
        wants_new_reviewers = submission.content['reassignment_request_reviewers']['value'].startswith('Yes')
        # If previous submission, change reader set to include previous reviewers submitted group
        if paper_link:
            content = None
            paper_forum = paper_link.split('?id=')[-1]
            arr_submission_v1 = openreview.tools.get_note(client_v1, paper_forum)
            arr_submission_v2 = openreview.tools.get_note(client, paper_forum)
            append = [ f"{venue_id}/{submission_name}{submission.number}/{reviewers_name}/{reviewers_submitted_name}" ]
            remove = [ f"{venue_id}/{submission_name}{submission.number}/{reviewers_name}" ]
            
            if arr_submission_v1:
                v1_domain = arr_submission_v1.invitation.split('/-/')[0]
                if not wants_new_reviewers:
                    append.append(f"{v1_domain}/Paper{arr_submission_v1.number}/{reviewers_name}/{reviewers_submitted_name}")

                content = {
                    'explanation_of_revisions_PDF': {
                        'readers': {
                            'append': append,
                            'remove': remove
                        }
                    }
                }
            if arr_submission_v2:
                v2_domain = arr_submission_v2.domain
                if not wants_new_reviewers:
                    append.append(f"{v2_domain}/{submission_name}{arr_submission_v2.number}/{reviewers_name}/{reviewers_submitted_name}")
                
                content = {
                    'explanation_of_revisions_PDF': {
                        'readers': {
                            'append': append,
                            'remove': remove
                        }
                    }
                }

            if content is not None:
                client.post_note_edit(
                    invitation=meta_invitation_id,
                    readers=[venue_id],
                    writers=[venue_id],
                    signatures=[venue_id],
                    note=openreview.api.Note(
                        id=submission.id,
                        content=content
                    )
                )
    
    ## Release the submissions to the public when the value for preprint is yes
    submissions = [s for s in client.get_all_notes(content= { 'venueid': submission_venue_id }) if s.content.get('preprint', {}).get('value') == 'yes']
    print(f'update {len(submissions)} submissions')
    openreview.tools.concurrent_requests(post_submission_edit, submissions, desc='post_submission_edit')    