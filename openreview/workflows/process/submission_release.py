def process(client, invitation):

    import re
    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    short_name = domain.content['subtitle']['value']

    submission_venue_id = domain.content['submission_venue_id']['value']
    article_endorsement_id = domain.content['article_endorsement_id']['value']
    submission_name = domain.content['submission_name']['value']
    decision_name = domain.content.get('decision_name', {}).get('value')
    rejected_venue_id = domain.content['rejected_venue_id']['value']
    decision_field_name = domain.content.get('decision_field_name', {}).get('value', 'decision')
    decision_invitation = client.get_invitation(f'{venue_id}/-/{decision_name}')
    accept_options = decision_invitation.content.get('accept_decision_options', {}).get('value')
    meta_invitation_id = domain.content['meta_invitation_id']['value']
    source = invitation.content.get('source', {}).get('value', 'all_submissions') if invitation.content else False

    now = openreview.tools.datetime_millis(datetime.datetime.now())
    cdate = invitation.cdate

    if cdate > now:
        ## invitation is in the future, do not process
        print('invitation is not yet active', cdate)
        return

    def get_all_notes():
        submissions = client.get_all_notes(content={ 'venueid': submission_venue_id }, sort='number:asc', details='directReplies')
        if not submissions:
            submissions = client.get_all_notes(content={ 'venueid': ','.join([venue_id, rejected_venue_id]) }, sort='number:asc', details='directReplies')

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

        if note_accepted or source == 'all_submissions':
            client.post_note_edit(
                invitation=invitation.id,
                note=updated_note,
                signatures=[venue_id]
            )
        elif not note_accepted:
            client.post_note_edit(
                invitation=meta_invitation_id,
                signatures=[venue_id],
                note=openreview.api.Note(
                    id=submission.id,
                    content={
                        'venueid': {
                            'value': rejected_venue_id
                        },
                        'venue': {
                            'value': venue
                        }
                    }
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

    print(f'{len(submissions)} submissions updated successfully')

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