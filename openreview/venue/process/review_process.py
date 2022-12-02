def process(client, edit, invitation):

    domain = client.get_group(edit.domain)
    venue_id = domain.id
    short_name = domain.get_content_value('subtitle')
    authors_name = domain.get_content_value('authors_name')
    submission_name = domain.get_content_value('submission_name')
    reviewers_name = domain.get_content_value('reviewers_name')
    reviewers_submitted_name = domain.get_content_value('reviewers_submitted_name')
    review_name = domain.get_content_value('review_name')

    submission = client.get_note(edit.note.forum)
    paper_group_id=f'{venue_id}/{submission_name}{submission.number}'
    review = client.get_note(edit.note.id)

    capital_review_name = review_name.replace('_', ' ')
    review_name = capital_review_name.lower()

    content = f'To view the {review_name}, click here: https://openreview.net/forum?id={submission.id}&noteId={edit.note.id}'

    if domain.get_content_value('review_email_pcs'):
        client.post_message(
            recipients=[domain.get_content_value('program_chairs_id')],
            subject=f'''[{short_name}] A {review_name} has been received on Paper number: {submission.number}, Paper title: "{submission.content['title']['value']}"''',
            message=f''''We have received a review on a submission to {short_name}.
            
{content}
'''
        )        

    area_chairs_name = domain.get_content_value('area_chairs_name')
    paper_area_chairs_id = f'{paper_group_id}/{area_chairs_name}'
    if area_chairs_name and ('everyone' in review.readers or paper_area_chairs_id in review.readers):
        client.post_message(
            recipients=[paper_area_chairs_id],
            subject=f'''[{short_name}] {capital_review_name} posted to your assigned Paper number: {submission.number}, Paper title: "{submission.content['title']['value']}"''',
            message=f''''A submission to {short_name}, for which you are an official area chair, has received a review.

Paper number: {submission.number}

Paper title: {submission.content['title']['value']}

{content}
'''
        )

    paper_reviewers_id = f'{paper_group_id}/{reviewers_name}'
    paper_reviewers_submitted_id = f'{paper_group_id}/{reviewers_submitted_name}'
    if 'everyone' in review.readers or paper_reviewers_id in review.readers:
        client.post_message(
            recipients=[paper_reviewers_id],
            subject=f'''[{short_name}] {capital_review_name} posted to your assigned Paper number: {submission.number}, Paper title: "{submission.content['title']['value']}"''',
            message=f''''A submission to {short_name}, for which you are a reviewer, has received a review.

Paper number: {submission.number}

Paper title: {submission.content['title']['value']}

{content}
'''
        )
    elif paper_reviewers_submitted_id in review.readers:
        client.post_message(
            recipients=[paper_reviewers_submitted_id],
            subject=f'''[{short_name}] {capital_review_name} posted to your assigned Paper number: {submission.number}, Paper title: "{submission.content['title']['value']}"''',
            message=f''''A submission to {short_name}, for which you are a reviewer, has received a review.

Paper number: {submission.number}

Paper title: {submission.content['title']['value']}

{content}
'''
        )

    paper_authors_id = f'{paper_group_id}/{authors_name}'
    if 'everyone' in  review.readers or paper_authors_id in review.readers:
        client.post_message(
            recipients=[paper_authors_id],
            subject=f'''[{short_name}] {capital_review_name} posted to your submission - Paper number: {submission.number}, Paper title: "{submission.content['title']['value']}"''',
            message=f''''Your submission to {short_name} has received a review.

{content}
'''
        )

    if paper_reviewers_submitted_id:
        client.add_members_to_group(paper_reviewers_submitted_id, review.signatures[0])
    

