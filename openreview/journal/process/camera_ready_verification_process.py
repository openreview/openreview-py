def process(client, edit, invitation):

    journal = openreview.journal.Journal()
    venue_id = journal.venue_id

    ## On update or delete return
    note = client.get_note(edit.note.id)
    if note.tcdate != note.tmdate:
        return

    submission = client.get_note(note.forum)
    decisions = client.get_notes(invitation=journal.get_ae_decision_id(number=submission.number))

    if not decisions:
        return

    decision = decisions[0]
    certifications = decision.content.get('certifications', {}).get('value', [])
    expert_reviewers = []

    if journal.get_certifications():
        if journal.has_expert_reviewers():
            expert_reviewer_ceritification = False
            authorids = submission.content['authorids']['value']
            print('check if an author is an expert reviewer')
            for authorid in authorids:
                print('checking', authorid)
                if client.get_groups(member=authorid, id=journal.get_expert_reviewers_id()) and not expert_reviewer_ceritification:
                    print('append expert reviewer certification')
                    certifications.append(journal.get_expert_reviewer_certification())
                    expert_reviewers.append(authorid)
                    expert_reviewer_ceritification = True

    content= {
        '_bibtex': {
            'value': journal.get_bibtex(submission, journal.accepted_venue_id, certifications=certifications)
        }
    }

    if certifications:
        content['certifications'] = { 'value': certifications }

    if expert_reviewers:
        content['expert_reviewers'] = { 'value': expert_reviewers }

    acceptance_note = client.post_note_edit(invitation=journal.get_accepted_id(),
                        signatures=[venue_id],
                        note=openreview.api.Note(id=submission.id,
                            pdate = openreview.tools.datetime_millis(datetime.datetime.utcnow()),
                            content= content
                        )
                    )

    ## Send email to Authors
    print('Send email to Authors')
    client.post_message(
        invitation=journal.get_meta_invitation_id(),
        recipients=[journal.get_authors_id(number=submission.number)],
        subject=f'''[{journal.short_name}] Camera ready version accepted for your {journal.short_name} submission {submission.number}: {submission.content['title']['value']}''',
        message=f'''Hi {{{{fullname}}}},

This is to inform you that your submitted camera ready version of your paper {submission.number}: {submission.content['title']['value']} has been verified and confirmed by the Action Editor.

We thank you again for your contribution to {journal.short_name} and congratulate you for your successful submission!

The {journal.short_name} Editors-in-Chief
''',
        replyTo=journal.contact_info, 
        signature=journal.venue_id,
        sender=journal.get_message_sender()
    )
