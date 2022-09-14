def process(client, edit, invitation):

    SUPPORT_GROUP = ''

    journal = openreview.journal.JournalRequest.get_journal(client, edit.note.id, setup=True)
    journal_request = openreview.journal.JournalRequest(client, SUPPORT_GROUP)
    journal_request.setup_journal_group(edit.note.id)
    journal_request.setup_comment_invitation(edit.note.id, journal.get_action_editors_id())
    journal_request.setup_recruitment_invitations(edit.note.id)
    journal_request.setup_recruitment_by_action_editors(edit.note.id)