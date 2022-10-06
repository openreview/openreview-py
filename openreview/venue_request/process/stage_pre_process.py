def process(client, note, invitation):

    forum_note = client.get_note(note.forum)

    if 'Yes' in note.content.get('make_reviews_public', ''):
        if 'Everyone (submissions are public)' not in forum_note.content.get('submission_readers', '') and 'Make accepted submissions public and hide rejected submissions' not in forum_note.content.get('submission_readers', ''):
            raise openreview.OpenReviewException('Reviews cannot be released to the public since all papers are private')

    if 'Yes' in note.content.get('make_meta_reviews_public', ''):
        if 'Everyone (submissions are public)' not in forum_note.content.get('submission_readers', '') and 'Make accepted submissions public and hide rejected submissions' not in forum_note.content.get('submission_readers', ''):
            raise openreview.OpenReviewException('Meta reviews cannot be released to the public since all papers are private')

    if 'Yes' in note.content.get('make_decisions_public', ''):
        if 'Everyone (submissions are public)' not in forum_note.content.get('submission_readers', '') and 'Make accepted submissions public and hide rejected submissions' not in forum_note.content.get('submission_readers', ''):
            raise openreview.OpenReviewException('Decisions cannot be released to the public since all papers are private')
