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
    submission_id = domain.get_content_value('submission_id')
    decision_name = domain.get_content_value('decision_name')
    submission_name = domain.get_content_value('submission_name')
    authors_name  = domain.get_content_value('authors_name')

    email_subject = invitation.get_content_value('subject')
    email_content = invitation.get_content_value('message')
    fields_to_include = invitation.get_content_value('fields_to_include')
    contact_email = domain.get_content_value('contact')
    decision_option = invitation.get_content_value('decision_option')

    if not fields_to_include:
        # log the failure so PCs can see it in the workflow timeline
        print(f'{decision_option} decision emails were not sent: no decision fields were selected. Select the fields under "Fields To Include" to run this step.')
        return

    def send_decision_email(submission_tuple):
        submission, decisions = submission_tuple

        subject = email_subject.format(
            submission_number=submission.number,
            submission_title=submission.content['title']['value']
        )

        # if email with this subject has already been sent, skip sending email
        if not client.get_messages(subject=subject):
            if decisions:
                formatted_decision = ''
                decision = decisions[0]
                for key in fields_to_include:
                    value = decision.content.get(key, {}).get('value')
                    if value:
                        formatted_decision+=f'''**{key}**: {value}\n'''

                message = email_content.format(
                    submission_number=submission.number,
                    submission_title=submission.content['title']['value'],
                    formatted_decision=formatted_decision,
                    submission_forum=submission.id
                )

                request = client.post_message(
                    subject=subject,
                    recipients=[f'{venue_id}/{submission_name}{submission.number}/{authors_name}'],
                    message=message,
                    invitation=invitation.id,
                    replyTo=contact_email
                )
                return request

        return None

    all_submissions = client.get_all_notes(invitation=submission_id, sort='number:asc', details='directReplies', domain=venue_id)
    print(f'Total submissions retrieved: {len(all_submissions)}')

    filtered_submissions = []
    for submission in all_submissions:
        if openreview.tools.should_match_invitation_source(client, invitation, submission, domain=domain):
            filtered_submissions.append((submission, [openreview.api.Note.from_json(reply) for reply in submission.details['directReplies'] if f'{venue_id}/{submission_name}{submission.number}/-/{decision_name}' in reply['invitations']]))

    print(f'{len(filtered_submissions)} out of {len(all_submissions)} submissions matched the source criteria')

    if not filtered_submissions:
        print(f'No emails were sent since there are no "{decision_option}" submissions')
        return

    messages = openreview.tools.concurrent_requests(send_decision_email, filtered_submissions)
    len_messages = len([m for m in messages if m is not None])

    if len_messages:
        print(f'{len_messages} "{decision_option}" decision emails sent to authors')
    else:
        print(f'No new "{decision_option}" decision emails sent to authors')