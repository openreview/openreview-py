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
    decision_name = domain.get_content_value('decision_name')
    submission_name = domain.get_content_value('submission_name')
    authors_name  = domain.get_content_value('authors_name')

    email_subject = invitation.get_content_value('subject')
    email_content = invitation.get_content_value('message')

    active_submissions = client.get_notes(content={'venueid': submission_venue_id}, details='directReplies')
    print('# active submissions:', len(active_submissions))

    def send_decision_email(submission):
        subject = email_subject.format(
            submission_number=submission.number,
            submission_title=submission.content['title']['value']
        )
        decisions = [openreview.api.Note.from_json(reply) for reply in submission.details['directReplies'] if f'{venue_id}/{submission_name}{submission.number}/-/{decision_name}' in reply['invitations']]
        if decisions:
            decision = decisions[0]
            decision_comment = f'''\n\nComment: {decision.content['comment']['value']}''' if 'comment' in decision.content else ''
            
            formatted_decision = f'''Decision: {decision.content['decision']['value']} {decision_comment}'''

            message = email_content.format(
                submission_number=submission.number,
                submission_title=submission.content['title']['value'],
                formatted_decision=formatted_decision,
                submission_forum=submission.id
            )

            client.post_message(
                subject=subject,
                recipients=[f'{venue_id}/{submission_name}{submission.number}/{authors_name}'],
                message=message,
                invitation=invitation.id
            )

    openreview.tools.concurrent_requests(send_decision_email, active_submissions)

    print('Decision emails sent to authors')