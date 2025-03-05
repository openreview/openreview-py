def process(client, invitation):

    import csv
    from io import StringIO
    from tqdm import tqdm
    from concurrent.futures import ThreadPoolExecutor
    from multiprocessing import cpu_count
    import datetime

    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    submission_venue_id = domain.content['submission_venue_id']['value']
    submission_name = domain.content['submission_name']['value']
    decision_name = domain.content.get('decision_name', {}).get('value', 'Decision')
    program_chairs_id = domain.get_content_value('program_chairs_id')

    decision_csv = invitation.get_content_value('decision_CSV')
    upload_date = invitation.get_content_value('upload_date')

    cdate = invitation.cdate

    now = openreview.tools.datetime_millis(datetime.datetime.utcnow())
    if cdate > now:
        ## invitation is in the future, do not process
        print('invitation is not yet active', cdate)
        return

    if not upload_date:
        raise openreview.OpenReviewException('Select a valid date to upload paper decisions')

    if not decision_csv:
        # post comment to request form
        raise openreview.OpenReviewException('No decision CSV was uploaded')
    
    notes = client.get_all_notes(content={ 'venueid': submission_venue_id }, details='directReplies')

    decisions_file = client.get_attachment(field_name='decision_CSV', invitation_id=invitation.id)
    decisions_data = list(csv.reader(StringIO(decisions_file.decode()), delimiter=","))
    paper_notes = {note.number: note for note in notes}

    def post_decision(paper_decision):
        if len(paper_decision) < 2:
            raise openreview.OpenReviewException(
                "Not enough values provided in the decision file. Expected values are: paper_number, decision, comment")
        if len(paper_decision) > 3:
            raise openreview.OpenReviewException(
                "Too many values provided in the decision file. Expected values are: paper_number, decision, comment"
            )
        if len(paper_decision) == 3:
            paper_number, decision, comment = paper_decision
        else:
            paper_number, decision = paper_decision
            comment = ''

        paper_number = int(paper_number)

        paper_note = paper_notes.get(paper_number, None)
        if not paper_note:
            raise openreview.OpenReviewException(
                f"Paper {paper_number} not found. Please check the submitted paper numbers."
            )

        paper_decision_note = None
        if paper_note.details:
            for reply in paper_note.details['directReplies']:
                if f'{venue_id}/{submission_name}{paper_note.number}/-/{decision_name}' in reply['invitations']:
                    paper_decision_note = reply
                    break

        content = {
            'title': {'value': 'Paper Decision'},
            'decision': {'value': decision.strip()},
            'comment': {'value': comment},
        }
        if paper_decision_note:
            client.post_note_edit(invitation = f'{venue_id}/{submission_name}{paper_note.number}/-/{decision_name}',
                signatures = [program_chairs_id],
                note = openreview.api.Note(
                    id = paper_decision_note['id'],
                    content = content
                )
            )
        else:
            client.post_note_edit(invitation = f'{venue_id}/{submission_name}{paper_note.number}/-/{decision_name}',
                signatures = [program_chairs_id],
                note = openreview.api.Note(
                    content = content
                )
            )

        print(f"Decision posted for Paper {paper_number}")

    futures = []
    futures_param_mapping = {}
    gathering_responses = tqdm(total=len(decisions_data), desc='Gathering Responses')
    results = []
    errors = {}

    with ThreadPoolExecutor(max_workers=min(6, cpu_count() - 1)) as executor:
        for _decision in decisions_data:
            _future = executor.submit(post_decision, _decision)
            futures.append(_future)
            futures_param_mapping[_future] = str(_decision)

        for future in futures:
            gathering_responses.update(1)
            try:
                results.append(future.result())
            except Exception as e:
                errors[futures_param_mapping[future]] = e.args[0] if isinstance(e, openreview.OpenReviewException) else repr(e)

        gathering_responses.close()

    print(f'{len(results)} decisions posted')

    if errors:
        print(errors)