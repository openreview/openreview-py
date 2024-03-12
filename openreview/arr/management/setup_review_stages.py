def process(client, invitation):

    from openreview.stages.arr_content import (
        arr_official_review_content,
        arr_metareview_content
    )
    from openreview.venue import matching
    from datetime import datetime

    def fetch_date(field_name, to_datetime=False):
        value = invitation.content.get(field_name, {}).get('value')
        if value == 0:
            return None
        return value if not to_datetime else value/1000

    domain = client.get_group(invitation.domain)
    venue_id = domain.id
    request_form_id = domain.content['request_form_id']['value']

    client_v1 = openreview.Client(
        baseurl=openreview.tools.get_base_urls(client)[0],
        token=client.token
    )

    super_user = '~Super_User1'
    request_form = client_v1.get_note(request_form_id)
    support_group = request_form.invitation.split('/-/')[0]

    reviewing_start_date = fetch_date('reviewing_start_date', to_datetime=True)
    reviewing_due_date = fetch_date('reviewing_due_date', to_datetime=True)
    reviewing_exp_date = fetch_date('reviewing_exp_date', to_datetime=True)
    metareviewing_start_date = fetch_date('metareviewing_start_date', to_datetime=True)
    metareviewing_due_date = fetch_date('metareviewing_due_date', to_datetime=True)
    metareviewing_exp_date = fetch_date('metareviewing_exp_date', to_datetime=True)

    # Create review stages
    review_stage_note = openreview.Note(
        content={
            'review_start_date': datetime.fromtimestamp(reviewing_start_date).strftime('%Y/%m/%d'),
            'review_deadline': datetime.fromtimestamp(reviewing_due_date).strftime('%Y/%m/%d'),
            'review_expiration_date': datetime.fromtimestamp(reviewing_exp_date).strftime('%Y/%m/%d'),
            'make_reviews_public': 'No, reviews should NOT be revealed publicly when they are posted',
            'release_reviews_to_authors': 'No, reviews should NOT be revealed when they are posted to the paper\'s authors',
            'release_reviews_to_reviewers': 'Reviews should be immediately revealed to the paper\'s reviewers who have already submitted their review',
            'remove_review_form_options': 'title,rating,review',
            'email_program_chairs_about_reviews': 'No, do not email program chairs about received reviews',
            'review_rating_field_name': 'overall_assessment',
            'additional_review_form_options': arr_official_review_content
        },
        forum=request_form_id,
        invitation='{}/-/Request{}/Review_Stage'.format(support_group, request_form.number),
        readers=['{}/Program_Chairs'.format(venue_id), support_group],
        referent=request_form_id,
        replyto=request_form_id,
        signatures=[super_user],
        writers=[]
    )
    client_v1.post_note(review_stage_note)

    meta_review_stage_note = openreview.Note(
        content={
            'make_meta_reviews_public': 'No, meta reviews should NOT be revealed publicly when they are posted',
            'meta_review_start_date': datetime.fromtimestamp(metareviewing_start_date).strftime('%Y/%m/%d'),
            'meta_review_deadline': datetime.fromtimestamp(metareviewing_due_date).strftime('%Y/%m/%d'),
            "meta_review_expiration_date": datetime.fromtimestamp(metareviewing_exp_date).strftime('%Y/%m/%d'),
            'release_meta_reviews_to_authors': 'No, meta reviews should NOT be revealed when they are posted to the paper\'s authors',
            'release_meta_reviews_to_reviewers': 'Meta reviews should be immediately revealed to the paper\'s reviewers who have already submitted their review',
            'additional_meta_review_form_options': arr_metareview_content,
            'remove_meta_review_form_options': ['recommendation', 'confidence']
        },
        forum=request_form_id,
        invitation='{}/-/Request{}/Meta_Review_Stage'.format(support_group, request_form.number),
        readers=['{}/Program_Chairs'.format(venue_id), support_group],
        referent=request_form_id,
        replyto=request_form_id,
        signatures=[super_user],
        writers=[]
    )
    client_v1.post_note(meta_review_stage_note)