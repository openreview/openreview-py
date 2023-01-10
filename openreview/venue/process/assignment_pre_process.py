def process_update(client, edge, invitation, existing_edge):

    domain = client.get_group(edge.domain)
    venue_id = domain.id
    submission_name = domain.content['submission_name']['value']
    review_name = domain.content['review_name']['value']
    reviewers_anon_name = domain.content['reviewers_anon_name']['value']
    
    if edge.ddate:
        paper=client.get_note(edge.head)

        paper_group_id=f'{venue_id}/{submission_name}{paper.number}'

        reviews=client.get_notes(invitation=f'{paper_group_id}/-/{review_name}')

        if not reviews:
            return

        groups=client.get_groups(regex=f'{paper_group_id}/{reviewers_anon_name}', signatory=edge.tail)

        if not groups:
            raise openreview.OpenReviewException(f'Can not remove assignment, signatory groups not found for {edge.tail}.')


        for review in reviews:
            if review.signatures[0] == groups[0].id:
                raise openreview.OpenReviewException(f'Can not remove assignment, the user {edge.tail} already posted a review.')

