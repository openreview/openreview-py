def process(client, edit, invitation):
    
    recommendation_field_name = edit.content['recommendation_field_name']['value']
    meta_review_content = edit.content['content']['value']

    meta_review_form_fields = [key for key in meta_review_content.keys() if 'delete' not in meta_review_content[key]]
    
    if recommendation_field_name not in meta_review_form_fields:
        raise openreview.OpenReviewException(f'"{recommendation_field_name}" does not exist in the meta review form fields')
    