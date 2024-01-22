def process(client, edit, invitation):

    paper_link = edit.note.content['paper_link']['value']
    paper_forum = paper_link.split('=')[-1]

    try:
        client_v1=openreview.Client(baseurl=openreview.tools.get_base_urls(client)[0], token=client.token)
        arr_submission = client_v1.get_note(paper_forum)
    except openreview.OpenReviewException as e:
        raise openreview.OpenReviewException('Provided paper link does not correspond to a submission in OpenReview')

    if 'aclweb.org/ACL/ARR' not in arr_submission.invitation:
        raise openreview.OpenReviewException('Provided paper link does not correspond to an ARR submission')