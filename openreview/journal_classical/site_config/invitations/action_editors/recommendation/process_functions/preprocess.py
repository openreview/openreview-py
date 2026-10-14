def process(client, edge, invitation):
    # Compatibility adapter: keep Journal's availability gate, then add
    # JMLR's Regular-only recommendation policy and eligibility classifier.
    if edge.ddate:
        return
    journal = openreview.journal.JournalRequest.get_journal(client, "{{PROD_JOURNAL_ID}}")
    submission = client.get_note(edge.head)
    if submission.content.get('track_id', {}).get('value', 'Regular') != 'Regular':
        raise openreview.OpenReviewException('Action Editor suggestions are only collected for Regular submissions.')
    if submission.content.get('previous_JMLR_submission_url', {}).get('value'):
        raise openreview.OpenReviewException('Action Editor suggestions are not collected for resubmissions.')
    if client.get_edges(invitation='JMLR/Action_Editors/-/Regular_Ineligible', head='JMLR/Action_Editors', tail=edge.tail):
        raise openreview.OpenReviewException(f'Action Editor {edge.tail} is not Regular eligible.')
    availability = client.get_edges(invitation=journal.get_ae_availability_id(), tail=edge.tail)
    if availability and availability[0].label == 'Unavailable':
        raise openreview.OpenReviewException(f'Action Editor {edge.tail} is currently unavailable.')
