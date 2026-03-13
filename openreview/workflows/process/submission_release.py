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

    submission_venue_id = domain.content['submission_venue_id']['value']
    article_endorsement_id = domain.content['article_endorsement_id']['value']
    submission_name = domain.content['submission_name']['value']
    decision_name = domain.content.get('decision_name', {}).get('value')
    rejected_venue_id = domain.content['rejected_venue_id']['value']
    decision_field_name = domain.content.get('decision_field_name', {}).get('value', 'decision')
    decision_invitation = client.get_invitation(f'{venue_id}/-/{decision_name}')
    accept_options = decision_invitation.content.get('accept_decision_options', {}).get('value')
    meta_invitation_id = domain.content['meta_invitation_id']['value']
    status_invitation_id = domain.get_content_value('status_invitation_id')
    request_form_id = domain.get_content_value('request_form_id')

    support_user = invitation.invitations[0].split('Template')[0] + 'Support'

    source = invitation.get_content_value('source')
    if not source:
        # post status to request form
        client.post_note_edit(
            invitation=status_invitation_id,
            signatures=[venue_id],
            readers=[venue_id, support_user],
            note=openreview.api.Note(
                forum=request_form_id,
                signatures=[venue_id],
                content={
                    'title': { 'value': 'Submission Release Failed' },
                    'comment': { 'value': f'The process "{invitation.id.split("/")[-1].replace("_", " ")}" was scheduled to run, but we found no valid source submissions. Please re-schedule this process to run at a later time and then select which submissions to release to the public.\n1. To re-schedule this process for a later time, go to the [workflow timeline UI](https://openreview.net/group/edit?={venue_id}), find and expand the "Create {invitation.id.split("/-/")[-1].replace("_", " ")}" invitation, and click on "Edit" next to "Dates". Set the activation date to a later time and click "Submit".\n2. Once the process has been re-scheduled, click "Edit" next to the "Which Submissions" invitation, select which submissions to release to the public and click "Submit".\n\nIf you would like this process to run now, you can skip step 1 and simply select which submissions to release. Once you have selected the source, click "Submit" and the process will automatically be scheduled to run shortly.' }
                }
            )
        )
        return

    def get_all_notes():
        submissions = client.get_all_notes(content={ 'venueid': submission_venue_id }, sort='number:asc', details='directReplies', domain=venue_id)
        if not submissions:
            submissions = client.get_all_notes(content={ 'venueid': ','.join([venue_id, rejected_venue_id]) }, sort='number:asc', details='directReplies', domain=venue_id)

        return submissions

    def get_source_submission_tuples(all_submissions):
        source_submissions = [(submission, openreview.api.Note.from_json(reply)) for submission in all_submissions for reply in submission.details['directReplies'] if f'{venue_id}/{submission_name}{submission.number}/-/{decision_name}' in reply['invitations']]
        return source_submissions

    def edit_submission(submission_tuple):
        submission, decision = submission_tuple
        decision_value = decision.content[decision_field_name]['value'] if decision else None
        note_accepted = openreview.tools.is_accept_decision(decision_value, accept_options) if decision_value else False

        venue = openreview.tools.decision_to_venue(short_name, decision_value, accept_options)

        updated_note = openreview.api.Note(
            id=submission.id,
            content={
                'authors': {
                    'readers': { 'delete': True }
                },
                'authorids': {
                    'readers': { 'delete': True }
                },
                'venueid': {
                    'value': venue_id if note_accepted else rejected_venue_id
                },
                'venue': {
                    'value': venue
                }
            }
        )

        if submission.odate is None:
            updated_note.odate = now
        # only if note is accepted
        if submission.pdate is None and note_accepted:
            updated_note.pdate = now

        updated_note.content['_bibtex'] = {
            'value': openreview.tools.generate_bibtex(
                note=submission,
                venue_fullname=title,
                year=str(datetime.datetime.now().year),
                url_forum=submission.forum,
                paper_status = 'accepted' if note_accepted else 'rejected',
                anonymous=False
            )
        }            

        if note_accepted or source == 'all_submissions':
            client.post_note_edit(
                invitation=invitation.id,
                note=updated_note,
                signatures=[venue_id]
            )
        elif not note_accepted:
            note_content = {
                'venueid': {
                    'value': rejected_venue_id
                },
                'venue': {
                    'value': venue
                }
            }
            if submission.content.get('bibtex', {}).get('value'):
                note_content['_bibtex'] = {
                    'value': openreview.tools.generate_bibtex(
                        note=submission,
                        venue_fullname=title,
                        year=str(datetime.datetime.now().year),
                        url_forum=submission.forum,
                        paper_status = 'rejected',
                        anonymous=True
                    )
                }
            client.post_note_edit(
                invitation=meta_invitation_id,
                signatures=[venue_id],
                note=openreview.api.Note(
                    id=submission.id,
                    content=note_content
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

    ## Release the submissions to specified readers if venueid is still submission
    submissions = get_all_notes()
    source_submissions = get_source_submission_tuples(submissions)

    if not source_submissions:
        print('No submissions were updated since there are no active submissions')
        return
    
    print(f'update {len(submissions)} submissions')
    openreview.tools.concurrent_requests(edit_submission, source_submissions, desc='post_submission_edit')

    print(f'{len(source_submissions)} submissions updated successfully')

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