def process(client, edit, invitation):
    '''Answers a reviewer message posted to a `<venue>/Submission<N>/Reviewer_<id>/-/LLM_Interaction` invitation.

    Sends the prompt, the submission PDF, the submission metadata visible to reviewers and the chat history
    to the LLM gateway and posts the answer as a reply signed by `<venue>/AI_Review_Assistant`.

    The settings are read from the content of the `<venue>/-/LLM_Interaction` super invitation, edited by
    the program chairs with the `<venue>/-/LLM_Interaction/Settings` invitation: llm_api_key, llm_base_url and
    llm_prompt (required, the gateway URL and the default prompt are set when the super invitation is created)
    and llm_model.

    This is the `process_script` of the super invitation. The process of the child invitations execs it with
    the `openreview`, `datetime`, `base64` and `requests` modules.
    '''

    MAX_TOKENS = 16000
    REQUEST_TIMEOUT = 600
    # the PDF is sent base64 encoded and the request must stay under the 32MB request limit
    MAX_PDF_BYTES = 20 * 1024 * 1024

    THINKING_MESSAGE = 'Thinking...'
    ERROR_MESSAGE = 'Sorry, I could not answer this message. Please try again later.'

    # never sent to the LLM: the author identities, the files, the author consent checkboxes and the venue bookkeeping fields
    EXCLUDED_FIELDS = ['authors', 'authorids', 'pdf', 'supplementary_material', 'email_sharing', 'data_release', 'venue', 'venueid']

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    assistant_id = f'{venue_id}/AI_Review_Assistant'

    # the replies posted by the assistant run this process too
    if edit.signatures[0] in [venue_id, assistant_id]:
        return

    if edit.note.ddate:
        return

    # answer new messages only, not the edits of a message
    message_edits = client.get_note_edits(note_id=edit.note.id, sort='tcdate:asc')
    if message_edits and message_edits[0].id != edit.id:
        print('not the first edit of the message, exiting...')
        return

    def update_reply(reply_edit_id, message):
        reply_edit = client.get_note_edit(reply_edit_id)
        reply_edit.note.content['message']['value'] = message
        # re-post the same edit so the reply note keeps its id
        reply_edit.note.id = None
        client.post_edit(reply_edit)

    def get_answer():
        super_invitation = client.get_invitation(invitation.invitations[0])
        api_key = super_invitation.get_content_value('llm_api_key')
        base_url = super_invitation.get_content_value('llm_base_url')
        model = super_invitation.get_content_value('llm_model', 'claude-sonnet-4-6')
        prompt = super_invitation.get_content_value('llm_prompt')
        if not api_key or not base_url or not prompt:
            raise openreview.OpenReviewException('The LLM key, URL or prompt is missing, set them with the LLM_Interaction/Settings invitation')

        submission = client.get_note(edit.note.forum)
        submission_name = domain.get_content_value('submission_name', 'Submission')
        reviewers_name = domain.get_content_value('reviewers_name', 'Reviewers')

        # the groups that make a submission field visible to the reviewer asking the questions
        reviewer_readers = {
            'everyone',
            f'{venue_id}/{reviewers_name}',
            f'{venue_id}/{submission_name}{submission.number}/{reviewers_name}',
            edit.signatures[0]
        }

        def is_visible(field):
            return 'readers' not in field or bool(reviewer_readers.intersection(field['readers']))

        context = []

        pdf_field = submission.content.get('pdf')
        if pdf_field and is_visible(pdf_field):
            try:
                pdf = client.get_attachment('pdf', id=submission.id)
                if len(pdf) > MAX_PDF_BYTES:
                    print(f'The submission PDF is too large to attach: {len(pdf)} bytes')
                else:
                    context.append({
                        'type': 'document',
                        'source': {
                            'type': 'base64',
                            'media_type': 'application/pdf',
                            'data': base64.standard_b64encode(pdf).decode('utf-8')
                        }
                    })
            except Exception as e:
                print('Could not load the submission PDF:', e)

        metadata = [f'Submission number: {submission.number}']
        for field_name, field in submission.content.items():
            if field_name in EXCLUDED_FIELDS or field_name.startswith('_') or not is_visible(field):
                continue
            value = field.get('value')
            if isinstance(value, list):
                value = ', '.join(str(item) for item in value)
            if value in (None, ''):
                continue
            metadata.append(f'{field_name.replace("_", " ").capitalize()}: {value}')

        if not context:
            metadata.append('The submission PDF is not available, answer based on the metadata only.')

        context.append({ 'type': 'text', 'text': 'Submission metadata:\n\n' + '\n\n'.join(metadata) })
        if model.startswith('claude'):
            # every message of the chat resends the same PDF and metadata, cache them
            context[-1]['cache_control'] = { 'type': 'ephemeral' }

        # the conversation up to and including the message being answered, oldest first
        messages = []
        for note in client.get_all_notes(invitation=invitation.id, sort='tcdate:asc'):
            text = note.content.get('message', {}).get('value', '')
            if note.signatures[0] == assistant_id:
                # skip the replies that were never completed
                if text not in (THINKING_MESSAGE, ERROR_MESSAGE):
                    messages.append({ 'role': 'assistant', 'content': text })
            else:
                messages.append({ 'role': 'user', 'content': text })

            if note.id == edit.note.id:
                break

        if messages and messages[0]['role'] == 'user':
            messages[0]['content'] = context + [{ 'type': 'text', 'text': messages[0]['content'] }]
        else:
            messages.insert(0, { 'role': 'user', 'content': context })

        body = {
            'model': model,
            'max_tokens': MAX_TOKENS,
            'system': prompt,
            'messages': messages
        }
        if model.startswith('claude'):
            body['thinking'] = { 'type': 'adaptive' }

        response = requests.post(
            f'{base_url.rstrip("/")}/v1/messages',
            headers={
                'Authorization': f'Bearer {api_key}',
                'content-type': 'application/json',
                'anthropic-version': '2023-06-01'
            },
            json=body,
            timeout=REQUEST_TIMEOUT
        )
        if not response.ok:
            raise openreview.OpenReviewException(f'LLM gateway error {response.status_code}: {response.text}')

        result = response.json()
        print('LLM usage:', result.get('usage'), 'cost:', response.headers.get('x-litellm-response-cost'))

        if result.get('stop_reason') == 'refusal':
            return 'Sorry, I cannot help with this request.'

        answer = '\n\n'.join(block['text'] for block in result.get('content', []) if block.get('type') == 'text').strip()
        if result.get('stop_reason') == 'max_tokens':
            answer += '\n\n_The answer was cut off because it reached the maximum length._'
        return answer

    reply_edit = client.post_note_edit(
        invitation=invitation.id,
        signatures=[assistant_id],
        note=openreview.api.Note(
            replyto=edit.note.id,
            content={
                'message': { 'value': THINKING_MESSAGE }
            }
        )
    )

    try:
        answer = get_answer()
    except Exception:
        update_reply(reply_edit['id'], ERROR_MESSAGE)
        raise

    update_reply(reply_edit['id'], answer)
