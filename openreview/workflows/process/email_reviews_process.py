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

    submission_authors_id = f'{venue_id}/{submission_name}{{submission_number}}/{authors_name}'

    email_subject = invitation.get_content_value('subject')
    email_content = invitation.get_content_value('message')
    fields_to_include = invitation.get_content_value('review_fields_to_include')

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