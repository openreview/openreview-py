def process(client, invitation):

    import re
    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    title = domain.content['title']['value']
    short_name = domain.content['subtitle']['value']

    now = openreview.tools.datetime_millis(datetime.datetime.now())
    cdate = invitation.cdate

    if cdate > now:
        ## invitation is in the future, do not process
        print('invitation is not yet active', cdate)
        return

    submission_id = domain.content['submission_id']['value']
    article_endorsement_id = domain.content['article_endorsement_id']['value']
    submission_name = domain.content['submission_name']['value']
    authors_name = domain.content['authors_name']['value']
    decision_name = domain.content.get('decision_name', {}).get('value', 'Decision')
    rejected_venue_id = domain.content['rejected_venue_id']['value']
    decision_field_name = domain.content.get('decision_field_name', {}).get('value', 'decision')
    decision_invitation = client.get_invitation(f'{venue_id}/-/{decision_name}')
    accept_options = decision_invitation.content.get('accept_decision_options', {}).get('value')
    meta_invitation_id = domain.content['meta_invitation_id']['value']
    decision_option = invitation.get_content_value('decision_option')
    release_accepted = True if decision_option == 'Accepted' else False
    status_invitation_id = domain.get_content_value('status_invitation_id')
    request_form_id = domain.get_content_value('request_form_id')

    support_user = invitation.invitations[0].split('Template')[0] + 'Support'

    reveal_authors = invitation.get_content_value('reveal_author_identities')
    if reveal_authors is None:
        # post status to request form
        client.post_note_edit(
            invitation=status_invitation_id,
            signatures=[venue_id],
            readers=[venue_id, support_user],
            note=openreview.api.Note(
                forum=request_form_id,
                signatures=[venue_id],
                content={
                    'title': { 'value': f'{decision_option} Submission Release Failed' },
                    'comment': { 'value': f'The process "{invitation.id.split("/")[-1].replace("_", " ")}" was scheduled to run, but we found no valid selection for whether or not to release author names. Please re-schedule this process to run at a later time and then select whether author names should be released.\n1. To re-schedule this process for a later time, go to the [workflow timeline UI](https://openreview.net/group/edit?={venue_id}), find and expand the "Create {invitation.id.split("/-/")[-1].replace("_", " ")}" invitation, and click on "Edit" next to "Dates". Set the activation date to a later time and click "Submit".\n2. Once the process has been re-scheduled, click "Edit" next to the "Readers" invitation, select whether or not to release author names to the submission readers (and update submission readers if needed) and click "Submit".\n\nIf you would like this process to run now, you can skip step 1 and simply select whether or not to release author names. Once you have made your selection, click "Submit" and the process will automatically be scheduled to run shortly.' }
                }
            )
        )
        return

    def edit_submission(submission_tuple):
        submission, decision = submission_tuple
        decision_value = decision[0].content[decision_field_name]['value']
        note_accepted = release_accepted

        venue = openreview.tools.decision_to_venue(short_name, decision_value, accept_options)

        note_content = {
            'authors': {
                'readers': { 'delete': True } if reveal_authors else [venue_id, f'{venue_id}/{submission_name}{submission.number}/{authors_name}']
            },
            'authorids': {
                'readers': { 'delete': True } if reveal_authors else [venue_id, f'{venue_id}/{submission_name}{submission.number}/{authors_name}']
            },
            'venueid': {
                'value': venue_id if note_accepted else rejected_venue_id
            },
            'venue': {
                'value': venue
            },
            '_bibtex': {
                'value': openreview.tools.generate_bibtex(
                    note=submission,
                    venue_fullname=title,
                    year=str(datetime.datetime.now().year),
                    url_forum=submission.forum,
                    paper_status='accepted' if note_accepted else 'rejected',
                    anonymous=not reveal_authors
                )
            }
        }

        public = invitation.edit['note']['readers'] == ['everyone']

        client.post_note_edit(
            invitation=invitation.id,
            signatures=[venue_id],
            note=openreview.api.Note(
                id=submission.id,
                content=note_content,
                odate=now if (public and submission.odate is None) else None,
                pdate=now if (note_accepted and submission.pdate is None) else None
            )
        )

        if note_accepted:
            client.post_tag(openreview.api.Tag(
                invitation=article_endorsement_id,
                signature=venue_id,
                forum=submission.id,
                note=submission.id,
                label=re.sub(r'[()\W]+', '', decision_value.replace('Accept', ''))
            ))

    ## Release the submissions to specified readers
    all_submissions = client.get_all_notes(invitation=submission_id, sort='number:asc', details='directReplies', domain=venue_id)

    filtered_submissions = []
    for submission in all_submissions:
        if openreview.tools.should_match_invitation_source(client, invitation, submission, domain=domain):
            filtered_submissions.append((submission, [openreview.api.Note.from_json(reply) for reply in submission.details['directReplies'] if f'{venue_id}/{submission_name}{submission.number}/-/{decision_name}' in reply['invitations']]))

    print(f'{len(filtered_submissions)} out of {len(all_submissions)} submissions matched the source criteria and will be released')

    if not filtered_submissions:
        print(f'No submissions were updated since there are no {decision_option.lower()} submissions')
        return
    
    openreview.tools.concurrent_requests(edit_submission, filtered_submissions, desc='post_submission_edit')

    print(f'{len(filtered_submissions)} submissions updated successfully')

    # update the decision heading map
    decision_options = decision_invitation.content.get('decision_options', {}).get('value')
    decision_heading_map = { openreview.tools.decision_to_venue(short_name, o):o for o in decision_options}

    client.post_group_edit(
        invitation=meta_invitation_id,
        signatures=[venue_id],
        group=openreview.api.Group(
            id=venue_id,
            content = {
                'decision_heading_map': {
                    'value': decision_heading_map
                }
            }
        )
    )