def process(client, edit, invitation):

    journal = openreview.journal.Journal()

    venue_id = journal.venue_id
    now = openreview.tools.datetime_millis(datetime.datetime.now())

    submission = client.get_note(edit.note.forum)

    ## Delete the Desk_Rejected edit so the submission venueid, venue, readers and writers go back to their previous values
    submission_edits = client.get_note_edits(note_id=submission.id, invitation=journal.get_desk_rejected_id())
    for submission_edit in submission_edits:
        print(f'remove edit {submission_edit.id}')
        submission_edit.ddate = now
        client.post_edit(submission_edit)

    ## Delete the expiration edits posted by the desk rejection to reopen the paper invitations it closed
    reopened_invitation_ids = []
    expired_invitations = client.get_invitations(prefix=f'{venue_id}/{journal.submission_group_name}{submission.number}/.*', invitation=journal.get_desk_rejection_expiration_id(), expired=True, type='all')
    for expired_invitation in expired_invitations:
        invitation_edits = client.get_invitation_edits(invitation_id=expired_invitation.id, invitation=journal.get_desk_rejection_expiration_id())
        for invitation_edit in invitation_edits:
            print(f'remove edit {invitation_edit.id}')
            invitation_edit.ddate = now
            client.post_edit(invitation_edit)
        reopened_invitation_ids.append(expired_invitation.id)

    ## Count again the pending reviews discounted when the review invitation was expired
    if journal.get_review_id(number=submission.number) in reopened_invitation_ids:
        reviews = { r.signatures[0]: r for r in client.get_notes(invitation=journal.get_review_id(number=submission.number)) }
        reviewers = client.get_group(journal.get_reviewers_id(number=submission.number))
        for reviewer in reviewers.members:
            signatures_group = client.get_groups(prefix=journal.get_reviewers_id(number=submission.number, anon=True), member=reviewer)[0]
            if signatures_group.id not in reviews:
                pending_edges = client.get_edges(invitation=journal.get_reviewer_pending_review_id(), tail=reviewer)
                if pending_edges:
                    pending_edge = pending_edges[0]
                    pending_edge.weight += 1
                    client.post_edge(pending_edge)

    ## Send email to authors and action editors
    print('Send email to authors and action editors')
    client.post_message(
        invitation=journal.get_meta_invitation_id(),
        recipients=[journal.get_authors_id(number=submission.number), journal.get_action_editors_id(number=submission.number)],
        subject=f'''[{journal.short_name}] Desk rejection reverted for {journal.short_name} submission {submission.number}: {submission.content['title']['value']}''',
        message=f'''Hi {{{{fullname}}}},

The {journal.short_name} Editors-in-Chief have reverted the desk rejection of the {journal.short_name} submission "{submission.number}: {submission.content['title']['value']}". The submission has been restored to its previous status.

To view the Editors-in-Chief's comments, follow this link: https://openreview.net/forum?id={submission.id}&noteId={edit.note.id}

The {journal.short_name} Editors-in-Chief
''',
        replyTo=journal.contact_info,
        signature=venue_id,
        sender=journal.get_message_sender()
    )
