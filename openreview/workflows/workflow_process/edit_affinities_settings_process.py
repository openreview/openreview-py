def process(client, edit, invitation):

    job_id = edit.content.get('expertise_job_id', {}).get('value')

    if job_id:
        if edit.content.get('affinity_score_model', {}).get('value') != 'I will upload my own affinity scores':
            raise openreview.OpenReviewException('If you provide an expertise job ID, you must select "I will upload my own affinity scores" as the affinity score model. To use an expertise model, delete the expertise job ID.')
        try:
            status_response = client.get_expertise_status(job_id)
            status = status_response.get('status')
            if 'Completed' not in status:
                raise openreview.OpenReviewException(f'Expertise job with ID "{job_id}" has not completed yet. Current status: {status}')
        except Exception as e:
            raise openreview.OpenReviewException(f'Failed to fetch expertise status for job_id "{job_id}". Error: {e}')