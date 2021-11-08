def process(client, note, invitation):

    if 'Yes' in note.content['compute_affinity_scores'] and 'upload_affinity_scores' in note.content['compute_affinity_scores']:
        raise openreview.OpenReviewException('Either upload your own affinity scores or select affinity scores computed by OpenReview')