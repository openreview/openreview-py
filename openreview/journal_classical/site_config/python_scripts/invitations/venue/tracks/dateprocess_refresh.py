def process(client, invitation):
    journal = openreview.journal.JournalRequest.get_journal(client, "{{PROD_JOURNAL_ID}}")
    refresh_track_surfaces(client, journal, load_track_records(client))


exec(r'''{{PYTHON_SCRIPT_FILE:invitations/venue/tracks/registry.py}}''')
