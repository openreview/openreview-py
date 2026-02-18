def process(client, invitation):
    import csv
    from tqdm import tqdm
    import time

    now = openreview.tools.datetime_millis(datetime.datetime.utcnow())
    cdate = invitation.cdate

    if cdate > now:
        ## invitation is in the future, do not process
        print('invitation is not yet active', cdate)
        return

    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    submission_venue_id = domain.get_content_value('submission_venue_id')
    review_name = domain.get_content_value('review_name')
    submission_name = domain.get_content_value('submission_name')
    authors_name  = domain.get_content_value('authors_name')

    email_subject = invitation.get_content_value('subject')
    email_content = invitation.get_content_value('message')
    fields_to_include = invitation.get_content_value('review_fields_to_include')

    status_invitation_id = domain.get_content_value('status_invitation_id')

    if not fields_to_include:
        if status_invitation_id:
            # post status to request form
            client.post_note_edit(
                invitation=status_invitation_id,
                signatures=[venue_id],
                note=openreview.api.Note(
                    signatures=[venue_id],
                    content={
                        'title': { 'value': 'Author Review Notification Failed' },
                        'comment': { 'value': f'The process "{invitation.id.split("/")[-1].replace("_", " ")}" was scheduled to run, but we found no valid review fields to include in the email notification. Please re-schedule this process to run at a later time and then select which fields to include.\n1. To re-schedule this process for a later time, go to the [workflow timeline UI](https://openreview.net/group/edit?={venue_id}), find and expand the "Create {invitation.id.split("/")[-1].replace("_", " ")}" invitation, and click on "Edit" next to "Dates". Set the activation date to a later time and click "Submit".\n2. Once the process has been re-scheduled, click "Edit" next to the "Fields To Include" invitation, select the fields to include when emailing reviews to authors and click "Submit".\n\nIf you would like this process to run now, you can skip step 1 and just select a valid fields to include. Once you have selected the fields to include, click "Submit" and the process will automatically be scheduled to run shortly.'}
                    }
                )
            )
        return

    active_submissions = client.get_notes(content={'venueid': submission_venue_id}, details='directReplies')
    print('# active submissions:', len(active_submissions))

    def send_reviews_email(submission):
        subject = email_subject.format(
            submission_number=submission.number,
            submission_title=submission.content['title']['value']
        )
        reviews = [openreview.api.Note.from_json(reply) for reply in submission.details['directReplies'] if f'{venue_id}/{submission_name}{submission.number}/-/{review_name}' in reply['invitations']]

        formatted_reviews = ''

        for review in reviews:
            keys = fields_to_include
            for key in keys:
                value = review.content.get(key, {}).get('value')
                if value:
                    formatted_reviews+=f'''**{key}**: {value}\n'''
            formatted_reviews+='\n'

        if formatted_reviews:
            message = email_content.format(
                submission_number=submission.number,
                submission_title=submission.content['title']['value'],
                formatted_reviews=formatted_reviews,
                submission_forum=submission.id
            )

            client.post_message(
                subject=subject,
                recipients=[f'{venue_id}/{submission_name}{submission.number}/{authors_name}'],
                message=message,
                invitation=invitation.id
            )

    if fields_to_include:
        openreview.tools.concurrent_requests(send_reviews_email, active_submissions)
        print('Review emails sent to authors')
    else:
        print('No fields were selected; please set the review fields to include in the email to be sent to authors')