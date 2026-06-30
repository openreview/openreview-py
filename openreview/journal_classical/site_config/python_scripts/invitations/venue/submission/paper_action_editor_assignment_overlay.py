def _assignment_affinity_result_value(row, keys):
    for key in keys:
        if key in row:
            return row[key]
    return None


def _flatten_assignment_affinity_result_dicts(value):
    rows = []
    if isinstance(value, dict):
        rows.append(value)
        for child in value.values():
            rows.extend(_flatten_assignment_affinity_result_dicts(child))
    elif isinstance(value, list):
        for child in value:
            rows.extend(_flatten_assignment_affinity_result_dicts(child))
    return rows


def extract_assignment_affinity_scores(results, note_id):
    scores = {}
    note_keys = ('submission', 'submission_id', 'submissionId', 'paper', 'paper_id', 'paperId', 'forum', 'note', 'note_id', 'noteId', 'head', 'entityB', 'id')
    user_keys = ('user', 'user_id', 'userId', 'profile', 'profile_id', 'profileId', 'member', 'member_id', 'memberId', 'tail', 'entityA')
    score_keys = ('score', 'weight', 'value', 'similarity')
    for row in _flatten_assignment_affinity_result_dicts(results):
        result_note_id = _assignment_affinity_result_value(row, note_keys)
        if isinstance(result_note_id, dict):
            result_note_id = _assignment_affinity_result_value(result_note_id, ('id', 'forum', 'noteId'))
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
        profile_id = _assignment_affinity_result_value(row, user_keys)
        score_value = _assignment_affinity_result_value(row, score_keys)
        if isinstance(profile_id, dict):
            profile_id = _assignment_affinity_result_value(profile_id, ('id', 'profile_id', 'user'))
        if result_note_id != note_id or not isinstance(profile_id, str) or not profile_id.startswith('~'):
            continue
        try:
            scores[profile_id] = float(score_value)
        except Exception:
            continue
    return scores


def active_assignment_affinity_edges_exist(client, journal, note, affinity_invitation_id):
    try:
        edges = client.get_edges(
            invitation=affinity_invitation_id,
            head=note.id,
            domain=journal.venue_id,
            limit=1
        )
    except TypeError:
        edges = client.get_edges(
            invitation=affinity_invitation_id,
            head=note.id,
            limit=1
        )
    except Exception as error:
        print(f'Could not check affinity edges for Paper{note.number}: {error}')
        return True
    return any(not getattr(edge, 'ddate', None) for edge in edges or [])


def _content_value(note, key, default=""):
    value = note.content.get(key, {}).get("value")
    return str(value if value is not None else default)


def _has_value(value):
    return value is not None and str(value).strip() and str(value).strip().upper() != "N/A"


def _copy_invitation_script_field(client, invitation_id, field_name):
    invitation = client.get_invitation(invitation_id)
    script = getattr(invitation, field_name, None)
    if script:
        return script
    invitation_edit = getattr(invitation, "edit", None)
    if isinstance(invitation_edit, dict):
        child_invitation = invitation_edit.get("invitation")
        if isinstance(child_invitation, dict):
            script = child_invitation.get(field_name)
            if script:
                return script
    return None


class _RawInvitationEditPayload:
    def __init__(self, payload):
        self.payload = payload

    def to_json(self):
        return self.payload


class _RawGroupEditPayload:
    def __init__(self, payload):
        self.payload = payload

    def to_json(self):
        return self.payload


def _group_content_with_assignment_web(group, assignment_page_group_web):
    content = dict(getattr(group, "content", None) or {})
    content["web"] = {"value": assignment_page_group_web}
    return content


def _group_has_assignment_web(group, assignment_page_group_web):
    if not group:
        return False
    content = getattr(group, "content", None) or {}
    content_web = ""
    if isinstance(content, dict):
        content_web = ((content.get("web") or {}).get("value") or "")
    return getattr(group, "web", None) == assignment_page_group_web and content_web == assignment_page_group_web


def post_action_editor_assignment_group_web(client, journal, group_id, editors_in_chief_id, assignment_page_group_web):
    try:
        group = client.get_group(group_id)
    except Exception:
        group = openreview.api.Group(id=group_id)
    group.readers = list(dict.fromkeys(
        list(getattr(group, "readers", None) or []) + [journal.venue_id, editors_in_chief_id, group_id]
    ))
    group.writers = list(dict.fromkeys(
        list(getattr(group, "writers", None) or []) + [journal.venue_id]
    ))
    group.web = assignment_page_group_web
    group.content = _group_content_with_assignment_web(group, assignment_page_group_web)
    client.post_group_edit(
        invitation=journal.get_meta_invitation_id(),
        signatures=[journal.venue_id],
        readers=[journal.venue_id],
        writers=[journal.venue_id],
        group=group,
    )
    try:
        refreshed_group = client.get_group(group_id)
    except Exception:
        refreshed_group = None
    if _group_has_assignment_web(refreshed_group, assignment_page_group_web):
        return

    client.post_group_edit(
        invitation=journal.get_meta_invitation_id(),
        signatures=[journal.venue_id],
        readers=[journal.venue_id],
        writers=[journal.venue_id],
        group=_RawGroupEditPayload({
            "id": group_id,
            "readers": list(dict.fromkeys(
                list(getattr(group, "readers", None) or []) + [journal.venue_id, editors_in_chief_id, group_id]
            )),
            "writers": list(dict.fromkeys(
                list(getattr(group, "writers", None) or []) + [journal.venue_id]
            )),
            "web": assignment_page_group_web,
            "content": {
                "web": {"value": assignment_page_group_web},
            },
        }),
    )
    try:
        refreshed_group = client.get_group(group_id)
    except Exception:
        refreshed_group = None
    if not _group_has_assignment_web(refreshed_group, assignment_page_group_web):
        raise openreview.OpenReviewException(
            f"Action Editor assignment group {group_id} did not retain the assignment-page webfield."
        )


def _assignment_overlay_context(journal, note):
    venue_id = journal.venue_id
    paper_group_id = f"{venue_id}/Paper{note.number}"
    paper_author_group_id = f"{paper_group_id}/Authors"
    paper_action_editors_group_id = f"{paper_group_id}/Action_Editors"
    paper_reviewers_group_id = f"{paper_group_id}/Reviewers"
    editors_in_chief_id = journal.get_editors_in_chief_id()
    action_editors_id = journal.get_action_editors_id()
    assignment_invitation_id = f"{paper_action_editors_group_id}/-/Assignment"
    assignment_page_group_id = paper_action_editors_group_id
    assignment_page_base_url = f"/group?id={assignment_page_group_id}"
    assignment_page_url = (
        assignment_page_base_url
        + f"&assignAePaper={note.id}"
        + f"&assignmentInvitation={assignment_invitation_id}"
    )
    authorids = [
        authorid
        for authorid in note.content.get("authorids", {}).get("value", [])
        if authorid
    ]
    return {
        "venue_id": venue_id,
        "paper_group_id": paper_group_id,
        "paper_author_group_id": paper_author_group_id,
        "paper_action_editors_group_id": paper_action_editors_group_id,
        "paper_reviewers_group_id": paper_reviewers_group_id,
        "editors_in_chief_id": editors_in_chief_id,
        "action_editors_id": action_editors_id,
        "assignment_invitation_id": assignment_invitation_id,
        "assignment_page_group_id": assignment_page_group_id,
        "assignment_page_base_url": assignment_page_base_url,
        "assignment_page_url": assignment_page_url,
        "authorids": authorids,
    }


def action_editor_assignment_browser_contract(journal, note, assignment_invitation_id, assignment_page_url):
    venue_id = journal.venue_id
    action_editors_id = journal.get_action_editors_id()
    reviewer_assignment_id = getattr(
        journal,
        "get_reviewer_assignment_id",
        lambda number=None: f"{venue_id}/Paper{number}/Reviewers/-/Assignment",
    )(number=note.number)
    paper_reviewers_id = getattr(
        journal,
        "get_reviewers_id",
        lambda number=None: f"{venue_id}/Paper{number}/Reviewers" if number else f"{venue_id}/Reviewers",
    )(number=note.number)
    ae_affinity_id = getattr(journal, "get_ae_affinity_score_id", lambda: f"{action_editors_id}/-/Affinity_Score")()
    ae_conflict_id = getattr(journal, "get_ae_conflict_id", lambda: f"{action_editors_id}/-/Conflict")()
    reviewer_conflict_id = getattr(journal, "get_reviewer_conflict_id", lambda: f"{venue_id}/Reviewers/-/Conflict")()
    ae_availability_id = getattr(journal, "get_ae_availability_id", lambda: f"{action_editors_id}/-/Assignment_Availability")()
    ae_assignment_id = journal.get_ae_assignment_id()
    try:
        ae_archived_assignment_id = journal.get_ae_assignment_id(archived=True)
    except TypeError:
        ae_archived_assignment_id = f"{action_editors_id}/-/Archived_Assignment"
    return {
        "paper_id": note.id,
        "paper_number": note.number,
        "assignment_invitation": assignment_invitation_id,
        "deployed_assignment_sources": [
            assignment_invitation_id,
        ],
        "readback_assignment_sources": [
            assignment_invitation_id,
        ],
        "reviewer_entry_sources": {
            "reviewer_assignment_invitation": reviewer_assignment_id,
            "paper_reviewers_group": paper_reviewers_id,
        },
        "score_sources": {
            "affinity_score_invitation": ae_affinity_id,
            "matching_input_group": action_editors_id,
        },
        "conflict_sources": {
            "openreview_conflict_invitation": ae_conflict_id,
            "reviewer_conflict_invitation": reviewer_conflict_id,
            "candidate_refresh_invitation": f"{venue_id}/-/Action_Editor_Candidate_Conflict_Refresh",
            "hard_author_fields": ["authorids", "author_list", "conflict_of_interests"],
        },
        "availability_sources": {
            "action_editor_availability_invitation": ae_availability_id,
            "action_editor_group": action_editors_id,
        },
        "load_sources": {
            "custom_max_papers_invitation": action_editors_id + "/-/Custom_Max_Papers",
            "assignment_history_sources": [
                assignment_invitation_id,
                ae_assignment_id,
                ae_archived_assignment_id,
            ],
        },
        "filter_semantics": {
            "candidate_group": action_editors_id,
            "requires_current_action_editor_membership": True,
            "blocks_hard_author_conflicts": True,
            "openreview_conflicts_are_override_warnings": True,
            "checks_active_load_and_cooldown": True,
            "excludes_current_action_editor_from_new_assignment": True,
        },
        "allowed_signatures": [
            journal.get_editors_in_chief_id(),
        ],
        "legacy_read_only_sources": [
            ae_assignment_id,
            ae_archived_assignment_id,
        ],
        "ui_boundary": {
            "visible_default_route": assignment_page_url,
            "raw_edges_browse_default": False,
        },
    }


def build_paper_action_editor_assignment_web(note, assignment_invitation_id, assignment_browser_contract=None, target_container="#invitation-container"):
    json = __import__("json")
    assignment_browser_contract = assignment_browser_contract or {
        "paper_id": note.id,
        "paper_number": note.number,
        "assignment_invitation": assignment_invitation_id,
    }
    web = "\n".join([
        "var ASSIGN_AE_WEBFIELD_SOURCE_GROUP_ID = 'JMLR/Editors_In_Chief';",
        "var ASSIGN_AE_WEBFIELD_CONTENT_KEY = 'assign_action_editor_webfield_script';",
        f"var ASSIGN_AE_PAPER_ID = {note.id!r};",
        f"var ASSIGN_AE_ASSIGNMENT_INVITATION_ID = {assignment_invitation_id!r};",
        f"var ASSIGN_AE_ASSIGNMENT_BROWSER_CONTRACT = {json.dumps(assignment_browser_contract)};",
        f"var ASSIGN_AE_TARGET_CONTAINER = {target_container!r};",
        "(function() {",
        "  var targetContainer = typeof ASSIGN_AE_TARGET_CONTAINER !== 'undefined' ? ASSIGN_AE_TARGET_CONTAINER : '#invitation-container';",
        "  var showError = function(message) {",
        "    if (typeof Webfield2 !== 'undefined' && Webfield2.ui && Webfield2.ui.errorMessage) {",
        "      Webfield2.ui.errorMessage(message);",
        "      return;",
        "    }",
        "    var $container = $(targetContainer);",
        "    if (!$container.length) $container = $('body');",
        "    $container.html('<div class=\"alert alert-danger\" role=\"alert\"></div>');",
        "    $container.children().first().text(String(message));",
        "  };",
        "  var readScript = function(group) {",
        "    return group && group.content && group.content[ASSIGN_AE_WEBFIELD_CONTENT_KEY] && group.content[ASSIGN_AE_WEBFIELD_CONTENT_KEY].value;",
        "  };",
        "  var runScript = function(source) {",
        "    if (!source) {",
        "      showError('The Action Editor assignment page webfield is not installed.');",
        "      return;",
        "    }",
        "    if (targetContainer !== '#invitation-container') {",
        "      source = String(source).replace(/#invitation-container/g, targetContainer);",
        "    }",
        "    (new Function('args', 'user', 'ASSIGN_AE_PAPER_ID', 'ASSIGN_AE_ASSIGNMENT_INVITATION_ID', 'ASSIGN_AE_ASSIGNMENT_BROWSER_CONTRACT', source))(",
        "      typeof args !== 'undefined' && args ? args : {},",
        "      typeof user !== 'undefined' && user ? user : {},",
        "      ASSIGN_AE_PAPER_ID,",
        "      ASSIGN_AE_ASSIGNMENT_INVITATION_ID,",
        "      ASSIGN_AE_ASSIGNMENT_BROWSER_CONTRACT",
        "    );",
        "  };",
        "  if (typeof Webfield2 === 'undefined' || !Webfield2.api || !Webfield2.api.get) {",
        "    showError('OpenReview Webfield2 API is unavailable.');",
        "    return;",
        "  }",
        "  Webfield2.api.get('/groups', {",
        "    id: ASSIGN_AE_WEBFIELD_SOURCE_GROUP_ID,",
        "    limit: 1,",
        "    select: 'id,content'",
        "  }).then(function(result) {",
        "    var group = result && result.groups && result.groups[0];",
        "    if (!group) {",
        "      showError('The Action Editor assignment page source group is not readable.');",
        "      return;",
        "    }",
        "    runScript(readScript(group));",
        "  }).fail(function(error) {",
        "    showError(error && (error.message || (error.responseJSON && error.responseJSON.message)) || error || 'Could not load the Action Editor assignment page.');",
        "  });",
        "}());",
    ])
    return web


def request_action_editor_affinity_for_assignment_page(client, journal, note, wait_for_complete=False):
    datetime = __import__('datetime')
    affinity_model = getattr(journal, 'get_expertise_model', lambda: '{{EXPERTISE_MODEL}}')()
    job_name = f"jmlr-{journal.venue_id.replace('/', '-')}-ae-affinity-paper{note.number}-{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    submissions = [{
        'id': note.id,
        'title': note.content.get('title', {}).get('value', ''),
        'abstract': note.content.get('abstract', {}).get('value', '')
    }]
    payload = {
        'name': job_name,
        'entityA': {
            'type': 'Group',
            'memberOf': journal.get_action_editors_id()
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
            journal.get_action_editors_id(),
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
            raise openreview.OpenReviewException(f"Action Editor affinity Expertise request failed with HTTP {http_response.status_code}: {http_response.text[:500]}")
        response = http_response.json()
    job_id = response.get('jobId') or response.get('job_id') or response.get('id')
    if not job_id:
        raise openreview.OpenReviewException(f'Action Editor affinity Expertise request did not return a job id for Paper{note.number}.')
    if not wait_for_complete:
        try:
            status_response = client.get_expertise_status(job_id)
            status = status_response.get('status')
        except Exception as error:
            print(f'Action Editor affinity Expertise job {job_id} was requested for Paper{note.number}; status was not immediately readable: {error}')
            return 0
        if status != 'Completed':
            print(f'Action Editor affinity Expertise job {job_id} was requested for Paper{note.number}; current status is {status or "unknown"}.')
            return 0
    results = client.get_expertise_results(job_id, wait_for_complete=wait_for_complete)
    action_editor_scores = extract_assignment_affinity_scores(results, note.id)
    if not action_editor_scores:
        raise openreview.OpenReviewException(f'Action Editor affinity Expertise job {job_id} returned no parseable scores for Paper{note.number}.')
    affinity_invitation = journal.get_ae_affinity_score_id()
    posted_count = 0
    for profile_id, score in sorted(action_editor_scores.items()):
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
    print(f'Posted {posted_count} Action Editor affinity scores for Paper{note.number} from Expertise job {job_id}.')
    return posted_count


def ensure_action_editor_affinity_on_first_assignment_page_create(client, journal, note, assignment_invitation_existed):
    if assignment_invitation_existed:
        return 'assignment_page_already_exists'
    if active_assignment_affinity_edges_exist(client, journal, note, journal.get_ae_affinity_score_id()):
        return 'affinity_edges_already_exist'
    try:
        posted_count = request_action_editor_affinity_for_assignment_page(client, journal, note, wait_for_complete=False)
        return 'affinity_computed' if posted_count else 'affinity_requested'
    except Exception as error:
        print(f'Could not compute Action Editor affinity for first assignment page for Paper{note.number}: {error}')
        return 'affinity_blocked'


def setup_paper_action_editor_forum_launcher(client, journal, note):
    context = _assignment_overlay_context(journal, note)
    venue_id = context["venue_id"]
    paper_group_id = context["paper_group_id"]
    editors_in_chief_id = context["editors_in_chief_id"]
    assignment_page_url = context["assignment_page_url"]
    authorids = context["authorids"]

    wrapper_invitation_id = f"{paper_group_id}/-/Assign_Action_Editor"
    launcher_description = "{{MESSAGE_TEMPLATE_JSON:assignment_launchers/assign_action_editor_redirect_description.html}}".format(
        submission_number=note.number,
        submission_title=_content_value(note, "title", f"Paper {note.number}"),
        assignment_page_url=assignment_page_url,
    )
    redirect_web = "\n".join([
        f"var ASSIGN_AE_ASSIGNMENT_PAGE_URL = {assignment_page_url!r};",
        "var main = function() {",
        "  var target = typeof ASSIGN_AE_ASSIGNMENT_PAGE_URL !== 'undefined' ? ASSIGN_AE_ASSIGNMENT_PAGE_URL : '';",
        "  if (!target) {",
        "    Webfield2.ui.setup('#invitation-container', 'JMLR', {",
        "      title: 'Assign Action Editor',",
        "      instructions: '<p class=\"text-danger\">The Action Editor assignment page is unavailable for this launcher.</p>',",
        "      fullWidth: true",
        "    });",
        "    Webfield2.ui.done();",
        "    return;",
        "  }",
        "  if (globalThis.top) globalThis.top.location.replace(target);",
        "  else globalThis.location.replace(target);",
        "};",
        "",
        "main();",
    ])
    launcher_process = "\n".join([
        "def process(client, edit, invitation):",
        "    import datetime",
        "    journal = openreview.journal.JournalRequest.get_journal(client, \"{{PROD_JOURNAL_ID}}\")",
        "    helper_note = client.get_note(edit.note.id)",
        "    client.post_note_edit(",
        "        invitation=journal.get_meta_invitation_id(),",
        "        signatures=[journal.venue_id],",
        "        note=openreview.api.Note(",
        "            id=helper_note.id,",
        "            readers=[journal.get_editors_in_chief_id()],",
        "            nonreaders=helper_note.nonreaders or [],",
        "            writers=[journal.venue_id],",
        "            ddate=openreview.tools.datetime_millis(datetime.datetime.now())",
        "        )",
        "    )",
    ])
    client.post_invitation_edit(
        invitations=journal.get_meta_invitation_id(),
        signatures=[venue_id],
        readers=[venue_id],
        writers=[venue_id],
        invitation=openreview.api.Invitation(
            id=wrapper_invitation_id,
            readers=[editors_in_chief_id],
            writers=[venue_id],
            invitees=[editors_in_chief_id],
            nonreaders=authorids,
            signatures=[venue_id],
            maxReplies=1,
            description=launcher_description,
            web=redirect_web,
            edit={
                "signatures": [editors_in_chief_id],
                "readers": [editors_in_chief_id],
                "nonreaders": authorids,
                "writers": [venue_id],
                "note": {
                    "id": {"param": {"withInvitation": wrapper_invitation_id, "optional": True}},
                    "forum": note.id,
                    "replyto": note.id,
                    "signatures": [editors_in_chief_id],
                    "readers": [editors_in_chief_id],
                    "nonreaders": authorids,
                    "writers": [venue_id],
                    "content": {
                        "assignment_page": {
                            "order": 1,
                            "description": "Open the paper-specific Action Editor assignment page.",
                            "value": {
                                "param": {
                                    "type": "string",
                                    "const": assignment_page_url,
                                    "hidden": True,
                                }
                            },
                        }
                    },
                },
            },
            process=launcher_process,
        ),
        replacement=True,
    )
    client.get_invitation(wrapper_invitation_id)
    return wrapper_invitation_id


def setup_paper_action_editor_assignment_overlay(client, journal, note):
    import datetime

    context = _assignment_overlay_context(journal, note)
    venue_id = context["venue_id"]
    paper_author_group_id = context["paper_author_group_id"]
    paper_action_editors_group_id = context["paper_action_editors_group_id"]
    paper_reviewers_group_id = context["paper_reviewers_group_id"]
    editors_in_chief_id = context["editors_in_chief_id"]
    action_editors_id = context["action_editors_id"]
    assignment_invitation_id = context["assignment_invitation_id"]
    authorids = context["authorids"]
    assignment_invitation_existed = True
    try:
        client.get_invitation(assignment_invitation_id)
    except Exception:
        assignment_invitation_existed = False
    assignment_browser_contract = action_editor_assignment_browser_contract(
        journal,
        note,
        assignment_invitation_id,
        context["assignment_page_url"],
    )
    selected_signature_param = "$" + "{3/signatures}"
    selected_tail_param = "$" + "{2/tail}"
    assignment_edge = {
        "id": {"param": {"withInvitation": assignment_invitation_id, "optional": True}},
        "ddate": {"param": {"range": [0, 9999999999999], "optional": True, "deletable": True}},
        "cdate": {"param": {"range": [0, 9999999999999], "optional": True, "deletable": True}},
        "readers": [editors_in_chief_id, paper_action_editors_group_id, selected_tail_param],
        "nonreaders": [paper_author_group_id] + authorids,
        "writers": [editors_in_chief_id],
        "signatures": {"param": {"items": [{"value": editors_in_chief_id, "optional": True}]}},
        "head": {"param": {"type": "note", "const": note.id}},
        "tail": {"param": {"type": "profile", "options": {"group": action_editors_id}}},
        "weight": {"param": {"minimum": -1}},
        "label": {"param": {"optional": True, "deletable": True, "minLength": 1}},
    }
    client.post_invitation_edit(
        invitations=journal.get_meta_invitation_id(),
        signatures=[venue_id],
        readers=[venue_id],
        writers=[venue_id],
        invitation=_RawInvitationEditPayload({
            "id": assignment_invitation_id,
            "readers": [editors_in_chief_id],
            "writers": [venue_id],
            "invitees": [editors_in_chief_id],
            "signatures": [venue_id],
            "preprocess": _copy_invitation_script_field(client, journal.get_ae_assignment_id(), "preprocess"),
            "process": _copy_invitation_script_field(client, journal.get_ae_assignment_id(), "process"),
            "web": build_paper_action_editor_assignment_web(note, assignment_invitation_id, assignment_browser_contract),
            "edge": assignment_edge,
        }),
        replacement=True,
    )
    assignment_page_group_web = build_paper_action_editor_assignment_web(
        note,
        assignment_invitation_id,
        assignment_browser_contract,
        target_container="#group-container",
    )
    post_action_editor_assignment_group_web(
        client,
        journal,
        paper_action_editors_group_id,
        editors_in_chief_id,
        assignment_page_group_web,
    )
    setup_paper_action_editor_forum_launcher(client, journal, note)

    paper_group_id = context["paper_group_id"]
    decision_invitation_id = f"{paper_group_id}/-/Decision"
    now = datetime.datetime.now()
    decision_duedate = now + datetime.timedelta(days=7)
    early_rejection_comment = "{{MESSAGE_TEMPLATE_JSON:decision/pre_ae_rejection_comment_default.txt}}".format(
        submission_number=note.number,
        submission_title=_content_value(note, "title", f"Paper {note.number}"),
    )
    client.post_invitation_edit(
        invitations=journal.get_meta_invitation_id(),
        signatures=[venue_id],
        readers=[venue_id],
        writers=[venue_id],
        invitation=openreview.api.Invitation(
            id=decision_invitation_id,
            invitations=[f"{venue_id}/-/Decision"],
            cdate=openreview.tools.datetime_millis(now),
            duedate=openreview.tools.datetime_millis(decision_duedate),
            readers=[editors_in_chief_id],
            nonreaders=[paper_author_group_id] + authorids,
            writers=[venue_id],
            invitees=[editors_in_chief_id],
            signatures=[editors_in_chief_id],
            maxReplies=1,
            minReplies=1,
            edit={
                "signatures": {"param": {"items": [{"value": editors_in_chief_id, "optional": True}]}},
                "readers": [editors_in_chief_id],
                "nonreaders": [paper_author_group_id] + authorids,
                "writers": [editors_in_chief_id],
                "note": {
                    "forum": note.id,
                    "replyto": note.id,
                    "signatures": [selected_signature_param],
                    "readers": [editors_in_chief_id, paper_action_editors_group_id, paper_reviewers_group_id],
                    "nonreaders": [paper_author_group_id] + authorids,
                    "writers": [editors_in_chief_id],
                    "content": {
                        "recommendation": {
                            "order": 1,
                            "description": "Pre-assignment Decision. The only allowed recommendation before assigning the first Action Editor is Reject without resubmission.",
                            "value": {
                                "param": {
                                    "type": "string",
                                    "enum": ["Reject without resubmission"],
                                    "input": "radio",
                                    "default": "Reject without resubmission",
                                }
                            },
                        },
                        "comment": {
                            "order": 2,
                            "description": "Decision comments to record the reason for not sending this paper to Action Editor assignment. The default text may be edited before submission.",
                            "value": {
                                "param": {
                                    "type": "string",
                                    "maxLength": 200000,
                                    "input": "textarea",
                                    "markdown": True,
                                    "default": early_rejection_comment,
                                }
                            },
                        },
                    },
                },
            },
            preprocess=_copy_invitation_script_field(client, journal.get_ae_decision_id(), "preprocess"),
            process=_copy_invitation_script_field(client, journal.get_ae_decision_id(), "process"),
        ),
        replacement=True,
    )
    return assignment_invitation_existed
