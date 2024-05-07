def process(client, note, invitation):
    import datetime

    forum_note = client.get_note(note.forum)

    previous_references = client.get_references(referent=forum_note.id, invitation=note.invitation)
    if len(previous_references) > 0:
        if not client.get_process_logs(id=previous_references[0].id):
            raise openreview.OpenReviewException('There is currently a stage process running, please wait until it finishes to try again.')

    if 'Yes' in note.content.get('make_reviews_public', ''):
        if 'Everyone (submissions are public)' not in forum_note.content.get('submission_readers', '') and 'Make accepted submissions public and hide rejected submissions' not in forum_note.content.get('submission_readers', ''):
            raise openreview.OpenReviewException('Reviews cannot be released to the public since all papers are private')

    if 'Yes' in note.content.get('make_meta_reviews_public', ''):
        if 'Everyone (submissions are public)' not in forum_note.content.get('submission_readers', '') and 'Make accepted submissions public and hide rejected submissions' not in forum_note.content.get('submission_readers', ''):
            raise openreview.OpenReviewException('Meta reviews cannot be released to the public since all papers are private')

    if 'Yes' in note.content.get('make_decisions_public', ''):
        if 'Everyone (submissions are public)' not in forum_note.content.get('submission_readers', '') and 'Make accepted submissions public and hide rejected submissions' not in forum_note.content.get('submission_readers', ''):
            raise openreview.OpenReviewException('Decisions cannot be released to the public since all papers are private')

    if 'review_expiration_date' in note.content and 'review_deadline' in note.content:
        review_due_date = note.content.get('review_deadline', '').strip()
        review_exp_date = note.content.get('review_expiration_date', '').strip()
        try:
            review_exp_date = datetime.datetime.strptime(review_exp_date, '%Y/%m/%d %H:%M')
        except ValueError:
            review_exp_date = datetime.datetime.strptime(review_exp_date, '%Y/%m/%d')
        try:
            review_due_date = datetime.datetime.strptime(review_due_date, '%Y/%m/%d %H:%M')
        except ValueError:
            review_due_date = datetime.datetime.strptime(review_due_date, '%Y/%m/%d')

        if review_exp_date < review_due_date:
            raise openreview.OpenReviewException('Review expiration date should be after review deadline.')

    if 'meta_review_expiration_date' in note.content and 'meta_review_deadline' in note.content:
        meta_review_due_date = note.content.get('meta_review_deadline', '').strip()
        meta_review_exp_date = note.content.get('meta_review_expiration_date', '').strip()
        try:
            meta_review_exp_date = datetime.datetime.strptime(meta_review_exp_date, '%Y/%m/%d %H:%M')
        except ValueError:
            meta_review_exp_date = datetime.datetime.strptime(meta_review_exp_date, '%Y/%m/%d')
        try:
            meta_review_due_date = datetime.datetime.strptime(meta_review_due_date, '%Y/%m/%d %H:%M')
        except ValueError:
            meta_review_due_date = datetime.datetime.strptime(meta_review_due_date, '%Y/%m/%d')

        if meta_review_exp_date < meta_review_due_date:
            raise openreview.OpenReviewException('Meta review expiration date should be after meta review deadline.')