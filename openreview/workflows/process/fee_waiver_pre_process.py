def process(client, edit, invitation):

    note = edit.note
    content = note.content or {}

    if note.replyto != note.forum:
        raise openreview.OpenReviewException('A fee waiver must reply to the submission itself.')

    if not content.get('countries', {}).get('value') and not content.get('comment', {}).get('value'):
        raise openreview.OpenReviewException('Give the countries or a comment that explains the waiver.')

    payment_name = invitation.get_content_value('payment_name')
    fee_invitations = [fee_invitation for fee_invitation in client.get_invitations(replyForum=note.forum, type='payment', expired=True) if fee_invitation.id.endswith(f'/-/{payment_name}')]
    if not fee_invitations:
        raise openreview.OpenReviewException('This submission has no submission fee to waive.')

    settled_payments = [payment for payment in client.get_all_payments(note=note.forum) if payment.status in ['paid', 'waived']]
    if settled_payments:
        raise openreview.OpenReviewException(f'The submission fee of this submission is already {settled_payments[0].status}.')

    if client.get_notes(invitation=invitation.id, forum=note.forum, limit=1):
        raise openreview.OpenReviewException('The submission fee of this submission is already being waived.')
