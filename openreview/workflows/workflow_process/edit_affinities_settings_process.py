def process(client, edit, invitation):

    job_id = edit.content.get('expertise_job_id', {}).get('value')

    if job_id:
        try:
            status_response = client.get_expertise_status(job_id)
            status = status_response.get('status')
            if 'Completed' not in status:
                raise openreview.OpenReviewException(f'Expertise job with ID "{job_id}" has not completed yet. Current status: {status}')
        except Exception as e:
            raise openreview.OpenReviewException(f'Failed to fetch expertise status for job_id "{job_id}". Error: {e}')