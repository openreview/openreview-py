"""Classify JMLR AE continuity without changing Journal assignment state."""


def active_prior_ae_assignment(client, journal, submission, action_editor_id):
    previous_url = submission.content.get('previous_JMLR_submission_url', {}).get('value')
    if not previous_url:
        return False
    previous_id = previous_url.split('?id=')[-1].split('&')[0]
    return any(
        client.get_edges(invitation=assignment_id, head=previous_id, tail=action_editor_id)
        for assignment_id in (
            journal.get_ae_assignment_id(),
            journal.get_ae_assignment_id(archived=True),
        )
    )
