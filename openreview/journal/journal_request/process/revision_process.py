def process(client, edit, invitation):

    ## re-run the journal setup to apply the updated request settings
    openreview.journal.JournalRequest.get_journal(client, edit.note.id, setup=True)
