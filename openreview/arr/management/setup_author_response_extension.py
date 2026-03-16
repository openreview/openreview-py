def process(client, invitation):
    """
    Author Response Extension Management Process

    This process runs on a cron schedule to:
    1. Keep Official_Comment open for papers with <3 reviews
    2. Keep Review_Issue_Report open for papers with <3 reviews
    3. Close Official_Comment/Review_Issue_Report based on 3rd review date for papers with 3+ reviews

    The process re-opens invitations if they were closed by other processes (e.g., setup_rebuttal_end.py)
    """

    import datetime

    now = openreview.tools.datetime_millis(datetime.datetime.now())
    cdate = invitation.cdate

    # Check if invitation is active
    if cdate > now:
        print(f'Author response extension process not yet active, cdate: {cdate}')
        return

    domain = client.get_group(invitation.domain)
    request_form_id = domain.content['request_form_id']['value']

    client_v1 = openreview.Client(
        baseurl=openreview.tools.get_base_urls(client)[0],
        token=client.token
    )

    venue = openreview.helpers.get_conference(client_v1, request_form_id)

    venue.process_author_response_extension(invitation)
