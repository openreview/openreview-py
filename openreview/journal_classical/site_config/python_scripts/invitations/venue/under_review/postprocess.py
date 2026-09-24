def process(client, edit, invitation):
    # JMLR delta: Journal creates the native browser; add contextual redirects only.
    journal = openreview.journal.JournalRequest.get_journal(
        client, "{{PROD_JOURNAL_ID}}"
    )
    submission = client.get_note(edit.note.id)
    try:
        prepare_previous_submission_reviewer_redirects(client, journal, submission)
    except Exception as error:
        print(
            f'Previous-reviewer redirect preparation failed for Paper{submission.number}: '
            f'{type(error).__name__}'
        )


# OpenReview detects the postprocess language from its first executable token.
# Keep the Python entrypoint above the embedded helper definitions.
# {{PYTHON_SCRIPT_FILE:invitations/venue/under_review/previous_submission_reviewer_redirects.py}}
