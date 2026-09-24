def process(client, edge, invitation):
    """Keep the Journal Python preprocess entry point as the first token."""
    return _process_with_jmlr_assignment_policy(client, edge, invitation)

# JMLR delta: share the server-only structural linked-submission resolver.
# {{PYTHON_SCRIPT_FILE:invitations/venue/under_review/previous_submission_reviewer_policy.py}}


def _process_with_jmlr_assignment_policy(client, edge, invitation):
    journal = openreview.journal.JournalRequest.get_journal(
        client, "{{PROD_JOURNAL_ID}}"
    )
    external_acceptance_namespace = {}
    exec(
        "{{PYTHON_SCRIPT_JSON:invitations/venue/under_review/external_reviewer_acceptance.py}}",
        external_acceptance_namespace,
    )
    reviewer_assignment_edges_namespace = {}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/reviewer_assignment_edges.py}}", reviewer_assignment_edges_namespace)
    submission = client.get_note(edge.head)
    assignment_invitation_id = (
        getattr(edge, 'invitation', None)
        or getattr(invitation, 'id', None)
        or journal.get_reviewer_assignment_id()
    )

    profile_identity_namespace = {'openreview': openreview, 'client': client}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/profile_identity_helpers.py}}", profile_identity_namespace)
    add_profile_identities = profile_identity_namespace['add_profile_identities']

    def actor_identities():
        identities = []
        add_profile_identities(identities, getattr(edge, 'tauthor', None))
        for edge_signature in getattr(edge, 'signatures', None) or []:
            add_profile_identities(identities, edge_signature)
        return identities

    def format_date(timestamp):
        date = datetime.datetime.fromtimestamp(timestamp / 1000, datetime.timezone.utc)
        return f'{date.strftime("%B")} {date.day}, {date.year}'

    def unavailable_message(availability_edge, now):
        if availability_edge and availability_edge.weight and availability_edge.weight > now:
            return f'Reviewer {edge.tail} is unavailable until {format_date(availability_edge.weight)}.'
        return f'Reviewer {edge.tail} is unavailable indefinitely.'

    def is_available(availability_edge, now):
        if not availability_edge or availability_edge.label != 'Unavailable':
            return True
        return bool(availability_edge.weight and availability_edge.weight <= now)

    def compute_assignment_conflicts(profile_id):
        try:
            return journal.assignment.compute_conflicts(submission, profile_id)
        except Exception:
            raise openreview.OpenReviewException(
                'Can not verify assignment conflicts; assignment was not changed.'
            )

    actor_ids = actor_identities()
    for actor_id in actor_ids:
        if not (actor_id.startswith('~') or '@' in actor_id):
            continue
        if compute_assignment_conflicts(actor_id):
            raise openreview.OpenReviewException(
                f'Conflicted users can not edit assignments for this submission: {submission.number}'
            )

    venue_id = submission.content.get('venueid', {}).get('value')
    if venue_id != journal.under_review_venue_id:
        raise openreview.OpenReviewException(
            f'Can not edit assignments for this submission: {venue_id}'
        )

    decisions = client.get_notes(
        invitation=journal.get_ae_decision_id(number=submission.number)
    )
    if any(not decision.ddate for decision in decisions):
        raise openreview.OpenReviewException(
            f'Can not edit assignments, a decision has already been posted for '
            f'this submission: {submission.number}.'
        )

    if edge.ddate:
        reviews = client.get_notes(
            invitation=journal.get_review_id(number=submission.number)
        )
        if not reviews:
            return
        groups = client.get_groups(
            prefix=journal.get_reviewers_id(number=submission.number, anon=True),
            signatory=edge.tail,
        )
        if not groups:
            raise openreview.OpenReviewException(
                f'Can not remove assignment, signatory groups not found for {edge.tail}.'
            )
        for review in reviews:
            if review.signatures[0] == groups[0].id:
                raise openreview.OpenReviewException(
                    f'Can not remove assignment, the user {edge.tail} already posted a review.'
                )
        return

    global_assignment_invitation_id = journal.get_reviewer_assignment_id()
    paper_assignment_invitation_id = journal.get_reviewer_assignment_id(number=submission.number)
    if assignment_invitation_id != global_assignment_invitation_id:
        raise openreview.OpenReviewException(
            f'Can not add assignment through {assignment_invitation_id}; '
            f'use {global_assignment_invitation_id}.'
        )
    active_invitation = openreview.tools.get_invitation(
        client, paper_assignment_invitation_id
    )
    if active_invitation is None:
        raise openreview.OpenReviewException(
            'Can not add assignment, invitation is not active yet.'
        )

    existing_assignments = reviewer_assignment_edges_namespace[
        'reviewer_assignment_edges_for_submission'
    ](client, journal, submission, tail=edge.tail)
    if any(not assignment.ddate for assignment in existing_assignments):
        raise openreview.OpenReviewException(
            f'Can not add assignment, reviewer {edge.tail} is already assigned to this paper.'
        )

    if compute_assignment_conflicts(edge.tail):
        raise openreview.OpenReviewException(
            f'Can not add assignment, conflict detected for {edge.tail}.'
        )

    if not client.get_groups(member=edge.tail, id=journal.get_reviewers_id()):
        raise openreview.OpenReviewException(
            f'Can not add assignment, reviewer {edge.tail} is not a member of '
            f'{journal.get_reviewers_id()}.'
        )

    now = openreview.tools.datetime_millis(datetime.datetime.now())
    edges = client.get_edges(invitation=journal.get_reviewer_availability_id(), tail=edge.tail)
    availability_edge = edges[0] if edges else None
    if not is_available(availability_edge, now):
        raise openreview.OpenReviewException(
            unavailable_message(availability_edge, now)
        )

    is_external_acceptance = external_acceptance_namespace[
        'is_external_reviewer_acceptance_assignment'
    ](client, journal, edge)
    if is_external_acceptance:
        return

    # The lean continuity contract bypasses only configured pending-review/load.
    # Journal has no reviewer assignment cooldown, so JMLR adds none here.
    if active_prior_reviewer_assignment(client, journal, submission, edge.tail):
        return

    pending_review_edges = client.get_edges(invitation=journal.get_reviewer_pending_review_id(), tail=edge.tail)
    pending_review_count = pending_review_edges[0].weight if pending_review_edges else 0
    max_papers = journal.get_reviewers_max_papers()
    custom_max_paper_edges = client.get_edges(invitation=f'{journal.get_reviewers_id()}/-/Custom_Max_Papers', tail=edge.tail)
    if custom_max_paper_edges and custom_max_paper_edges[0].weight is not None:
        max_papers = custom_max_paper_edges[0].weight
    if pending_review_count >= max_papers:
        raise openreview.OpenReviewException(
            f'Can not add assignment, reviewer {edge.tail} has reached the '
            f'maximum active paper load of {max_papers}.'
        )
