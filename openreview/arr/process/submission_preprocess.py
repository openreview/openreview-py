def process(client, edit, invitation):
    # TODO: Check for reviews and meta-reviews
    editor_reassignment_field = edit.note.content.get('reassignment_request_action_editor', {}).get('value', '')
    editor_reassignment_request = len(editor_reassignment_field) > 0 and 'not a resubmission' not in editor_reassignment_field
    reviewer_reassignment_field = edit.note.content.get('reassignment_request_reviewers', {}).get('value', '')
    reviewer_reassignment_request = len(reviewer_reassignment_field) > 0 and 'not a resubmission' not in reviewer_reassignment_field
    paper_link = edit.note.content.get('previous_URL', {}).get('value')
    volunteers = edit.note.content.get('reviewing_volunteers', {}).get('value', [])
    authorids = edit.note.content.get('authorids').get('value')

    if paper_link:
        paper_forum = paper_link.split('=')[-1]
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

    # If provided previous URL but left a reassignment request blank
    if paper_link and (not editor_reassignment_request or not reviewer_reassignment_request):
      raise openreview.OpenReviewException('Since you are re-submitting, please indicate if you would like the same editors/reviewers as your indicated previous submission')

    # If no previous URL but selected reassignment
    if not paper_link and (editor_reassignment_request or reviewer_reassignment_request):
      raise openreview.OpenReviewException('You have selected a reassignment request with no previous URL. Please enter a URL or close and re-open the submission form to clear your reassignment request')
    
    for v in volunteers:
        if v not in authorids:
            raise openreview.OpenReviewException(f'Volunteer {v} is not an author of this submission')