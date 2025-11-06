def process(client, edit, invitation):

    journal = openreview.journal.Journal()

    submission = client.get_note(edit.note.id)
    submission_edits = client.get_note_edits(note_id=submission.id, sort='tcdate:asc')

    # run post-process only if this is the first edit of the submission
    if edit.id != submission_edits[0].id:
        print('Submission edited, exit')
        return
    
    # check if submission contains blocked author
    blocked_authors_group_id = journal.get_blocked_authors_id()

    blocked_authors_group = openreview.tools.get_group(client, blocked_authors_group_id)
    if blocked_authors_group and blocked_authors_group.members:
        authors = submission.content.get('authorids', {}).get('value', [])
        blocked_authors = []
        for author in authors:
            if client.get_groups(id=blocked_authors_group_id, member=author):
                blocked_authors.append(author)

        if blocked_authors:
            client.post_message(
                invitation=journal.get_meta_invitation_id(),
                recipients=[journal.get_editors_in_chief_id()],
                subject=f'''[{journal.short_name}] Submission by a blocked author received, titled {submission.content['title']['value']}''',
                message=f'''Hi {{{{fullname}}}},

The following authors are blocked from submitting to {journal.short_name}:

{', '.join(blocked_authors)}

Please review their submission and take appropriate action.
Link: https://openreview.net/forum?id={submission.id}
'''
            )
    