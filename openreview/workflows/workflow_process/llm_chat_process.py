def process(client, edit, invitation):
    '''Answers a message posted to a chat invitation, e.g. `<venue>/Submission<N>/Reviewer_<id>/-/LLM_Interaction`.

    Sends the prompt, the submission PDF, the submission metadata visible to the committee and the chat history
    to the LLM gateway and posts the answer as a reply signed by `<venue>/AI_Review_Assistant`. When the super
    invitation lists reply invitation names in llm_reply_invitations, e.g. the reviews, rebuttals and comments for
    the area chairs, the forum replies of those invitations that the committee member can read are sent too.

    The settings are read from the content of the committee super invitation, e.g. `<venue>/Reviewers/-/LLM_Interaction`,
    edited by the program chairs with its `/Settings` invitation: llm_api_key, llm_base_url and
    llm_prompt (required, the gateway URL and the default prompt are set when the super invitation is created)
    and llm_model.

    The edit of each answer stores the tokens used, the gateway usage and the cost in USD in its content, readable
    by the venue only. Once the answers in a chat, one committee member on one submission, add up to llm_token_limit
    tokens, the assistant stops calling the LLM in that chat.

    This is the `process_script` of the super invitation. The process of the child invitations execs it with
    the `openreview`, `datetime`, `base64` and `requests` modules.
    '''

    MAX_TOKENS = 16000
    REQUEST_TIMEOUT = 600
    # the PDF is sent base64 encoded and the request must stay under the 32MB request limit
    MAX_PDF_BYTES = 20 * 1024 * 1024

    THINKING_MESSAGE = 'Thinking...'
    ERROR_MESSAGE = 'Sorry, I could not answer this message. Please try again later.'
    LIMIT_MESSAGE = 'You have reached the usage limit of the AI assistant for this submission. Please contact the program chairs if you need to continue.'
    UNAVAILABLE_MESSAGE = 'The submission is not available to you yet, so the AI assistant cannot answer questions about it.'

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

    def count_tokens(usage):
        # all the input, cache and output tokens reported by the gateway
        return sum(value for key, value in usage.items() if key.endswith('_tokens') and isinstance(value, int))

    def get_cost(headers):
        # the cost of the call in USD reported by the gateway, after its discount and margin
        if headers.get('x-litellm-response-cost') is not None:
            return float(headers['x-litellm-response-cost'])
        if headers.get('x-litellm-response-cost-original') is None:
            return None
        return float(headers['x-litellm-response-cost-original']) - float(headers.get('x-litellm-response-cost-discount-amount') or 0) + float(headers.get('x-litellm-response-cost-margin-amount') or 0)

    def update_reply(reply_edit_id, message, usage=None, cost=None):
        reply_edit = client.get_note_edit(reply_edit_id)
        reply_edit.note.content['message']['value'] = message
        if usage:
            # the invitation makes the usage readable by the venue only
            reply_edit.content = {
                'tokens': { 'value': count_tokens(usage) },
                'usage': { 'value': usage }
            }
            if cost is not None:
                reply_edit.content['cost'] = { 'value': cost }
        # re-post the same edit so the reply note keeps its id
        reply_edit.note.id = None
        client.post_edit(reply_edit)

    def get_used_tokens():
        # the tokens of the answers in this chat, the committee member's chat about the submission; the edits
        # without usage, like the placeholder, have the content fields without a value
        return sum(
            (chat_edit.content or {}).get('tokens', {}).get('value') or 0
            for chat_edit in client.get_note_edits(invitation=invitation.id)
            if chat_edit.signatures[0] == assistant_id
        )

    def get_answer():
        super_invitation = client.get_invitation(invitation.invitations[0])
        api_key = super_invitation.get_content_value('llm_api_key')
        base_url = super_invitation.get_content_value('llm_base_url')
        model = super_invitation.get_content_value('llm_model', 'claude-sonnet-4-6')
        prompt = super_invitation.get_content_value('llm_prompt')
        token_limit = super_invitation.get_content_value('llm_token_limit')
        if not api_key or not base_url or not prompt:
            raise openreview.OpenReviewException('The LLM key, URL or prompt is missing, set them with the LLM_Interaction/Settings invitation')

        if token_limit is not None:
            used_tokens = get_used_tokens()
            print(f'tokens used in the chat: {used_tokens} of {token_limit}')
            if used_tokens >= token_limit:
                return LIMIT_MESSAGE, None, None

        submission = client.get_note(edit.note.forum)
        submission_name = domain.get_content_value('submission_name', 'Submission')
        # the super invitation belongs to the committee that chats, e.g. <venue>/Reviewers/-/LLM_Interaction
        committee_name = super_invitation.id.split('/-/')[0].split('/')[-1]

        # the groups that make a note or a field visible to the committee member asking the questions; the context
        # is built with the venue client, so every note and field is checked against them
        member_readers = {
            'everyone',
            f'{venue_id}/{committee_name}',
            f'{venue_id}/{submission_name}{submission.number}/{committee_name}',
            edit.signatures[0]
        }

        def can_read(note):
            return bool(member_readers.intersection(note.readers)) and not member_readers.intersection(note.nonreaders or [])

        def is_visible(field):
            return 'readers' not in field or bool(member_readers.intersection(field['readers']))

        # e.g. the chats were activated before the submissions were released to the committee
        if not can_read(submission):
            return UNAVAILABLE_MESSAGE, None, None

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

        def format_fields(content, excluded_fields=[]):
            lines = []
            for field_name, field in content.items():
                if field_name in excluded_fields or field_name.startswith('_') or not is_visible(field):
                    continue
                value = field.get('value')
                if isinstance(value, list):
                    value = ', '.join(str(item) for item in value)
                if value in (None, ''):
                    continue
                lines.append(f'{field_name.replace("_", " ").capitalize()}: {value}')
            return lines

        metadata = [f'Submission number: {submission.number}'] + format_fields(submission.content, EXCLUDED_FIELDS)

        if not context:
            metadata.append('The submission PDF is not available, answer based on the metadata only.')

        context.append({ 'type': 'text', 'text': 'Submission metadata:\n\n' + '\n\n'.join(metadata) })

        # the forum replies of the invitations listed by the super invitation, e.g. the reviews, rebuttals and
        # comments for the area chairs, that the committee member can read
        reply_invitation_names = super_invitation.get_content_value('llm_reply_invitations', [])
        if reply_invitation_names:

            def label(note):
                return f'{note.invitations[0].split("/-/")[-1].replace("_", " ")} by {note.signatures[0].split("/")[-1]}'

            forum_notes = { note.id: note for note in client.get_all_notes(forum=submission.id, sort='tcdate:asc') }
            replies = []
            for note in forum_notes.values():
                if note.id == submission.id or note.invitations[0].split('/-/')[-1] not in reply_invitation_names or not can_read(note):
                    continue
                header = label(note)
                parent = forum_notes.get(note.replyto)
                if parent and parent.id != submission.id and can_read(parent):
                    header += f', in reply to the {label(parent)}'
                replies.append(f'{header}:\n\n' + '\n\n'.join(format_fields(note.content)))

            context.append({ 'type': 'text', 'text': 'Forum replies:\n\n' + ('\n\n---\n\n'.join(replies) if replies else 'There are no replies in the forum yet.') })

        if model.startswith('claude'):
            # every message of the chat resends the same context, cache it
            context[-1]['cache_control'] = { 'type': 'ephemeral' }

        # the conversation up to and including the message being answered, oldest first
        messages = []
        for note in client.get_all_notes(invitation=invitation.id, sort='tcdate:asc'):
            text = note.content.get('message', {}).get('value', '')
            if note.signatures[0] == assistant_id:
                # skip the replies that were never completed
                if text not in (THINKING_MESSAGE, ERROR_MESSAGE, LIMIT_MESSAGE, UNAVAILABLE_MESSAGE):
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
        usage = { 'model': result.get('model', model), **(result.get('usage') or {}) }
        cost = get_cost(response.headers)
        print('LLM usage:', usage, 'cost:', cost)

        if result.get('stop_reason') == 'refusal':
            return 'Sorry, I cannot help with this request.', usage, cost

        answer = '\n\n'.join(block['text'] for block in result.get('content', []) if block.get('type') == 'text').strip()
        if result.get('stop_reason') == 'max_tokens':
            answer += '\n\n_The answer was cut off because it reached the maximum length._'
        return answer, usage, cost

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
        answer, usage, cost = get_answer()
    except Exception:
        update_reply(reply_edit['id'], ERROR_MESSAGE)
        raise

    update_reply(reply_edit['id'], answer, usage, cost)
