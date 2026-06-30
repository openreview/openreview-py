def process(client, edge, invitation):

    journal = openreview.journal.JournalRequest.get_journal(client, "{{PROD_JOURNAL_ID}}")
    assignment_conflict_namespace = {}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/assignment_conflicts.py}}", assignment_conflict_namespace)
    external_reviewer_acceptance_namespace = {}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/under_review/external_reviewer_acceptance.py}}", external_reviewer_acceptance_namespace)
    reviewer_assignment_edges_namespace = {}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/reviewer_assignment_edges.py}}", reviewer_assignment_edges_namespace)
    cooldown_days = int("{{REVIEWER_NEW_ASSIGNMENT_COOLDOWN_DAYS}}")

    submission = client.get_note(edge.head)
    assignment_invitation_id = getattr(edge, 'invitation', None) or getattr(invitation, 'id', None) or journal.get_reviewer_assignment_id()

    ## authors should not be able to edit assignments
    authors_group_id = journal.get_authors_id(number=submission.number)
    def group_has_member(group_id, member_id):
        try:
            return bool(client.get_groups(id=group_id, member=member_id))
        except Exception as error:
            if 'Group Not Found' in str(error) or 'NotFoundError' in str(error):
                return False
            raise

    def add_identity(identities, value):
        if value and isinstance(value, str) and value not in identities:
            identities.append(value)

    def add_profile_identities(identities, value):
        add_identity(identities, value)
        if not value or not isinstance(value, str):
            return
        if not value.startswith('~') and '@' not in value:
            return
        try:
            profiles = openreview.tools.get_profiles(client, [value])
            profile = profiles[0] if profiles else None
        except Exception:
            profile = None
        if not profile:
            return
        add_identity(identities, getattr(profile, 'id', None))
        try:
            add_identity(identities, profile.get_preferred_email())
        except Exception:
            pass
        profile_content = getattr(profile, 'content', {}) or {}
        add_identity(identities, profile_content.get('preferredEmail'))
        for email in profile_content.get('emails', []) or []:
            add_identity(identities, email)
        for email in profile_content.get('preferredEmails', []) or []:
            add_identity(identities, email)

    def actor_identities():
        identities = []
        add_profile_identities(identities, getattr(edge, 'tauthor', None))
        for edge_signature in getattr(edge, 'signatures', None) or []:
            add_profile_identities(identities, edge_signature)
        return identities

    def format_month(timestamp):
        month_start = datetime.datetime.fromtimestamp(timestamp / 1000, datetime.timezone.utc)
        return f'{month_start.strftime("%B")} {month_start.day}, {month_start.year}'

    def unavailable_message(role, profile_id, availability_edge, now):
        if availability_edge and availability_edge.weight and availability_edge.weight > now:
            return f'{role} {profile_id} is unavailable until {format_month(availability_edge.weight)}.'
        return f'{role} {profile_id} is unavailable indefinitely.'

    def is_available(availability_edge, now):
        if not availability_edge:
            return True
        if availability_edge.label != 'Unavailable':
            return True
        if availability_edge.weight and availability_edge.weight <= now:
            return True
        return False

    authorids = submission.content.get('authorids', {}).get('value') or []
    actor_ids = actor_identities()
    if any(actor_id in authorids or group_has_member(authors_group_id, actor_id) for actor_id in actor_ids):
        raise openreview.OpenReviewException(f'Authors can not edit assignments for this submission: {submission.number}')    

    for actor_id in actor_ids:
        if not (actor_id.startswith('~') or '@' in actor_id):
            continue
        try:
            hard_actor_conflict = assignment_conflict_namespace['get_assignment_conflict'](client, journal, submission, actor_id)
            if hard_actor_conflict:
                raise openreview.OpenReviewException(f'Conflicted users can not edit assignments for this submission: {submission.number}')
            openreview_actor_conflict = assignment_conflict_namespace['get_assignment_conflict'](client, journal, submission, actor_id, conflict_type='openreview')
            if openreview_actor_conflict:
                print(
                    f'OpenReview-computed actor conflict for {actor_id} on submission {submission.number} '
                    'is advisory for assignment operations.'
                )
        except openreview.OpenReviewException:
            raise
        except Exception:
            pass

    venue_id = submission.content.get('venueid', {}).get('value')
    if venue_id not in [journal.under_review_venue_id]:
        raise openreview.OpenReviewException(f'Can not edit assignments for this submission: {venue_id}')

    # Invitation availability is not lifecycle state; only an active Decision note is.
    # This blocks stale reviewer-assignment forms after any terminal or revision decision.
    def decision_made():
        return any(
            not decision.ddate
            for decision in client.get_notes(invitation=journal.get_ae_decision_id(number=submission.number))
        )

    if decision_made():
        raise openreview.OpenReviewException(f'Can not edit assignments, a decision has already been posted for this submission: {submission.number}.')

    if edge.ddate:

        submission=client.get_note(edge.head)

        reviews=client.get_notes(invitation=journal.get_review_id(number=submission.number))

        if not reviews:
            return

        groups=client.get_groups(prefix=journal.get_reviewers_id(number=submission.number, anon=True), signatory=edge.tail)

        if not groups:
            raise openreview.OpenReviewException(f'Can not remove assignment, signatory groups not found for {edge.tail}.')


        for review in reviews:
            if review.signatures[0] == groups[0].id:
                raise openreview.OpenReviewException(f'Can not remove assignment, the user {edge.tail} already posted a review.')

    else:
        ## Check Paper Assignment invitation is active
        paper_assignment_invitation_id = journal.get_reviewer_assignment_id(number=submission.number)
        if assignment_invitation_id != paper_assignment_invitation_id:
            raise openreview.OpenReviewException(f'Can not add assignment through {assignment_invitation_id}; use {paper_assignment_invitation_id}.')

        invitation = openreview.tools.get_invitation(client, paper_assignment_invitation_id)

        if invitation is None:
           raise openreview.OpenReviewException(f'Can not add assignment, invitation is not active yet.')

        existing_assignments = reviewer_assignment_edges_namespace['reviewer_assignment_edges_for_submission'](
            client,
            journal,
            submission,
            tail=edge.tail,
        )
        if any(not existing_assignment.ddate for existing_assignment in existing_assignments):
            raise openreview.OpenReviewException(f'Can not add assignment, reviewer {edge.tail} is already assigned to this paper.')

        def get_previous_forum_id(note):
            def parse_forum_id(url):
                if not url or url == "N/A":
                    return None
                try:
                    from urllib.parse import parse_qs, urlparse
                    parsed = urlparse(str(url))
                    forum_ids = parse_qs(parsed.query).get("id")
                    if forum_ids and forum_ids[0]:
                        return forum_ids[0]
                except Exception:
                    pass
                try:
                    return str(url).split("forum?id=", 1)[1].split("&", 1)[0]
                except Exception:
                    return None

            def previous_forum_id_from_list(note):
                import re
                value = note.content.get("previous_JMLR_submissions", {}).get("value") or ""
                match = re.search(r"forum\?id=([A-Za-z0-9_-]+)", str(value))
                return match.group(1) if match else None

            previous_submission_url = note.content.get("previous_JMLR_submission_URL", {}).get("value")
            if not previous_submission_url or previous_submission_url == "N/A":
                previous_submission_number = note.content.get("previous_JMLR_submission_number", {}).get("value")
                if not previous_submission_number or str(previous_submission_number).strip().upper() == "N/A":
                    return previous_forum_id_from_list(note)
                try:
                    previous_notes = client.get_notes(
                        invitation=f"{journal.venue_id}/-/Submission",
                        number=int(str(previous_submission_number).strip())
                    )
                    return previous_notes[0].id if previous_notes else None
                except Exception:
                    return None
            return parse_forum_id(previous_submission_url)

        def is_resubmission_reassignment(note, reviewer_id):
            previous_forum_id = get_previous_forum_id(note)
            if not previous_forum_id:
                return False
            previous_assignment_invitation_ids = [
                journal.get_reviewer_assignment_id(),
                journal.get_reviewer_assignment_id(archived=True),
            ]
            try:
                previous_note = client.get_note(previous_forum_id)
                previous_assignment_invitation_ids.append(journal.get_reviewer_assignment_id(number=previous_note.number))
            except Exception:
                pass
            for previous_assignment_invitation_id in previous_assignment_invitation_ids:
                try:
                    previous_assignments = client.get_edges(
                        invitation=previous_assignment_invitation_id,
                        head=previous_forum_id,
                        tail=reviewer_id
                    )
                except Exception:
                    continue
                if any(not previous_assignment.ddate for previous_assignment in previous_assignments):
                    return True
            return False

        resubmission_reassignment = is_resubmission_reassignment(submission, edge.tail)

        hard_conflict = assignment_conflict_namespace['get_assignment_conflict'](client, journal, submission, edge.tail)
        if hard_conflict:
            raise openreview.OpenReviewException(f'Can not add assignment, {edge.tail} appears in the submission {hard_conflict["reason"]}.')

        previous_reviewer_conflict_override_label = 'Previous Reviewer Conflict Override'
        ae_openreview_conflict_override_label = 'AE OpenReview Conflict Override'
        eic_openreview_conflict_override_label = 'EIC OpenReview Conflict Override'

        is_external_reviewer_acceptance = external_reviewer_acceptance_namespace['is_external_reviewer_acceptance_assignment'](client, journal, edge)

        ## Check conflicts
        openreview_conflict = assignment_conflict_namespace['get_assignment_conflict'](client, journal, submission, edge.tail, conflict_type='openreview')
        if openreview_conflict and not is_external_reviewer_acceptance and not (
            (resubmission_reassignment and edge.label == previous_reviewer_conflict_override_label) or
            edge.label in [ae_openreview_conflict_override_label, eic_openreview_conflict_override_label]
        ):
           raise openreview.OpenReviewException(f'Can not add assignment, conflict detected for {edge.tail}.')

        is_normal_reviewer = bool(client.get_groups(member=edge.tail, id=journal.get_reviewers_id()))

        ## Existing-reviewer assignment only accepts official reviewer members.
        ## External email/profile invitations use Invite_Assignment instead.
        if not is_normal_reviewer:
            raise openreview.OpenReviewException(f'Can not add assignment, reviewer {edge.tail} is not a member of {journal.get_reviewers_id()}.')

        now = openreview.tools.datetime_millis(datetime.datetime.now())

        ## Check availability
        edges = client.get_edges(invitation=journal.get_reviewer_availability_id(), tail=edge.tail)
        availability_edge = edges[0] if edges else None
        if not is_available(availability_edge, now):
           raise openreview.OpenReviewException(unavailable_message('Reviewer', edge.tail, availability_edge, now))

        ## Resubmission continuity copies previous reviewers without normal new-assignment
        ## cooldown/load restrictions, but role, conflict, and availability checks still apply.
        if resubmission_reassignment:
            return

        ## Check if it is a volunteer and skip the pending reviews check
        if client.get_groups(member=edge.tail, id=journal.get_solicit_reviewers_id(number=submission.number)):
            return

        if is_external_reviewer_acceptance:
            return

        cooldown_millis = cooldown_days * 24 * 60 * 60 * 1000
        min_assignment_date = now - cooldown_millis
        recent_assignment_edges = reviewer_assignment_edges_namespace['reviewer_assignment_edges_for_tail'](
            client,
            journal,
            edge.tail,
            active_only=True,
        )
        for recent_assignment in recent_assignment_edges:
            if recent_assignment.ddate:
                continue
            if recent_assignment.head == edge.head:
                continue
            if not recent_assignment.cdate or recent_assignment.cdate < min_assignment_date:
                continue

            recent_submission = client.get_note(recent_assignment.head)
            if is_resubmission_reassignment(recent_submission, edge.tail):
                continue

            recent_assignment_date = datetime.datetime.fromtimestamp(recent_assignment.cdate / 1000).strftime("%Y-%m-%d")
            next_assignment_date = datetime.datetime.fromtimestamp((recent_assignment.cdate + cooldown_millis) / 1000).strftime("%Y-%m-%d")
            raise openreview.OpenReviewException(
                f'Reviewer {edge.tail} was assigned new paper {recent_submission.number} on {recent_assignment_date}. '
                f'Please wait until {next_assignment_date} before assigning another new paper. '
                'Resubmission reassignment to a previous reviewer is allowed and does not count toward this limit.'
            )

        ## Check pending reviews for official reviewers
        pending_review_edges = client.get_edges(invitation=journal.get_reviewer_pending_review_id(), tail=edge.tail)
        pending_review_count = pending_review_edges[0].weight if pending_review_edges else 0
        max_papers = journal.get_reviewers_max_papers()
        custom_max_paper_edges = client.get_edges(invitation=f'{journal.get_reviewers_id()}/-/Custom_Max_Papers', tail=edge.tail)
        if custom_max_paper_edges and custom_max_paper_edges[0].weight is not None:
            max_papers = custom_max_paper_edges[0].weight
        if pending_review_count >= max_papers:
            raise openreview.OpenReviewException(f'Can not add assignment, reviewer {edge.tail} has reached the maximum active paper load of {max_papers}.')
