def _reviewer_affinity_result_value(row, keys):
    for key in keys:
        if key in row:
            return row[key]
    return None


def previous_submission_id_from_note(note):
    import re

    previous_url = note.content.get('previous_JMLR_submission_URL', {}).get('value') or ''
    match = re.search(r'forum\?id=([A-Za-z0-9_-]+)', str(previous_url))
    if match:
        return match.group(1)
    previous_list = note.content.get('previous_JMLR_submissions', {}).get('value') or ''
    match = re.search(r'forum\?id=([A-Za-z0-9_-]+)', str(previous_list))
    return match.group(1) if match else ''


def previous_submission_number_from_note(note):
    import re

    previous_number = str(note.content.get('previous_JMLR_submission_number', {}).get('value') or '').strip()
    if previous_number and previous_number.upper() != 'N/A':
        return previous_number
    previous_list = note.content.get('previous_JMLR_submissions', {}).get('value') or ''
    match = re.search(r'Paper\s+([0-9]+)', str(previous_list))
    return match.group(1) if match else ''


def _flatten_reviewer_affinity_result_dicts(value):
    rows = []
    if isinstance(value, dict):
        rows.append(value)
        for child in value.values():
            rows.extend(_flatten_reviewer_affinity_result_dicts(child))
    elif isinstance(value, list):
        for child in value:
            rows.extend(_flatten_reviewer_affinity_result_dicts(child))
    return rows


def extract_reviewer_affinity_scores(results, note_id):
    scores = {}
    note_keys = ('submission', 'submission_id', 'submissionId', 'paper', 'paper_id', 'paperId', 'forum', 'note', 'note_id', 'noteId', 'head', 'entityB', 'id')
    user_keys = ('user', 'user_id', 'userId', 'profile', 'profile_id', 'profileId', 'member', 'member_id', 'memberId', 'tail', 'entityA')
    score_keys = ('score', 'weight', 'value', 'similarity')
    for row in _flatten_reviewer_affinity_result_dicts(results):
        result_note_id = _reviewer_affinity_result_value(row, note_keys)
        if isinstance(result_note_id, dict):
            result_note_id = _reviewer_affinity_result_value(result_note_id, ('id', 'forum', 'noteId'))
        if result_note_id == note_id:
            for score_map_key in ('scores', 'scoreByUser', 'userScores', 'members', 'users'):
                score_map = row.get(score_map_key)
                if isinstance(score_map, dict):
                    for profile_id, score_value in score_map.items():
                        if isinstance(profile_id, str) and profile_id.startswith('~'):
                            try:
                                scores[profile_id] = float(score_value)
                            except Exception:
                                pass
        profile_id = _reviewer_affinity_result_value(row, user_keys)
        score_value = _reviewer_affinity_result_value(row, score_keys)
        if isinstance(profile_id, dict):
            profile_id = _reviewer_affinity_result_value(profile_id, ('id', 'profile_id', 'user'))
        if result_note_id != note_id or not isinstance(profile_id, str) or not profile_id.startswith('~'):
            continue
        try:
            scores[profile_id] = float(score_value)
        except Exception:
            continue
    return scores


def active_reviewer_affinity_edges_exist(client, journal, note):
    try:
        edges = client.get_edges(
            invitation=journal.get_reviewer_affinity_score_id(),
            head=note.id,
            domain=journal.venue_id,
            limit=1
        )
    except TypeError:
        edges = client.get_edges(
            invitation=journal.get_reviewer_affinity_score_id(),
            head=note.id,
            limit=1
        )
    except Exception as error:
        print(f'Could not check reviewer affinity edges for Paper{note.number}: {error}')
        return True
    return any(not getattr(edge, 'ddate', None) for edge in edges or [])


def active_reviewer_candidate_tails(client, journal):
    try:
        reviewer_group = client.get_group(journal.get_reviewers_id())
        reviewers = [
            member for member in (reviewer_group.members or [])
            if isinstance(member, str) and member.startswith('~')
        ]
    except Exception:
        reviewers = []
    return reviewers


def active_reviewer_candidate_tails_for_matching(client, journal):
    reviewers = active_reviewer_candidate_tails(client, journal)
    if not reviewers:
        return []
    indefinitely_unavailable = set()
    try:
        availability_edges = client.get_all_edges(invitation=journal.get_reviewer_availability_id())
    except Exception:
        try:
            availability_edges = client.get_edges(invitation=journal.get_reviewer_availability_id())
        except Exception:
            availability_edges = []
    for availability_edge in availability_edges or []:
        if (
            getattr(availability_edge, 'tail', None)
            and not getattr(availability_edge, 'ddate', None)
            and getattr(availability_edge, 'label', None) == 'Unavailable'
            and not getattr(availability_edge, 'weight', None)
        ):
            indefinitely_unavailable.add(availability_edge.tail)
    return [
        tail for tail in reviewers
        if tail not in indefinitely_unavailable
    ]


def reviewer_assignment_cooldown_until_by_tail(client, journal, note, reviewer_tails):
    import datetime
    import openreview

    cooldown_days = int("{{REVIEWER_NEW_ASSIGNMENT_COOLDOWN_DAYS}}")
    cooldown_millis = cooldown_days * 24 * 60 * 60 * 1000
    if not cooldown_millis:
        return {}
    now = openreview.tools.datetime_millis(datetime.datetime.now())
    cutoff = now - cooldown_millis
    cooldown_until_by_tail = {}
    for tail in reviewer_tails or []:
        try:
            edges = client.get_all_edges(tail=tail, domain=journal.venue_id)
        except Exception:
            try:
                edges = client.get_edges(tail=tail, domain=journal.venue_id)
            except Exception:
                edges = []
        recent_assignment_edges = [
            edge for edge in (edges or [])
            if getattr(edge, 'invitation', '').endswith('/Reviewers/-/Assignment')
            and not getattr(edge, 'ddate', None)
            and getattr(edge, 'head', None) != note.id
            and getattr(edge, 'cdate', None)
            and edge.cdate >= cutoff
        ]
        if recent_assignment_edges:
            latest_assignment = max(recent_assignment_edges, key=lambda edge: edge.cdate or 0)
            cooldown_until_by_tail[tail] = latest_assignment.cdate + cooldown_millis
    return cooldown_until_by_tail


def filtered_reviewer_matching_group_id(journal, note):
    return f'{journal.venue_id}/Paper{note.number}/Reviewer_Matching_Input'


def ensure_filtered_reviewer_matching_group(client, journal, note, reviewer_candidate_tails):
    group_id = filtered_reviewer_matching_group_id(journal, note)
    members = list(dict.fromkeys([
        tail for tail in reviewer_candidate_tails or []
        if isinstance(tail, str) and tail.startswith('~')
    ]))
    try:
        group = client.get_group(group_id)
    except Exception:
        group = openreview.api.Group(id=group_id)
    group.signatures = [journal.venue_id]
    group.readers = list(dict.fromkeys([
        journal.venue_id,
        journal.get_editors_in_chief_id(),
        journal.get_action_editors_id(number=note.number),
    ]))
    group.writers = [journal.venue_id]
    group.members = members
    client.post_group_edit(
        invitation=journal.get_meta_invitation_id(),
        signatures=[journal.venue_id],
        readers=[journal.venue_id],
        writers=[journal.venue_id],
        group=group,
    )
    return group_id


def request_reviewer_affinity_for_assignment_hub(client, journal, note, reviewer_candidate_tails=None):
    datetime = __import__('datetime')
    affinity_model = getattr(journal, 'get_expertise_model', lambda: '{{EXPERTISE_MODEL}}')()
    job_name = f"jmlr-{journal.venue_id.replace('/', '-')}-reviewer-affinity-paper{note.number}-{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    reviewer_candidate_tails = list(dict.fromkeys(reviewer_candidate_tails or active_reviewer_candidate_tails_for_matching(client, journal)))
    if not reviewer_candidate_tails:
        raise openreview.OpenReviewException(f'Reviewer affinity has no active reviewer candidates for Paper{note.number}.')
    reviewer_matching_group_id = ensure_filtered_reviewer_matching_group(client, journal, note, reviewer_candidate_tails)
    allowed_reviewer_tails = set(reviewer_candidate_tails)
    submissions = [{
        'id': note.id,
        'title': note.content.get('title', {}).get('value', ''),
        'abstract': note.content.get('abstract', {}).get('value', '')
    }]
    payload = {
        'name': job_name,
        'entityA': {
            'type': 'Group',
            'memberOf': reviewer_matching_group_id
        },
        'entityB': {
            'type': 'Note',
            'submissions': submissions
        },
        'model': {
            'name': affinity_model,
            'normalizeScores': False
        }
    }
    try:
        response = client.request_paper_subset_expertise(
            job_name,
            [note],
            reviewer_matching_group_id,
            model=affinity_model
        )
    except Exception:
        response = None
        session = getattr(client, 'session', None)
        baseurl = getattr(client, 'baseurl', None)
        headers = getattr(client, 'headers', None)
        if not session or not baseurl:
            raise
        http_response = session.post(baseurl + '/expertise', json=payload, headers=headers)
        if http_response.status_code < 200 or http_response.status_code >= 300:
            raise openreview.OpenReviewException(f"Reviewer affinity Expertise request failed with HTTP {http_response.status_code}: {http_response.text[:500]}")
        response = http_response.json()
    job_id = response.get('jobId') or response.get('job_id') or response.get('id')
    if not job_id:
        raise openreview.OpenReviewException(f'Reviewer affinity Expertise request did not return a job id for Paper{note.number}.')
    results = client.get_expertise_results(job_id, wait_for_complete=True)
    reviewer_scores = extract_reviewer_affinity_scores(results, note.id)
    if not reviewer_scores:
        raise openreview.OpenReviewException(f'Reviewer affinity Expertise job {job_id} returned no parseable scores for Paper{note.number}.')
    affinity_invitation = journal.get_reviewer_affinity_score_id()
    posted_count = 0
    for profile_id, score in sorted(reviewer_scores.items()):
        if profile_id not in allowed_reviewer_tails:
            continue
        existing_edges = client.get_edges(invitation=affinity_invitation, head=note.id, tail=profile_id)
        client.post_edge(openreview.api.Edge(
            id=existing_edges[0].id if existing_edges else None,
            invitation=affinity_invitation,
            signatures=[journal.venue_id],
            head=note.id,
            tail=profile_id,
            weight=score
        ))
        posted_count += 1
    print(f'Posted {posted_count} reviewer affinity scores for Paper{note.number} from Expertise job {job_id}.')
    return posted_count


def ensure_reviewer_affinity_on_first_assignment_hub_create(client, journal, note, hub_webfield_already_initialized, reviewer_candidate_tails=None):
    if hub_webfield_already_initialized:
        return 'hub_already_initialized'
    if active_reviewer_affinity_edges_exist(client, journal, note):
        return 'affinity_edges_already_exist'
    try:
        request_reviewer_affinity_for_assignment_hub(client, journal, note, reviewer_candidate_tails)
        return 'affinity_computed'
    except Exception as error:
        print(f'Could not compute reviewer affinity for first reviewer assignment hub for Paper{note.number}: {error}')
        return 'affinity_blocked'


def reviewer_assignment_browser_contract(journal, note, reviewer_assignment_id, reviewer_invite_assignment_id, reviewers_id, reviewer_assignment_hub_url):
    return {
        'paper_id': note.id,
        'paper_number': note.number,
        'assignment_invitation': reviewer_assignment_id,
        'deployed_assignment_sources': [
            reviewer_assignment_id
        ],
        'readback_assignment_sources': [
            reviewer_assignment_id,
            reviewer_invite_assignment_id,
            f'{journal.venue_id}/Reviewers/-/Review_Due_Date'
        ],
        'score_sources': {
            'affinity_score_invitation': journal.get_reviewer_affinity_score_id(),
            'matching_input_group': filtered_reviewer_matching_group_id(journal, note),
            'reviewer_stats_source': f'{journal.venue_id}/-/Submission'
        },
        'conflict_sources': {
            'openreview_conflict_invitation': journal.get_reviewer_conflict_id(),
            'candidate_refresh_invitation': f'{journal.venue_id}/-/Assignment_Candidate_Conflict_Refresh',
            'hard_author_fields': ['authorids', 'author_list', 'conflict_of_interests']
        },
        'availability_sources': {
            'reviewer_availability_invitation': journal.get_reviewer_availability_id(),
            'paper_scoped_config_key': 'reviewerAssignmentAvailability'
        },
        'load_sources': {
            'pending_reviews_invitation': journal.get_reviewer_pending_review_id(),
            'custom_max_papers_invitation': reviewers_id + '/-/Custom_Max_Papers',
            'assignment_history_sources': [
                reviewer_assignment_id,
                journal.get_reviewer_assignment_id()
            ]
        },
        'filter_semantics': {
            'candidate_group': reviewers_id,
            'requires_current_reviewer_membership': True,
            'blocks_hard_author_conflicts': True,
            'openreview_conflicts_are_override_warnings': True,
            'blocks_unavailable_reviewers': True,
            'checks_active_load_and_cooldown': True,
            'excludes_current_reviewers_from_new_assignment': True,
            'max_total_reviewer_assignments': 5
        },
        'allowed_signatures': [
            journal.get_editors_in_chief_id(),
            journal.get_action_editors_id(number=note.number)
        ],
        'legacy_read_only_sources': [
            journal.get_reviewer_assignment_id()
        ],
        'ui_boundary': {
            'visible_default_route': reviewer_assignment_hub_url,
            'raw_edges_browse_default': False
        }
    }


def external_reviewer_invite_profile_lookup_identity(profile_map, value, profile_json):
    if not value:
        return
    key = str(value).strip()
    if not key:
        return
    if '@' in key and '*' in key:
        return
    profile_map[key.lower()] = profile_json


def external_reviewer_invite_profile_lookup_profile(profile_map, profile, preferred_email_by_profile_id=None):
    profile_id = getattr(profile, 'id', None)
    if not profile_id:
        return
    profile_content = getattr(profile, 'content', {}) or {}
    profile_json = {
        'id': profile_id,
        'content': profile_content
    }
    external_reviewer_invite_profile_lookup_identity(profile_map, profile_id, profile_json)
    preferred_emails = (preferred_email_by_profile_id or {}).get(profile_id)
    if isinstance(preferred_emails, str):
        preferred_emails = [preferred_emails]
    for preferred_email in preferred_emails or []:
        external_reviewer_invite_profile_lookup_identity(profile_map, preferred_email, profile_json)
    try:
        external_reviewer_invite_profile_lookup_identity(profile_map, profile.get_preferred_email(), profile_json)
    except Exception:
        pass
    for field in ['preferredEmail', 'preferredId']:
        external_reviewer_invite_profile_lookup_identity(profile_map, profile_content.get(field), profile_json)
    for field in ['emails', 'preferredEmails', 'confirmedEmails', 'emailsConfirmed', 'usernames']:
        for value in profile_content.get(field, []) or []:
            external_reviewer_invite_profile_lookup_identity(profile_map, value, profile_json)
    for name in profile_content.get('names', []) or []:
        if isinstance(name, dict):
            external_reviewer_invite_profile_lookup_identity(profile_map, name.get('username'), profile_json)


def get_reviewer_invite_preferred_email_by_profile_id(client, journal, profile_ids):
    allowed_profile_ids = set(profile_ids or [])
    if not allowed_profile_ids:
        return {}
    preferred_email_by_profile_id = {}
    try:
        grouped_edges = client.get_grouped_edges(
            invitation=journal.get_preferred_emails_invitation_id(),
            groupby='head',
            select='tail'
        )
    except Exception as error:
        print(f'Could not load reviewer invite preferred-email edges: {error}')
        return preferred_email_by_profile_id
    for grouped_edge in grouped_edges or []:
        grouped_id = grouped_edge.get('id') if isinstance(grouped_edge, dict) else getattr(grouped_edge, 'id', None)
        head = grouped_id.get('head') if isinstance(grouped_id, dict) else None
        values = grouped_edge.get('values', []) if isinstance(grouped_edge, dict) else getattr(grouped_edge, 'values', [])
        if head not in allowed_profile_ids:
            continue
        for value in values or []:
            tail = value.get('tail') if isinstance(value, dict) else getattr(value, 'tail', None)
            if not tail:
                continue
            tail = str(tail).strip()
            if '@' not in tail or '*' in tail:
                continue
            preferred_email_by_profile_id.setdefault(head, [])
            if tail not in preferred_email_by_profile_id[head]:
                preferred_email_by_profile_id[head].append(tail)
    return preferred_email_by_profile_id


def refresh_reviewer_assignment_hub(client, journal, note, duedate, number_of_reviewers, reviewers_max_papers, json, html, re):
    invitation_refresh_namespace = {'openreview': openreview}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/under_review/reviewer_assignment_invitation_refresh.py}}", invitation_refresh_namespace)
    required_reviewers_namespace = {'openreview': openreview}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/review/required_reviewers.py}}", required_reviewers_namespace)
    identity_namespace = {'openreview': openreview}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/reviewer_identity_continuity.py}}", identity_namespace)

    reviewer_assignment_invitation = invitation_refresh_namespace['refresh_reviewer_assignment_invitation'](
        client,
        journal,
        note,
        duedate
    )
    number_of_reviewers = required_reviewers_namespace['get_required_reviewers'](client, journal, note)
    required_reviewers_id = required_reviewers_namespace['required_reviewers_invitation_id'](journal, note)
    required_reviewers_tail = required_reviewers_namespace['required_reviewers_tail'](journal, note)
    reviewer_identity_continuity = identity_namespace['load_reviewer_identity_continuity'](note)
    reviewer_assignment_invitation_updated = False
    web = reviewer_assignment_invitation.web or ''
    hub_webfield_already_initialized = 'var AUTO_ASSIGN_CONFIG = ' in web
    marker = 'var HEADER = '
    if marker in web:
        reviewers_id = journal.get_reviewers_id()
        reviewer_assignment_id = journal.get_reviewer_assignment_id(number=note.number)
        reviewer_invite_assignment_id = journal.get_reviewer_invite_assignment_id()
        reviewer_assignment_hub_url = f'/group?id={journal.get_reviewers_id(number=note.number)}'
        assigned_action_editor_signature = ''
        try:
            assigned_action_editor_signature = (client.get_group(journal.get_action_editors_id(number=note.number)).members or [''])[0]
        except Exception:
            assigned_action_editor_signature = ''
        reviewer_candidate_tails = active_reviewer_candidate_tails(client, journal)
        reviewer_matching_candidate_tails = active_reviewer_candidate_tails_for_matching(client, journal)
        reviewer_invite_profile_lookup = {}

        reviewer_invite_profile_ids = list(reviewer_candidate_tails)
        reviewer_invite_profile_ids.extend([
            author_id for author_id in (note.content.get('authorids', {}).get('value') or [])
            if isinstance(author_id, str) and author_id.startswith('~')
        ])
        for group_id_getter_name in ['get_action_editors_id', 'get_editors_in_chief_id', 'get_oss_action_editors_id']:
            group_id_getter = getattr(journal, group_id_getter_name, None)
            if not callable(group_id_getter):
                continue
            group_id = group_id_getter_name
            try:
                group_id = group_id_getter()
                group = client.get_group(group_id)
                reviewer_invite_profile_ids.extend([
                    member for member in (group.members or [])
                    if isinstance(member, str) and member.startswith('~')
                ])
            except Exception as error:
                print(f'Could not load reviewer invite profile lookup group {group_id}: {error}')
        reviewer_invite_profile_ids = list(dict.fromkeys(reviewer_invite_profile_ids))
        if reviewer_invite_profile_ids:
            preferred_email_by_profile_id = get_reviewer_invite_preferred_email_by_profile_id(
                client,
                journal,
                reviewer_invite_profile_ids
            )
            try:
                reviewer_invite_profiles = openreview.tools.get_profiles(
                    client,
                    reviewer_invite_profile_ids,
                    with_preferred_emails=journal.get_preferred_emails_invitation_id()
                )
            except Exception as error:
                print(f'Could not load reviewer invite profile lookup profiles: {error}')
                reviewer_invite_profiles = []
            for profile in reviewer_invite_profiles or []:
                external_reviewer_invite_profile_lookup_profile(
                    reviewer_invite_profile_lookup,
                    profile,
                    preferred_email_by_profile_id
                )
        now_millis = int(__import__('time').time() * 1000)
        reviewer_assignment_availability = {}
        try:
            reviewer_availability_edges = client.get_all_edges(invitation=journal.get_reviewer_availability_id())
        except Exception:
            reviewer_availability_edges = client.get_edges(invitation=journal.get_reviewer_availability_id())
        for availability_edge in reviewer_availability_edges or []:
            if (
                getattr(availability_edge, 'tail', None)
                and getattr(availability_edge, 'label', None) == 'Unavailable'
                and (
                    not getattr(availability_edge, 'weight', None)
                    or int(getattr(availability_edge, 'weight', 0)) > now_millis
                )
            ):
                reviewer_assignment_availability[availability_edge.tail] = {
                    'unavailableForAssignment': True
                }
        reviewer_assignment_cooldown_until = reviewer_assignment_cooldown_until_by_tail(
            client,
            journal,
            note,
            reviewer_candidate_tails
        )
        assignment_browser_contract = reviewer_assignment_browser_contract(
            journal,
            note,
            reviewer_assignment_id,
            reviewer_invite_assignment_id,
            reviewers_id,
            reviewer_assignment_hub_url
        )
        start = web.index(marker) + len(marker)
        header, header_length = json.JSONDecoder().raw_decode(web[start:])
        end = start + header_length
        paper_title = html.escape(note.content["title"]["value"])
        paper_abstract = html.escape(note.content.get("abstract", {}).get("value", ""))
        cover_letter = html.escape(str(note.content.get("cover_letter", {}).get("value") or "").strip())
        cover_letter_body = (
            f'<p style="margin-top: 8px; white-space: pre-wrap;">{cover_letter}</p>'
            if cover_letter
            else '<p class="text-muted" style="margin-top: 8px;">No cover letter was provided.</p>'
        )
        paper_url = f'/forum?id={note.id}'
        paper_pdf_url = f'/pdf?id={note.id}'
        header['title'] = 'Assign Reviewers'
        header['instructions'] = (
            '<style>'
            '.jmlr-assignment-collapsible { margin-bottom: 12px; }'
            '.jmlr-assignment-collapsible > summary { cursor: pointer; list-style: none; border-radius: 4px; padding: 4px 6px; }'
            '.jmlr-assignment-collapsible > summary::-webkit-details-marker { display: none; }'
            '.jmlr-assignment-collapsible > summary:hover { background: #f5f5f5; }'
            '.jmlr-assignment-collapsible > summary:focus-visible { outline: 2px solid #337ab7; outline-offset: 2px; }'
            '.jmlr-assignment-caret { display: inline-block; margin-right: 6px; transition: transform 0.15s ease-in-out; }'
            '.jmlr-assignment-collapsible:not([open]) .jmlr-assignment-caret { transform: rotate(-90deg); }'
            '</style>'
            f'<p class="dark">Use this page to assign reviewers for '
            f'<a href="{paper_url}">Paper {note.number}: {paper_title}</a> '
            f'(<a href="{paper_pdf_url}" target="_blank" rel="noopener noreferrer">PDF</a>).</p>'
            '<details class="dark jmlr-assignment-collapsible" open>'
            '<summary><span class="jmlr-assignment-caret" aria-hidden="true">&#9662;</span><strong>Abstract</strong></summary>'
            f'<p style="margin-top: 8px; white-space: pre-wrap;">{paper_abstract}</p>'
            '</details>'
            '<details class="dark jmlr-assignment-collapsible" open>'
            '<summary><span class="jmlr-assignment-caret" aria-hidden="true">&#9662;</span><strong>Cover Letter</strong></summary>'
            f'{cover_letter_body}'
            '</details>'
        )
        web = web[:start] + json.dumps(header) + web[end:]

        def build_auto_assign_script():
            auto_assign_script = f"""
    var AUTO_ASSIGN_CONFIG = {json.dumps({
    'noteId': note.id,
    'paperNumber': note.number,
    'numberOfReviewers': number_of_reviewers,
    'requiredReviewersId': required_reviewers_id,
    'requiredReviewersTail': required_reviewers_tail,
    'maxRequiredReviewers': required_reviewers_namespace['MAX_REQUIRED_REVIEWERS'],
    'submissionTitle': note.content['title']['value'],
    'submissionAbstract': note.content.get('abstract', {}).get('value', ''),
    'submissionCoverLetter': note.content.get('cover_letter', {}).get('value', ''),
    'submissionAuthorList': note.content.get('author_list', {}).get('value', ''),
    'submissionConflictOfInterests': note.content.get('conflict_of_interests', {}).get('value', ''),
    'paperPdfUrl': f'/pdf?id={note.id}',
    'candidateDisplayLimit': 80,
    'maxTotalReviewerAssignments': 5,
    'reviewersMaxPapers': reviewers_max_papers,
    'reviewPeriodDays': int(journal.get_review_period_length(note) * 7),
    'reviewerNewAssignmentCooldownDays': int("{{REVIEWER_NEW_ASSIGNMENT_COOLDOWN_DAYS}}"),
    'expertiseModel': "{{EXPERTISE_MODEL}}",
    'inviteAssignmentNoResponseExpirationDays': int("{{INVITE_ASSIGNMENT_NO_RESPONSE_EXPIRATION_DAYS}}"),
    'previousSubmissionId': previous_submission_id_from_note(note),
    'previousSubmissionNumber': previous_submission_number_from_note(note),
    'previousSubmissionList': note.content.get('previous_JMLR_submissions', {}).get('value') or '',
    'venueId': journal.venue_id,
    'submissionGroupName': 'Paper',
    'reviewersId': reviewers_id,
    'reviewerCandidateTails': reviewer_candidate_tails,
    'reviewerInviteProfileLookup': reviewer_invite_profile_lookup,
    'assignmentBrowserContract': assignment_browser_contract,
    'reviewersReviewDueDateId': f'{journal.venue_id}/Reviewers/-/Review_Due_Date',
    'reviewersInviteAssignmentId': reviewer_invite_assignment_id,
    'assignedActionEditorSignature': assigned_action_editor_signature,
    'reviewersAffinityScoreId': journal.get_reviewer_affinity_score_id(),
    'reviewersConflictId': journal.get_reviewer_conflict_id(),
    'reviewerAssignmentAvailability': reviewer_assignment_availability,
    'reviewerAssignmentCooldownUntilByTail': reviewer_assignment_cooldown_until,
    'reviewersPendingReviewsId': journal.get_reviewer_pending_review_id(),
    'reviewersCustomMaxPapersId': reviewers_id + '/-/Custom_Max_Papers',
    'expertReviewersId': journal.venue_id + '/Expert_Reviewers',
    'metaInvitationId': journal.get_meta_invitation_id(),
    'contactInfo': journal.contact_info,
    'submissionAuthorIds': note.content.get('authorids', {}).get('value') or [],
    'ratingScores': {
        'No rating': 0,
        'Exceeds expectations': 1,
        'Meets expectations': 0,
        'Falls below expectations': -1,
        'Report problem': -2
    },
    'timelinessOrder': ['On time', 'Past due', 'Review not expected'],
    'actionEditorsId': journal.get_action_editors_id(),
    'manualAssignmentUrl': reviewer_assignment_hub_url,
    'reviewerIdentityContinuity': {
        'reviewers': reviewer_identity_continuity.get('reviewers', [])
    }
    })};
    var REVIEWER_AUTO_CONFLICT_OVERRIDE_ENABLED = false;

"""
            reviewer_assignment_hub_js_parts = {}
            exec("{{PYTHON_SCRIPT_JSON:invitations/venue/under_review/reviewer_assignment_hub_parts/shared_helpers.py}}", reviewer_assignment_hub_js_parts)
            exec("{{PYTHON_SCRIPT_JSON:invitations/venue/under_review/reviewer_assignment_hub_parts/invite_new_reviewers_tab.py}}", reviewer_assignment_hub_js_parts)
            exec("{{PYTHON_SCRIPT_JSON:invitations/venue/under_review/reviewer_assignment_hub_parts/previous_reviewers_tab.py}}", reviewer_assignment_hub_js_parts)
            exec("{{PYTHON_SCRIPT_JSON:invitations/venue/under_review/reviewer_assignment_hub_parts/candidate_data_helpers.py}}", reviewer_assignment_hub_js_parts)
            exec("{{PYTHON_SCRIPT_JSON:invitations/venue/under_review/reviewer_assignment_hub_parts/search_reviewers_tab.py}}", reviewer_assignment_hub_js_parts)
            exec("{{PYTHON_SCRIPT_JSON:invitations/venue/under_review/reviewer_assignment_hub_parts/auto_assign_reviewers_tab.py}}", reviewer_assignment_hub_js_parts)
            return auto_assign_script + ''.join([
                reviewer_assignment_hub_js_parts['REVIEWER_ASSIGNMENT_SHARED_JS'],
                reviewer_assignment_hub_js_parts['INVITE_NEW_REVIEWERS_TAB_JS'],
                reviewer_assignment_hub_js_parts['PREVIOUS_REVIEWERS_TAB_JS'],
                reviewer_assignment_hub_js_parts['REVIEWER_CANDIDATE_DATA_HELPERS_JS'],
                reviewer_assignment_hub_js_parts['SEARCH_REVIEWERS_TAB_JS'],
                reviewer_assignment_hub_js_parts['AUTO_ASSIGN_REVIEWERS_TAB_JS'],
            ])

        if 'var AUTO_ASSIGN_CONFIG = ' not in web:
            ensure_reviewer_affinity_on_first_assignment_hub_create(
                client,
                journal,
                note,
                hub_webfield_already_initialized,
                reviewer_matching_candidate_tails
            )
            insert_at = web.find(';\n', start)
            if insert_at >= 0:
                insert_at += 2
            else:
                insert_at = end
            auto_assign_script = build_auto_assign_script()
            web = web[:insert_at] + auto_assign_script + web[insert_at:]
        else:
            block_start = web.find('var AUTO_ASSIGN_CONFIG = ')
            block_end = web.find('\nfunction main()', block_start)
            if block_start < 0 or block_end <= block_start:
                raise ValueError('Could not refresh reviewer assignment hub: missing generated assignment block boundary.')
            web = web[:block_start] + build_auto_assign_script() + web[block_end:]

        config_marker = 'var AUTO_ASSIGN_CONFIG = '
        config_start = web.find(config_marker)
        if config_start >= 0:
            config_value_start = config_start + len(config_marker)
            auto_assign_config, auto_assign_config_length = json.JSONDecoder().raw_decode(web[config_value_start:])
            auto_assign_config['noteId'] = note.id
            auto_assign_config['paperNumber'] = note.number
            auto_assign_config['numberOfReviewers'] = number_of_reviewers
            auto_assign_config['requiredReviewersId'] = required_reviewers_id
            auto_assign_config['requiredReviewersTail'] = required_reviewers_tail
            auto_assign_config['maxRequiredReviewers'] = required_reviewers_namespace['MAX_REQUIRED_REVIEWERS']
            auto_assign_config['submissionTitle'] = note.content['title']['value']
            auto_assign_config['submissionAbstract'] = note.content.get('abstract', {}).get('value', '')
            auto_assign_config['submissionCoverLetter'] = note.content.get('cover_letter', {}).get('value', '')
            auto_assign_config['submissionAuthorList'] = note.content.get('author_list', {}).get('value', '')
            auto_assign_config['submissionConflictOfInterests'] = note.content.get('conflict_of_interests', {}).get('value', '')
            auto_assign_config['paperPdfUrl'] = f'/pdf?id={note.id}'
            auto_assign_config['submissionAuthorIds'] = note.content.get('authorids', {}).get('value') or []
            auto_assign_config['reviewPeriodDays'] = int(journal.get_review_period_length(note) * 7)
            auto_assign_config['reviewerAssignmentAvailability'] = reviewer_assignment_availability
            auto_assign_config['reviewerCandidateTails'] = reviewer_candidate_tails
            auto_assign_config['reviewerInviteProfileLookup'] = reviewer_invite_profile_lookup
            auto_assign_config['assignmentBrowserContract'] = assignment_browser_contract
            auto_assign_config['reviewersInviteAssignmentId'] = reviewer_invite_assignment_id
            auto_assign_config['assignedActionEditorSignature'] = assigned_action_editor_signature
            auto_assign_config['previousSubmissionId'] = previous_submission_id_from_note(note)
            auto_assign_config['previousSubmissionNumber'] = previous_submission_number_from_note(note)
            auto_assign_config['previousSubmissionList'] = note.content.get('previous_JMLR_submissions', {}).get('value') or ''
            auto_assign_config['reviewerIdentityContinuity'] = {
                'reviewers': reviewer_identity_continuity.get('reviewers', [])
            }
            auto_assign_config.pop('reviewersAssignmentId', None)
            auto_assign_config.pop('reviewersAvailabilityId', None)
            web = (
                web[:config_value_start]
                + json.dumps(auto_assign_config)
                + web[config_value_start + auto_assign_config_length:]
            )

        new_content = (
            "'<div id=\"reviewer-assignment-status\"></div>' +\n"
            "    '<p class=\"text-center\">' +\n"
            "      (hasPreviousSubmissionReference() ? '<button id=\"previous-reviewers\" type=\"button\" class=\"btn btn-lg btn-default\" style=\"margin-right: 8px;\">Previous Reviewers</button>' : '') +\n"
            "      '<button id=\"auto-assign-reviewers\" type=\"button\" class=\"btn btn-lg btn-default\" style=\"margin-right: 8px;\">Auto-assign Reviewers</button>' +\n"
            "      '<button id=\"search-reviewers\" type=\"button\" class=\"btn btn-lg btn-default\" style=\"margin-right: 8px;\">Search Reviewers</button>' +\n"
            "      '<button id=\"invite-new-reviewer\" type=\"button\" class=\"btn btn-lg btn-default\" style=\"margin-right: 8px;\">Invite New Reviewer</button>' +\n"
            "      '<p id=\"auto-assign-status\" class=\"text-center\" style=\"margin-top: 12px;\"></p>' +\n"
            "      '<section id=\"previous-reviewers-container\" class=\"panel panel-default\" style=\"display: none; max-width: 1100px; margin: 16px auto 0; text-align: left;\">' +\n"
            "        '<div class=\"panel-heading\"><strong>Previous Reviewers</strong></div>' +\n"
            "        '<div class=\"panel-body\">' +\n"
            "          '<div id=\"previous-reviewers-results\"></div>' +\n"
            "          '<button id=\"cancel-previous-reviewers\" type=\"button\" class=\"btn btn-default\">Cancel</button>' +\n"
            "        '</div>' +\n"
            "      '</section>' +\n"
            "      '<section id=\"manual-reviewer-search-container\" class=\"panel panel-default\" style=\"display: none; max-width: 1100px; margin: 16px auto 0; text-align: left;\">' +\n"
            "        '<div class=\"panel-heading\"><strong>Search reviewers</strong></div>' +\n"
            "        '<div class=\"panel-body\">' +\n"
            "          '<p class=\"text-muted\">Search existing JMLR reviewers by name, email, or OpenReview profile id. Select matching reviewers, then confirm the assignment.</p>' +\n"
            "          '<div class=\"form-inline\">' +\n"
            "            '<input id=\"manual-reviewer-search-input\" type=\"search\" class=\"form-control\" style=\"min-width: 360px; margin-right: 8px;\" placeholder=\"name, email, or OpenReview id\">' +\n"
            "            '<button id=\"run-reviewer-search\" type=\"button\" class=\"btn btn-primary\" style=\"margin-right: 8px;\">Search</button>' +\n"
            "            '<button id=\"cancel-reviewer-search\" type=\"button\" class=\"btn btn-default\">Cancel</button>' +\n"
            "          '</div>' +\n"
            "          '<div id=\"manual-reviewer-search-results\" style=\"margin-top: 12px;\"></div>' +\n"
            "        '</div>' +\n"
            "      '</section>' +\n"
            "      '<section id=\"invite-new-reviewer-container\" class=\"panel panel-default\" style=\"display: none; max-width: 900px; margin: 16px auto 0; text-align: left;\">' +\n"
            "        '<div class=\"panel-heading\"><strong>Invite New Reviewer</strong></div>' +\n"
            "        '<div class=\"panel-body\">' +\n"
            "          '<div class=\"form-inline\">' +\n"
            "            '<input id=\"invite-new-reviewer-email\" type=\"email\" class=\"form-control\" style=\"min-width: 320px; margin-right: 8px;\" placeholder=\"reviewer@example.com\">' +\n"
            "            '<button id=\"search-reviewer-invite\" type=\"button\" class=\"btn btn-primary\" style=\"margin-right: 8px;\">Search</button>' +\n"
            "            reviewerDueDateInputHtml('invite-reviewer-due-date') +\n"
            "            '<button id=\"send-reviewer-invite\" type=\"button\" class=\"btn btn-success\" style=\"display: none; margin-right: 8px;\">Send Invite</button>' +\n"
            "            '<button id=\"cancel-reviewer-invite\" type=\"button\" class=\"btn btn-default\">Cancel</button>' +\n"
            "          '</div>' +\n"
            "          '<p id=\"invite-new-reviewer-email-status\" class=\"alert alert-warning\" style=\"margin-top: 8px; margin-bottom: 8px;\">Before sending, confirm this reviewer has no known conflict with the paper.</p>' +\n"
            "        '<div class=\"panel panel-default\" style=\"max-width: 760px; margin: 12px auto 0; text-align: left;\">' +\n"
            "          '<div class=\"panel-heading\"><strong>Email preview</strong></div>' +\n"
            "          '<div class=\"panel-body\">' +\n"
            "            '<p><strong>Subject:</strong> <span id=\"invite-email-subject\"></span></p>' +\n"
            "            '<label for=\"invite-email-body\" class=\"control-label\">Standard invitation email preview</label>' +\n"
            "            '<textarea id=\"invite-email-body\" class=\"form-control\" rows=\"16\" readonly style=\"font-family: monospace; white-space: pre-wrap; margin-bottom: 0;\"></textarea>' +\n"
            "          '</div>' +\n"
            "        '</div>' +\n"
            "        '</div>' +\n"
            "      '</section>' +\n"
            "    '</p>'"
        )
        web = re.sub(
            r"'<p class=\"text-center\">' \+\n\s*'<button id=\"auto-assign-reviewers\"[\s\S]*?AUTO_ASSIGN_CONFIG\.decisionUrl[\s\S]*?'<div id=\"invite-new-reviewer-container\"[\s\S]*?'\s*</p>'",
            new_content,
            web,
        )
        web = re.sub(
            r"'<p class=\"text-center\">' \+\n\s*'<a href=\"' \+ [A-Za-z0-9_$]+ \+ '\" class=\"btn btn-lg btn-primary\" >Assign Reviewers</a>' \+\n\s*'</p>'",
            new_content,
            web,
        )
        web = re.sub(r"\s*var [A-Za-z0-9_$]+ = location\.origin \+ '[^']+' \+ [A-Za-z0-9_$]+;\n", "\n", web)
        web = re.sub(r"\s*var [A-Za-z0-9_$]+ = [A-Z_]+\.replace\('\{userId\}', user\.profile\.id\);\n", "\n", web)
        web = re.sub(r"\nvar [A-Z_]+ = 'start=staticList,[^\n]+\n", "\n", web)
        web = re.sub(r'\n\s*"aeConsoleUrl":\s*"[^"]*",', '', web)
        web = re.sub(r'\n\s*"decisionUrl":\s*"[^"]*",', '', web)
        mode_helpers = """    function getReviewerAssignmentRequestedMode() {
      if (typeof args !== 'undefined' && args && args.mode) {
    var argMode = String(args.mode || '').toLowerCase();
    if (argMode === 'add-new') return 'invite';
      if (['auto', 'previous', 'search', 'invite'].indexOf(argMode) >= 0) return argMode;
      }
      var pageLocation =
    (typeof globalThis !== 'undefined' && globalThis.location) ||
    (typeof document !== 'undefined' && document && document.location) ||
    (typeof location !== 'undefined' && location);
      var urls = [];
      if (pageLocation && pageLocation.href) urls.push(pageLocation.href);
      if (typeof performance !== 'undefined' && performance.getEntriesByType) {
    (performance.getEntriesByType('navigation') || []).forEach(function(entry) {
      if (entry && entry.name) urls.push(entry.name);
    });
      }
      if (typeof document !== 'undefined' && document && document.referrer) urls.push(document.referrer);
      for (var i = 0; i < urls.length; i += 1) {
    try {
      var baseUrl = pageLocation && pageLocation.origin ? pageLocation.origin : null;
      var url = baseUrl ? new URL(urls[i], baseUrl) : new URL(urls[i]);
      var hashParams = new URLSearchParams(String(url.hash || '').replace(/^#/, ''));
      var mode = String(url.searchParams.get('mode') || hashParams.get('mode') || '').toLowerCase();
      if (mode === 'add-new') return 'invite';
      if (['auto', 'previous', 'search', 'invite'].indexOf(mode) >= 0) return mode;
    } catch (error) {
      // Ignore malformed referrer/navigation values.
    }
      }
      return '';
    }

    function applyReviewerAssignmentRequestedMode() {
      var mode = getReviewerAssignmentRequestedMode();
      var marker = $('#jmlr-reviewer-assignment-mode-applied');
      if (!mode || (marker.length && marker.attr('data-mode') === mode)) return;
      marker.remove();
      if (mode === 'auto') {
    $('body').append('<span id="jmlr-reviewer-assignment-mode-applied" data-mode="auto" style="display:none;"></span>');
    $('#auto-assign-reviewers').trigger('click');
      } else if (mode === 'search') {
    $('body').append('<span id="jmlr-reviewer-assignment-mode-applied" data-mode="search" style="display:none;"></span>');
    $('#search-reviewers').trigger('click');
      } else if (mode === 'previous' && hasPreviousSubmissionReference()) {
    $('body').append('<span id="jmlr-reviewer-assignment-mode-applied" data-mode="previous" style="display:none;"></span>');
    $('#previous-reviewers').trigger('click');
      } else if (mode === 'invite') {
    $('body').append('<span id="jmlr-reviewer-assignment-mode-applied" data-mode="invite" style="display:none;"></span>');
    $('#invite-new-reviewer').trigger('click');
      }
    }
"""
        if "function getReviewerAssignmentRequestedMode()" in web:
            web = re.sub(
                r"    function getReviewerAssignmentRequestedMode\(\) \{[\s\S]*?    function reviewerEligibilityStatus\(candidate\) \{",
                mode_helpers + "\n    function reviewerEligibilityStatus(candidate) {",
                web,
            )
        elif "function reviewerEligibilityStatus(candidate)" in web:
            web = web.replace("    function reviewerEligibilityStatus(candidate) {", mode_helpers + "\n    function reviewerEligibilityStatus(candidate) {")
        render_return = '  return $.Deferred().resolve();\n}\n\n// Go!'
        render_start = web.find('function renderContent()')
        render_return_start = web.find(render_return, render_start)
        if render_return_start >= 0 and "renderReviewerAssignmentHomepageStrip();" not in web:
            web = (
                web[:render_return_start] +
                "  renderReviewerAssignmentHomepageStrip();\n\n" +
                web[render_return_start:]
            )
        render_return_start = web.find(render_return, render_start)
        if render_return_start >= 0 and "$('#auto-assign-reviewers').off('click')" not in web:
            web = (
                web[:render_return_start] +
                "  $('#auto-assign-reviewers').off('click').on('click', submitAutoReviewerAssignments);\n\n" +
                web[render_return_start:]
            )
        render_return_start = web.find(render_return, render_start)
        if render_return_start >= 0 and "$('#search-reviewers').off('click')" not in web:
            web = (
                web[:render_return_start] +
                "  renderReviewerStatusArea();\n\n" +
                "  $('#search-reviewers').off('click').on('click', showReviewerSearchPanel);\n\n" +
                "  $('#run-reviewer-search').off('click').on('click', searchExistingReviewers);\n\n" +
                "  $('#cancel-reviewer-search').off('click').on('click', hideReviewerSearchPanel);\n\n" +
                "  $('#manual-reviewer-search-input').off('keydown').on('keydown', function(event) { if (event.key === 'Enter') { event.preventDefault(); searchExistingReviewers(); } });\n\n" +
                web[render_return_start:]
            )
        render_return_start = web.find(render_return, render_start)
        if render_return_start >= 0 and "$('#previous-reviewers').off('click')" not in web:
            web = (
                web[:render_return_start] +
                "  $('#previous-reviewers').off('click').on('click', showPreviousReviewersPanel);\n\n" +
                "  $('#cancel-previous-reviewers').off('click').on('click', hidePreviousReviewersPanel);\n\n" +
                web[render_return_start:]
            )
        render_return_start = web.find(render_return, render_start)
        if render_return_start >= 0 and "$('#invite-new-reviewer').off('click')" not in web:
            web = (
                web[:render_return_start] +
                "  $('#invite-new-reviewer').off('click').on('click', showReviewerInviteForm);\n\n" +
                web[render_return_start:]
            )
        render_return_start = web.find(render_return, render_start)
        if render_return_start >= 0 and "$('#send-reviewer-invite').off('click')" not in web:
            web = (
                web[:render_return_start] +
                "  $('#search-reviewer-invite').off('click').on('click', searchReviewerInviteEmail);\n\n" +
                "  $('#send-reviewer-invite').off('click').on('click', submitReviewerEmailInvite);\n\n" +
                "  $('#cancel-reviewer-invite').off('click').on('click', hideReviewerInviteForm);\n\n" +
                "  $('#invite-new-reviewer-email').off('input').on('input', updateReviewerInviteEmailPreview);\n\n" +
                "  $('#invite-new-reviewer-email').off('keydown').on('keydown', function(event) { if (event.key === 'Enter') { event.preventDefault(); searchReviewerInviteEmail(); } });\n\n" +
                web[render_return_start:]
            )
        render_return_start = web.find(render_return, render_start)
        if render_return_start >= 0 and "applyReviewerAssignmentRequestedMode();" not in web:
            web = (
                web[:render_return_start] +
                "  applyReviewerAssignmentRequestedMode();\n\n" +
                "  setTimeout(applyReviewerAssignmentRequestedMode, 100);\n\n" +
                "  setTimeout(applyReviewerAssignmentRequestedMode, 500);\n\n" +
                web[render_return_start:]
            )
        elif render_return_start >= 0 and "setTimeout(applyReviewerAssignmentRequestedMode, 100)" not in web:
            web = web.replace(
                "  applyReviewerAssignmentRequestedMode();\n\n",
                "  applyReviewerAssignmentRequestedMode();\n\n  setTimeout(applyReviewerAssignmentRequestedMode, 100);\n\n  setTimeout(applyReviewerAssignmentRequestedMode, 500);\n\n"
            )
        if "var hasLoadOrAvailabilityWarning = reviewerModels.some" not in web:
            web = web.replace(
                "        var hasConflictOverrideChoice = conflictedReviewerIds.some(function(tail) {\n"
                "          return assignableReviewerIds.indexOf(tail) >= 0;\n"
                "        });\n"
                "        var disabled =",
                "        var hasConflictOverrideChoice = conflictedReviewerIds.some(function(tail) {\n"
                "          return assignableReviewerIds.indexOf(tail) >= 0;\n"
                "        });\n"
                "        var hasLoadOrAvailabilityWarning = reviewerModels.some(function(model) {\n"
                "          return !model.alreadyAssigned && assignableReviewerIds.indexOf(model.tail) >= 0 &&\n"
                "            (!model.available || model.activePaperLoad >= model.maxPapers);\n"
                "        });\n"
                "        var warningSummary = [];\n"
                "        if (hasConflictOverrideChoice) warningSummary.push('One or more previous reviewers have OpenReview conflict edges for this paper.');\n"
                "        if (hasLoadOrAvailabilityWarning) warningSummary.push('One or more previous reviewers are unavailable or at/over configured active-review load; continuity assignment treats this as warning information.');\n"
                "        var disabled ="
            )
        web = web.replace(
            "          (hasConflictOverrideChoice ? '<div class=\"checkbox\"><label><input id=\"include-conflicted-previous-reviewers\" type=\"checkbox\"> Include conflicted previous reviewers. This records a previous-reviewer conflict override.</label></div>' : '') +",
            "          (warningSummary.length ? '<div class=\"alert alert-warning\"><strong>Continuity warnings</strong><ul>' + warningSummary.map(function(item) { return '<li>' + escapeAutoAssignHtml(item) + '</li>'; }).join('') + '</ul></div>' : '') +\n"
            "          (assignableReviewerIds.length ? '<div class=\"checkbox\"><label><input id=\"include-conflicted-previous-reviewers\" type=\"checkbox\"> Include conflicted previous reviewers, and record a previous-reviewer conflict override for selected previous reviewers if OpenReview reports a conflict at submit time.</label></div>' : '') +"
        )
        web = web.replace(
            "              if (includeConflicted && conflictedReviewerIds.indexOf(tail) >= 0) {\n"
            "                postBody.label = 'Previous Reviewer Conflict Override';\n"
            "              }",
            "              if (includeConflicted) {\n"
            "                postBody.label = 'Previous Reviewer Conflict Override';\n"
                "              }"
        )

        def ensure_reviewer_assignment_main_wrapper(current_web):
            if 'main();' not in current_web or re.search(r'(function\s+main\s*\(|var\s+main\b|main\s*=)', current_web):
                return current_web
            render_content_marker = 'function renderContent()'
            render_content_start = current_web.find(render_content_marker)
            if render_content_start < 0:
                raise ValueError(f'Could not refresh reviewer assignment hub for Paper{note.number}: refreshed webfield calls main() but has no main or renderContent definition.')
            main_wrapper = """// Main is the entry point to the webfield code and runs everything
function main() {
  if (args && args.referrer) {
    OpenBanner.referrerLink(args.referrer);
  } else {
    OpenBanner.venueHomepageLink(CONFERENCE_ID + '/Action_Editors');
  }

  Webfield.ui.setup('#invitation-container', CONFERENCE_ID);  // required

  Webfield.ui.header(HEADER.title, HEADER.instructions);

  Webfield.ui.spinner('#notes', { inline: true });

  load().then(renderContent).then(Webfield.ui.done);
}

function load() {
  return $.Deferred().resolve();
}

"""
            return current_web[:render_content_start] + main_wrapper + current_web[render_content_start:]

        web = ensure_reviewer_assignment_main_wrapper(web)
        if 'main();' in web and not re.search(r'(function\s+main\s*\(|var\s+main\b|main\s*=)', web):
            raise ValueError(f'Could not refresh reviewer assignment hub for Paper{note.number}: refreshed webfield calls main() but no main definition remains.')

        reviewer_assignment_invitation.web = web
        reviewer_assignment_group_web = web.replace('#invitation-container', '#group-container')
        paper_reviewers_group = client.get_group(journal.get_reviewers_id(number=note.number))
        paper_reviewers_group.readers = [
            journal.get_action_editors_id(note.number),
            journal.get_editors_in_chief_id()
        ]
        paper_reviewers_group.writers = list(dict.fromkeys(
            list(paper_reviewers_group.writers or []) + [
                journal.venue_id,
                journal.get_action_editors_id(note.number)
            ]
        ))
        paper_reviewers_group.web = reviewer_assignment_group_web
        client.post_group_edit(
            invitation=journal.get_meta_invitation_id(),
            signatures=[journal.venue_id],
            readers=[journal.venue_id],
            writers=[journal.venue_id],
            group=paper_reviewers_group
        )
        client.post_invitation_edit(
            invitations=journal.get_meta_invitation_id(),
            signatures=[journal.venue_id],
            invitation=reviewer_assignment_invitation,
            replacement=True
        )

    if not reviewer_assignment_invitation_updated:
        client.post_invitation_edit(
            invitations=journal.get_meta_invitation_id(),
            signatures=[journal.venue_id],
            invitation=reviewer_assignment_invitation,
            replacement=True
        )
