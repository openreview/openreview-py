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
    decision_name = domain.content.get('decision_name', {}).get('value', 'Decision')
    decision_field_name = domain.content.get('decision_field_name', {}).get('value', 'decision')
    decision_invitation = client.get_invitation(f'{venue_id}/-/{decision_name}')
    accept_options = decision_invitation.content.get('accept_decision_options', {}).get('value')
    meta_invitation_id = domain.content['meta_invitation_id']['value']
    decision_option = invitation.get_content_value('decision_option')
    release_accepted = openreview.tools.is_accept_decision(decision_option, accept_options)

    # The authors/authorids readers are defined in the invitation content schema: a readers
    # constant, or the escaped delete { 'const': { 'delete': True } } that the API stamps as
    # { 'delete': True } on every note edit. The process only uses the schema to build the
    # bibtex accordingly.
    authors_readers_schema = invitation.edit.get('note', {}).get('content', {}).get('authors', {}).get('readers')
    reveal_authors = authors_readers_schema == { 'const': { 'delete': True } }

    def edit_submission(submission_tuple):
        submission, decision = submission_tuple
        decision_value = decision[0].content[decision_field_name]['value']
        note_accepted = release_accepted

        # The authors/authorids readers are not posted here: they are stamped by the API
        # from the constants defined in the invitation content schema. The process only
        # posts the values that cannot be defined as invitation constants.
        updated_content = {
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
                content=updated_content,
                odate=now if (public and submission.odate is None) else None
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
        print(f'No submissions were updated since there are no "{decision_option}" submissions')
        return
    
    openreview.tools.concurrent_requests(edit_submission, filtered_submissions, desc='post_submission_edit')

    print(f'{len(filtered_submissions)} "{decision_option}" submissions updated successfully')

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