def process(client, edit, invitation):
    # TODO: Check for reviews and meta-reviews
    editor_reassignment_field = edit.note.content.get('reassignment_request_area_chair', {}).get('value', '')
    editor_reassignment_request = len(editor_reassignment_field) > 0 and 'not a resubmission' not in editor_reassignment_field
    reviewer_reassignment_field = edit.note.content.get('reassignment_request_reviewers', {}).get('value', '')
    reviewer_reassignment_request = len(reviewer_reassignment_field) > 0 and 'not a resubmission' not in reviewer_reassignment_field
    paper_link = edit.note.content.get('previous_URL', {}).get('value')

    # If no previous URL but selected reassignment
    if not paper_link and (editor_reassignment_request or reviewer_reassignment_request):
        raise openreview.OpenReviewException('You have selected a reassignment request with no previous URL. Please enter a URL or close and re-open the submission form to clear your reassignment request')

    if paper_link:
        paper_forum = paper_link.split('?id=')[-1]

        if '&' in paper_link:
            raise openreview.OpenReviewException('Invalid paper link. Please make sure not to provide anything after the character "&" in the paper link.')

        client_v1=openreview.Client(baseurl=openreview.tools.get_base_urls(client)[0], token=client.token)

        try:
            arr_submission_v1 = client_v1.get_note(paper_forum)
        except:
            arr_submission_v1 = None

        try:
            arr_submission_v2 = client.get_note(paper_forum)
        except:
            arr_submission_v2 = None

        if not arr_submission_v1 and not arr_submission_v2:
            raise openreview.OpenReviewException('Provided paper link does not correspond to a submission in OpenReview')

        if (arr_submission_v1 and 'aclweb.org/ACL/ARR' not in arr_submission_v1.invitation) or (arr_submission_v2 and not any('aclweb.org/ACL/ARR' in inv for inv in arr_submission_v2.invitations)):
            raise openreview.OpenReviewException('Provided paper link does not correspond to an ARR submission')
        
        # Check if the submission is from the current cycle
        if (arr_submission_v2 and invitation.domain == arr_submission_v2.domain):
            raise openreview.OpenReviewException('The provided URL points to a submission in the current cycle. Please provide a link to a previous ARR submission.')

        if (arr_submission_v1 and arr_submission_v1.id != arr_submission_v1.forum) or (arr_submission_v2 and arr_submission_v2.id != arr_submission_v2.forum):
            raise openreview.OpenReviewException('Provided paper link does not correspond to an ARR submission. Make sure the link points to a submission and not to a reply.')

        if arr_submission_v1 and 'aclweb.org/ACL/ARR' in arr_submission_v1.invitation and not arr_submission_v1.invitation.endswith('Submission'):
            raise openreview.OpenReviewException('Provided paper link does not point to a blind submission. Make sure you get the url to your submission from the browser')

        # Only authors of the previous ARR submission may link it: linking grants access to its reviews.
        # The edit signature is the verified identity of the submitter; group signatures (paper authors, program chairs) are trusted.
        signature = edit.signatures[0]
        if signature.startswith('~'):
            if arr_submission_v2:
                author_submissions = client.get_notes(invitation=arr_submission_v2.invitations[0], content={'authorids': signature})
                is_author = arr_submission_v2.id in [note.id for note in author_submissions]
            else:
                author_submissions = client_v1.get_notes(invitation=arr_submission_v1.invitation.replace('/-/Blind_Submission', '/-/Submission'), content={'authorids': signature})
                is_author = (arr_submission_v1.original or arr_submission_v1.id) in [note.id for note in author_submissions]

            if not is_author:
                raise openreview.OpenReviewException('Provided previous URL does not correspond to an ARR submission you are an author of. Only authors of the previous submission can link it.')

        # If provided previous URL but left a reassignment request blank
        if (not editor_reassignment_request or not reviewer_reassignment_request):
            raise openreview.OpenReviewException('Since you are re-submitting, please indicate if you would like the same editors/reviewers as your indicated previous submission')