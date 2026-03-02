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
                handle_insufficient_reviews(
                    client, venue_id, meta_invitation_id, paper_number,
                    TWO_WEEKS_MILLIS, now
                )
            else:
                # CASE 2: Papers with 3+ reviews - use 3rd review timing
                third_review = reviews[2]
                third_review_tcdate = third_review.get('tcdate', 0)

                print(f'Paper {paper_number}: Using 3rd review date {third_review_tcdate}')

                handle_sufficient_reviews(
                    client, venue_id, meta_invitation_id, paper_number,
                    third_review_tcdate, review_count, now,
                    author_response_delay, reviewer_response_delay, review_issue_report_delay
                )

        except Exception as e:
            print(f'Error processing paper {paper_number}: {str(e)}')
            continue

    print(f'Completed author response extension management for {venue_id}')


def handle_insufficient_reviews(client, venue_id, meta_invitation_id, paper_number,
                                two_weeks_millis, now_millis):
    """
    Handle papers with < 3 reviews by keeping Official_Comment and Review_Issue_Report open
    """
    print(f'Paper {paper_number}: Keeping invitations open (< 3 reviews)')

    # Open Official_Comment for authors
    try:
        invitation = client.get_invitation(
            f"{venue_id}/Submission{paper_number}/-/Official_Comment"
        )

        needs_update = False
        edit_params = {}

        # Check invitees
        authors_group = f"{venue_id}/Submission{paper_number}/Authors"
        if authors_group not in invitation.invitees:
            edit_params['invitees'] = {'add': [authors_group]}
            needs_update = True
            print(f'  - Adding Authors to Official_Comment invitees')

        # Check outer readers
        if authors_group not in invitation.readers:
            if 'readers' not in edit_params:
                edit_params['readers'] = {}
            edit_params['readers']['add'] = [authors_group]
            needs_update = True
            print(f'  - Adding Authors to Official_Comment outer readers')

        # Check inner readers (note readers)
        current_readers = invitation.edit['note']['readers']['param']['enum']
        if authors_group not in current_readers:
            if 'edit' not in edit_params:
                edit_params['edit'] = {}
            edit_params['edit']['note'] = {
                'readers': {
                    'param': {
                        'enum': current_readers + [authors_group]
                    }
                }
            }
            needs_update = True
            print(f'  - Adding Authors to Official_Comment inner readers')

        # Check signatures
        current_signatures = invitation.edit['signatures']['param']['items']
        signature_values = [
            item.get('prefix') if 'prefix' in item else item.get('value', '')
            for item in current_signatures
        ]
        if not any('Authors' in sig for sig in signature_values):
            if 'edit' not in edit_params:
                edit_params['edit'] = {}
            if 'signatures' not in edit_params.get('edit', {}):
                if 'edit' not in edit_params:
                    edit_params['edit'] = {}
                edit_params['edit']['signatures'] = {
                    'param': {
                        'items': current_signatures + [
                            {'value': authors_group, 'optional': True}
                        ]
                    }
                }
            needs_update = True
            print(f'  - Adding Authors to Official_Comment signatures')

        if needs_update:
            client.post_invitation_edit(
                invitations=meta_invitation_id,
                readers=[venue_id],
                writers=[venue_id],
                signatures=[venue_id],
                invitation=openreview.api.Invitation(
                    id=invitation.id,
                    signatures=[venue_id],
                    **edit_params
                )
            )
            print(f'  - Updated Official_Comment invitation for paper {paper_number}')
        else:
            print(f'  - Official_Comment already open for paper {paper_number}')

    except Exception as e:
        print(f'  - Error updating Official_Comment for paper {paper_number}: {str(e)}')

    # Open Review_Issue_Report invitations for each review (1-10)
    for review_number in range(1, 11):
        try:
            invitation = client.get_invitation(
                f"{venue_id}/Submission{paper_number}/Official_Review{review_number}/-/Review_Issue_Report"
            )

            needs_update = False
            edit_params = {}

            # Check if not yet activated
            if invitation.cdate > now_millis:
                edit_params['cdate'] = now_millis
                needs_update = True
                print(f'  - Activating Review_Issue_Report for Review{review_number}')

            # Check if expired
            if invitation.expdate <= now_millis:
                edit_params['expdate'] = two_weeks_millis
                needs_update = True
                print(f'  - Setting Review_Issue_Report expdate to ~2 weeks for Review{review_number}')

            if needs_update:
                client.post_invitation_edit(
                    invitations=meta_invitation_id,
                    readers=[venue_id],
                    writers=[venue_id],
                    signatures=[venue_id],
                    invitation=openreview.api.Invitation(
                        id=invitation.id,
                        signatures=[venue_id],
                        **edit_params
                    )
                )
                print(f'  - Updated Review_Issue_Report for Review{review_number}')

        except Exception as e:
            # Review invitation doesn't exist, skip silently
            continue


def handle_sufficient_reviews(client, venue_id, meta_invitation_id, paper_number,
                              third_review_tcdate, review_count, now_millis,
                              three_days_millis, four_days_millis, five_days_millis):
    """
    Handle papers with 3+ reviews by closing based on 3rd review date
    """
    print(f'Paper {paper_number}: Checking based on 3rd review (total reviews: {review_count})')

    # Calculate closure dates
    author_response_close = third_review_tcdate + three_days_millis
    reviewer_response_close = third_review_tcdate + four_days_millis
    review_issue_close = third_review_tcdate + five_days_millis

    print(f'  - Author response closes at: {author_response_close}')
    print(f'  - Reviewer response closes at: {reviewer_response_close}')
    print(f'  - Review issues close at: {review_issue_close}')

    # Handle Official_Comment invitation
    try:
        invitation = client.get_invitation(
            f"{venue_id}/Submission{paper_number}/-/Official_Comment"
        )

        needs_update = False
        edit_params = {}
        authors_group = f"{venue_id}/Submission{paper_number}/Authors"

        # Remove authors from invitees/signatures/outer readers after 3 days
        if now_millis > author_response_close:
            if authors_group in invitation.invitees:
                edit_params['invitees'] = {'remove': [authors_group]}
                needs_update = True
                print(f'  - Removing Authors from Official_Comment invitees')

            if authors_group in invitation.readers:
                if 'readers' not in edit_params:
                    edit_params['readers'] = {}
                edit_params['readers']['remove'] = [authors_group]
                needs_update = True
                print(f'  - Removing Authors from Official_Comment outer readers')

            # Remove from signatures
            current_signatures = invitation.edit['signatures']['param']['items']
            signature_values = [
                item.get('prefix') if 'prefix' in item else item.get('value', '')
                for item in current_signatures
            ]
            if any('Authors' in sig for sig in signature_values):
                filtered_signatures = [
                    sig_obj for sig_obj in current_signatures
                    if 'Authors' not in (
                        sig_obj.get('prefix', '') if 'prefix' in sig_obj
                        else sig_obj.get('value', '')
                    )
                ]
                if 'edit' not in edit_params:
                    edit_params['edit'] = {}
                edit_params['edit']['signatures'] = {
                    'param': {'items': filtered_signatures}
                }
                needs_update = True
                print(f'  - Removing Authors from Official_Comment signatures')

        # Remove authors from inner readers after 4 days
        if now_millis > reviewer_response_close:
            current_readers = invitation.edit['note']['readers']['param']['enum']
            if any('Authors' in reader for reader in current_readers):
                filtered_readers = [
                    reader for reader in current_readers if 'Authors' not in reader
                ]
                if 'edit' not in edit_params:
                    edit_params['edit'] = {}
                if 'note' not in edit_params['edit']:
                    edit_params['edit']['note'] = {}
                edit_params['edit']['note']['readers'] = {
                    'param': {'enum': filtered_readers}
                }
                needs_update = True
                print(f'  - Removing Authors from Official_Comment inner readers')

        if needs_update:
            client.post_invitation_edit(
                invitations=meta_invitation_id,
                readers=[venue_id],
                writers=[venue_id],
                signatures=[venue_id],
                invitation=openreview.api.Invitation(
                    id=invitation.id,
                    signatures=[venue_id],
                    **edit_params
                )
            )
            print(f'  - Updated Official_Comment closures for paper {paper_number}')
        else:
            print(f'  - Official_Comment closures already set for paper {paper_number}')

    except Exception as e:
        print(f'  - Error updating Official_Comment for paper {paper_number}: {str(e)}')

    # Handle Review_Issue_Report invitations (1-10 reviews)
    for review_number in range(1, 11):
        try:
            invitation = client.get_invitation(
                f"{venue_id}/Submission{paper_number}/Official_Review{review_number}/-/Review_Issue_Report"
            )

            if invitation.expdate != review_issue_close:
                client.post_invitation_edit(
                    invitations=meta_invitation_id,
                    readers=[venue_id],
                    writers=[venue_id],
                    signatures=[venue_id],
                    invitation=openreview.api.Invitation(
                        id=invitation.id,
                        signatures=[venue_id],
                        expdate=review_issue_close
                    )
                )
                print(f'  - Set Review_Issue_Report expdate for Review{review_number}')

        except Exception as e:
            # Review invitation doesn't exist, skip silently
            continue
