def process(client, edit, invitation):

    THINKING_MESSAGE = 'Thinking...'
    # a question still waiting for its answer after this time is considered lost, e.g. the process timed out
    PENDING_TIMEOUT = 15 * 60 * 1000

    # the edit is not saved yet, so it has no domain
    domain = client.get_group(invitation.domain)
    assistant_id = f'{domain.id}/AI_Review_Assistant'

    # the answers of the assistant are not questions
    if edit.signatures[0] in [domain.id, assistant_id]:
        return

    chat_notes = client.get_all_notes(invitation=invitation.id, sort='tcdate:asc')

    # the edits of an existing message are not new questions
    if edit.note.id and edit.note.id in { note.id for note in chat_notes }:
        return

    questions = [note for note in chat_notes if note.signatures[0] != assistant_id]
    answered = { note.replyto for note in chat_notes if note.signatures[0] == assistant_id and note.content['message']['value'] != THINKING_MESSAGE }

    now = openreview.tools.datetime_millis(datetime.datetime.now())
    if questions and questions[-1].id not in answered and now - questions[-1].tcdate < PENDING_TIMEOUT:
        raise openreview.OpenReviewException('Please wait for the answer to your previous message before sending a new one.')
