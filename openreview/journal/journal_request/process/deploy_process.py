def process(client, edit, invitation):

    SUPPORT_GROUP = ''

    journal = openreview.journal.JournalRequest.get_journal(client, edit.note.id, setup=True)
    journal_request = openreview.journal.JournalRequest(client, SUPPORT_GROUP)
    journal_request.setup_journal_group(edit.note.id)
    invitation_edit = journal_request.setup_comment_invitation(edit.note.id, journal.get_action_editors_id())
    journal_request.setup_recruitment_invitations(edit.note.id)
    journal_request.setup_recruitment_by_action_editors(edit.note.id)
    journal_request.setup_revision_invitation(edit.note.id)

    comment_invitation_id = invitation_edit['invitation']['id']
    baseurl = openreview.tools.get_site_url(client)

    # post comment to journal request
    client.post_note_edit(
        invitation = comment_invitation_id,
        signatures = [SUPPORT_GROUP],
        note = openreview.api.Note(
            forum = edit.note.id,
            replyto = edit.note.id,
            readers = [journal.venue_id, SUPPORT_GROUP],
            content = {
                'title': { 'value': 'Your journal is available in OpenReview' },
                'comment': { 'value': f'''
Hi Editors-in-Chief,

Thank you for choosing OpenReview to host your journal.

We have set up the journal based on the information that you provided here: {baseurl}/forum?id={edit.note.id}

You can use the following links to access the journal:
- **Journal home page:** {baseurl}/group?id={journal.venue_id}
    - This page is visible to the public. This is where authors will submit papers, and action editors and reviewers will access their consoles.
- **Journal Editors-in-Chief Console:** {baseurl}/group?id={journal.venue_id}/Editors_In_Chief
    - This page is visible only to Editors-in-Chief, and is where you can see all submissions as well as stats about your journal.
- **Journal Request Form:** {baseurl}/forum?id={edit.note.id}
    - This page is visible only to Editors-in-Chief and Action Editors. Use this page to configure your journal. This page is also used by Editors-in-Chief to recruit Action Editors and Reviewers and for Action Editors to recruit Reviewers.

Best,  
The OpenReview Team'''
                }
            }
        )
    )
