def process_update(client, edge, invitation, existing_edge):

    domain = client.get_group(edge.domain)
    venue_id = domain.id
    submission_name = domain.content['submission_name']['value']

    reviewers_id = invitation.content['reviewers_id']['value']
    review_name = domain.content.get('review_name', {}).get('value') if reviewers_id == domain.content['reviewers_id']['value'] else domain.content.get('meta_review_name', {}).get('value')
    reviewers_anon_name = invitation.content['reviewers_anon_name']['value']
    reviewers_name = invitation.content['reviewers_name']['value']
    paper=client.get_note(edge.head)
    paper_group_id=f'{venue_id}/{submission_name}{paper.number}'

    if edge.ddate:

        if not review_name:
            return

        reviews=client.get_notes(invitation=f'{paper_group_id}/-/{review_name}')

        if not reviews:
            return

        groups=client.get_groups(prefix=f'{paper_group_id}/{reviewers_anon_name}', signatory=edge.tail)

        if not groups:
            raise openreview.OpenReviewException(f'Can not remove assignment, signatory groups not found for {edge.tail}.')


        for review in reviews:
            if review.signatures[0] == groups[0].id:
                raise openreview.OpenReviewException(f'Can not remove assignment, the user {edge.tail} already posted a {review_name}')

    else:
        group = openreview.tools.get_group(client, f'{paper_group_id}/{reviewers_name}')
        if not group:
            raise openreview.OpenReviewException(f'Can not make assignment, submission reviewers group not found.')

