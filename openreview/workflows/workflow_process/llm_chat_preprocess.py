def process(client, edit, invitation):

    THINKING_MESSAGE = 'Thinking...'
    # a question still waiting for its answer after this time is considered lost, e.g. the process timed out
    PENDING_TIMEOUT = 15 * 60 * 1000

    venue_id = invitation.domain
    assistant_id = f'{venue_id}/AI_Review_Assistant'

    # the answers of the assistant are not questions
    if edit.signatures[0] in [venue_id, assistant_id]:
        return

    # the edits of an existing message are not new questions; a new message gets its id when the edit is saved
    if edit.note.id:
        return

    # the latest message of the chat by creation date, the edits of an older message change its tmdate: the previous
    # question while the assistant has not replied, the placeholder while it answers, or the answer
    latest_notes = client.get_notes(invitation=invitation.id, sort='tcdate:desc', limit=1)
    if not latest_notes:
        return

    latest_note = latest_notes[0]
    answered = latest_note.signatures[0] == assistant_id and latest_note.content['message']['value'] != THINKING_MESSAGE

    now = openreview.tools.datetime_millis(datetime.datetime.now())
    if not answered and now - latest_note.tcdate < PENDING_TIMEOUT:
        raise openreview.OpenReviewException('Please wait for the answer to your previous message before sending a new one.')
