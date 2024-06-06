def process(client, edit, invitation):

    paper_link = edit.note.content['paper_link']['value']
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

    if (arr_submission_v1 and arr_submission_v1.id != arr_submission_v1.forum) or (arr_submission_v2 and arr_submission_v2.id != arr_submission_v2.forum):
            raise openreview.OpenReviewException('Provided paper link does not correspond to an ARR submission. Make sure the link points to a submission and not to a reply.')

    if arr_submission_v1 and 'aclweb.org/ACL/ARR' in arr_submission_v1.invitation and not arr_submission_v1.invitation.endswith('Blind_Submission'):
        raise openreview.OpenReviewException('Provided paper link does not point to a blind submission. Make sure you get the url to your submission from the browser')