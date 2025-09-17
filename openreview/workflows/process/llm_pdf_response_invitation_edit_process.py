def process(client, invitation):

    api_key = invitation.get_content_value('api_key')
    if not api_key:
        print('No API key provided')
        return

    domain = client.get_group(invitation.domain)
    meta_invitation = client.get_invitation(domain.content['meta_invitation_id']['value'])
    submission_venue_id = domain.content['submission_venue_id']['value']
    submission_name = domain.content['submission_name']['value']
    script = meta_invitation.content["invitation_edit_script"]['value']
    funcs = {
        'openreview': openreview,
        'datetime': datetime,
        'date_index': date_index
    }
    exec(script, funcs)
    funcs['process'](client, invitation)

    model = invitation.get_content_value('model', 'gemini/gemini-2.0-flash')
    prompt = invitation.get_content_value('prompt')
    gateway = openreview.llm.LLMGateway(api_key, model)
    gateway.set_system_message('You are a reviewer expert in AI topics.')

    # add rest of date process here!
    now = openreview.tools.datetime_millis(datetime.datetime.now())
    cdate = invitation.edit['invitation']['cdate'] if 'cdate' in invitation.edit['invitation'] else invitation.cdate
    if cdate > now and not client.get_invitations(invitation=invitation.id, limit=1):
        ## invitation is in the future, do not process
        print('invitation is not yet active and no child invitations created', cdate)
        return

    submissions = client.get_all_notes(content={ 'venueid': submission_venue_id }, sort='number:asc', details='directReplies')
    child_invitation_name = invitation.edit['invitation']['id'].split('/-/')[-1]

    llm_pdf_responses = [reply for s in submissions for reply in s.details['directReplies'] if reply['invitations'][0].endswith(f'/-/{child_invitation_name}')]
    if llm_pdf_responses:
        return

    def generate_and_post_review(note):
        response = gateway.chat(prompt, pdf_attachment=client.get_attachment('pdf', id=note.id))

        client.post_note_edit(
            invitation=f'{domain.id}/{submission_name}{note.number}/-/{child_invitation_name}',
            signatures=[f'{domain.id}/Automated_Administrator'],
            note=openreview.api.Note(
                content={
                    'feedback': { 'value': response },
                }
            )
        )

    openreview.tools.concurrent_requests(generate_and_post_review, submissions, desc=f'llm_pdf_response_edit_invitation_process')

    print(f'{len(submissions)} LLM-generated feedbacks posted.')
    