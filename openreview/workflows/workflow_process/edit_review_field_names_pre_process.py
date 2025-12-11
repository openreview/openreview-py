def process(client, edit, invitation):
    
    rating_field_name = edit.content['rating_field_name']['value']
    confidence_field_name = edit.content['confidence_field_name']['value']
    review_content = edit.content['content']['value']

    review_form_fields = [key for key in review_content.keys() if 'delete' not in review_content[key]]
    
    if rating_field_name not in review_form_fields:
        raise openreview.OpenReviewException(f'"{rating_field_name}" does not exist in the review form fields')
    
    if confidence_field_name not in review_form_fields:
        raise openreview.OpenReviewException(f'"{confidence_field_name}" does not exist in the review form fields')
    