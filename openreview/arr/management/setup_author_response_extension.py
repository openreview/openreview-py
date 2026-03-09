def process(client, invitation):
    from openreview.arr.arr import ARR
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

    # Get domain and venue information
    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    meta_invitation_id = domain.content['meta_invitation_id']['value']

    # Fetch all submissions with replies
    submissions = client.get_all_notes(
        invitation=f"{venue_id}/-/Submission",
        details='directReplies',
        sort='number:asc'
    )

    print(f'Processing {len(submissions)} total submissions')

    # Read delays from invitation content
    author_response_delay = invitation.content['author_response_delay_ms']['value']
    reviewer_response_delay = invitation.content['reviewer_response_delay_ms']['value']
    review_issue_report_delay = invitation.content['review_issue_report_delay_ms']['value']

    # Constants for timing
    TWO_WEEKS_MILLIS = openreview.tools.datetime_millis(
        datetime.datetime.now() + datetime.timedelta(days=14)
    )

    # Process each submission
    for submission in submissions:
        paper_number = submission.number

        try:
            # Extract Official_Review notes from replies
            reviews = [r for r in submission.details.get('directReplies', []) if any('Official_Review' in i for i in r.get('invitations', []))]

            # Sort reviews by tcdate
            reviews.sort(key=lambda r: r.get('tcdate', 0))

            review_count = len(reviews)
            print(f'Paper {paper_number}: {review_count} reviews found')

            if review_count < 3:
                # CASE 1: Papers with < 3 reviews - keep everything open
                ARR.handle_insufficient_reviews(
                    client, venue_id, meta_invitation_id, paper_number,
                    TWO_WEEKS_MILLIS, now
                )
            else:
                # CASE 2: Papers with 3+ reviews - use 3rd review timing
                third_review = reviews[2]
                third_review_tcdate = third_review.get('tcdate', 0)

                print(f'Paper {paper_number}: Using 3rd review date {third_review_tcdate}')

                ARR.handle_sufficient_reviews(
                    client, venue_id, meta_invitation_id, paper_number,
                    third_review_tcdate, review_count, now,
                    author_response_delay, reviewer_response_delay, review_issue_report_delay
                )

        except Exception as e:
            print(f'Error processing paper {paper_number}: {str(e)}')
            continue

    print(f'Completed author response extension management for {venue_id}')
