def process(client, edit, invitation):

    ## re-run the journal setup to apply the updated request settings
    journal = openreview.journal.JournalRequest.get_journal(client, edit.note.id, setup=True)

    if journal:
        openreview.journal.JournalRequest(client, journal.get_support_group()).setup_recruitment_invitations(edit.note.id)
