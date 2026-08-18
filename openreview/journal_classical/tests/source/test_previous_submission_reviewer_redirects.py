"""Source tests for JMLR's read-only previous-reviewer launcher context."""

from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "site_config"
HELPER = SITE / "python_scripts/invitations/venue/under_review/previous_submission_reviewer_redirects.py"
POLICY = SITE / "python_scripts/invitations/venue/under_review/previous_submission_reviewer_policy.py"
LAUNCHER = SITE / "web_fragments/assignment_launchers/previous_reviewer_redirects.js"
POSTPROCESS = SITE / "python_scripts/invitations/venue/under_review/postprocess.py"
UNDER_REVIEW = SITE / "invitations/venue/under_review/invitation/invitation.json"


def load_helper():
    namespace = {}
    source = HELPER.read_text(encoding="utf-8")
    source = source.replace(
        "# {{PYTHON_SCRIPT_FILE:invitations/venue/under_review/previous_submission_reviewer_policy.py}}",
        POLICY.read_text(encoding="utf-8"),
    )
    source = re.sub(
        r'"?\{\{WEB_FRAGMENT_JSON:assignment_launchers/previous_reviewer_redirects.js\}\}"?',
        lambda _match: json.dumps(LAUNCHER.read_text(encoding="utf-8")), source,
    )
    exec(compile(source, str(HELPER), "exec"), namespace)
    return namespace


class FakeJournal:
    venue_id = "JMLR"

    def get_author_submission_id(self):
        return "JMLR/-/Submission"

    def get_reviewer_assignment_id(self, number=None, archived=False):
        if number is not None:
            return f"JMLR/Paper{number}/Reviewers/-/Assignment"
        return f"JMLR/Reviewers/-/{'Archived_Assignment' if archived else 'Assignment'}"

    def get_meta_invitation_id(self):
        return "JMLR/-/Edit"

    def get_action_editors_id(self, number=None, anon=False):
        if number is None:
            return "JMLR/Action_Editor_" if anon else "JMLR/Action_Editors"
        return f"JMLR/Paper{number}/{'Action_Editor_' if anon else 'Action_Editors'}"

    def get_authors_id(self, number=None):
        return "JMLR/Authors" if number is None else f"JMLR/Paper{number}/Authors"


def submission(note_id, number, previous_url=None, *, domain="JMLR", invitations=None):
    content = {"venueid": {"value": "JMLR/Under_Review"}}
    if previous_url is not None:
        content["previous_JMLR_submission_url"] = {"value": previous_url}
    return SimpleNamespace(
        id=note_id, number=number, domain=domain,
        invitations=invitations or ["JMLR/-/Submission"], content=content,
    )


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://openreview.net/forum?id=prior", "prior"),
        ("https://dev.openreview.net/forum?id=prior", "prior"),
        ("https://dev.openreview.net/forum?foo=1&id=prior&bar=2", "prior"),
        ("https://dev.openreview.net/forum", None),
        ("https://dev.openreview.net/forum?id=", None),
        ("https://dev.openreview.net/forum?id=one&id=two", None),
        ("https://dev.openreview.net/forum?id=%20prior", None),
        ("http://openreview.net/forum?id=prior", None),
        ("https://example.org/forum?id=prior", None),
        ("https://openreview.net:443/forum?id=prior", None),
        ("https://user@openreview.net/forum?id=prior", None),
        ("https://openreview.net/group?id=prior", None),
    ],
)
def test_structural_forum_url_parser(url, expected):
    assert load_helper()["parse_openreview_forum_id"](url) == expected


def test_previous_submission_resolution_fails_closed():
    helper = load_helper()["resolve_previous_submission"]
    current = submission("current", 2, "https://dev.openreview.net/forum?id=prior")
    unreadable = SimpleNamespace(get_note=lambda _id: (_ for _ in ()).throw(RuntimeError("denied")))
    assert helper(unreadable, FakeJournal(), current) is None
    assert helper(SimpleNamespace(get_note=lambda _id: submission("other", 1)), FakeJournal(), current) is None
    assert helper(SimpleNamespace(get_note=lambda _id: submission("prior", 1, domain="Foreign")), FakeJournal(), current) is None
    assert helper(SimpleNamespace(get_note=lambda _id: submission("prior", 1, invitations=["JMLR/-/Other"])), FakeJournal(), current) is None


def test_derivation_uses_only_active_and_archived_assignments_and_dedupes():
    active = SimpleNamespace(tail="~Reviewer1", ddate=None)
    archived_duplicate = SimpleNamespace(tail="~Reviewer1", ddate=None)
    archived = SimpleNamespace(tail="~Reviewer2", ddate=None)
    removed = SimpleNamespace(tail="~Removed", ddate=123)
    task = SimpleNamespace(tail="JMLR/Paper1/Reviewers", ddate=None)
    email_tail = SimpleNamespace(tail="person@example.org", ddate=None)

    class Client:
        def get_edges(self, invitation, head):
            assert head == "prior"
            assert "Invite_Assignment" not in invitation
            if invitation.endswith("/Archived_Assignment"):
                return [archived_duplicate, archived]
            if invitation.endswith("/Assignment"):
                return [active, removed, task, email_tail]
            raise AssertionError(invitation)

    assert load_helper()["prior_reviewer_ids"](Client(), FakeJournal(), submission("prior", 1)) == ["~Reviewer1", "~Reviewer2"]


def test_derivation_rejects_malformed_profile_tails():
    probe_tails = ["~", "~Good1", "~bad tail1", "~group/child1"]

    class Client:
        def get_edges(self, invitation, head):
            assert head == "prior"
            return (
                [SimpleNamespace(tail=tail, ddate=None) for tail in probe_tails]
                if invitation.endswith("/Assignment")
                and not invitation.endswith("/Archived_Assignment")
                else []
            )

    assert load_helper()["prior_reviewer_ids"](
        Client(), FakeJournal(), submission("prior", 1)
    ) == ["~Good1"]


@pytest.mark.parametrize(
    "profile_id",
    [
        "~Good1",
        "~Haw-Shiuan_Chang1",
        "~Nihar_B._Shah1",
        "~Merve_Gürel1",
        "~Ruei-Yao_Sun1",
        "~First_Last23",
    ],
)
def test_profile_id_validator_accepts_canonical_openreview_ids(profile_id):
    assert load_helper()["is_openreview_profile_id"](profile_id)


@pytest.mark.parametrize(
    "profile_id",
    [
        None,
        "",
        "~",
        " ~Good1",
        "~Good1 ",
        "~bad tail1",
        "~group/child1",
        "~NoNumericSuffix",
        "person@example.org",
        "JMLR/Reviewers",
    ],
)
def test_profile_id_validator_rejects_noncanonical_tails(profile_id):
    assert not load_helper()["is_openreview_profile_id"](profile_id)


def test_assignment_read_failure_is_a_safe_empty_result():
    client = SimpleNamespace(get_edges=lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("denied")))
    assert load_helper()["prior_reviewer_ids"](client, FakeJournal(), submission("prior", 1)) == []


def test_safe_names_collisions_ordering_and_profile_fallback_use_names_only():
    profiles = {
        "~A": SimpleNamespace(content={"names": [{"fullname": "Same"}], "email": "never@example.org"}),
        "~B": SimpleNamespace(content={"names": [{"fullname": " Same ", "preferred": True}], "emails": ["never@example.org"]}),
        "~C": SimpleNamespace(content={"names": [{"fullname": "Zulu"}, {"fullname": "Alpha", "preferred": True}], "preferredEmail": "never@example.org"}),
    }

    class Client:
        def get_profile(self, profile_id):
            if profile_id == "~D":
                raise RuntimeError("unreadable")
            return profiles[profile_id]

    assert load_helper()["safe_reviewer_rows"](Client(), ["~C", "~D", "~B", "~A"]) == [
        {"id": "~C", "displayName": "Alpha"},
        {"id": "~A", "displayName": "Same (~A)"},
        {"id": "~B", "displayName": "Same (~B)"},
        {"id": "~D", "displayName": "~D"},
    ]


def test_web_overlay_preserves_edge_browser_params_and_forum_id_is_independent():
    transform = load_helper()["reviewer_assignment_browser_web"]
    params = "start=staticList,type:head,ids:current&traverse=kept&edit=kept&browse=kept&filter=x%20y&maxColumns=2&version=2&referrer=kept"
    original = f"var EDGE_BROWSER_PARAMS = '{params}';\n// Go!\nmain();"
    rows = [{"id": "~R", "displayName": "Name <unsafe>"}]
    linked = transform(original, "prior<&", rows)
    assert f"var EDGE_BROWSER_PARAMS = '{params}';" in linked
    assert "JMLRPreviousReviewerRedirects.install" in linked
    assert '"displayName": "Name \\u003cunsafe\\u003e"' in linked
    assert '"previousForumId": "prior\\u003c\\u0026"' in linked
    generic = transform(linked, None, [])
    assert f"var EDGE_BROWSER_PARAMS = '{params}';" in generic
    assert "JMLRPreviousReviewerRedirects.install" in generic
    assert '"reviewers": []' in generic
    assert '"previousForumId": null' in generic
    assert "Name <unsafe>" not in generic


def test_launcher_has_checked_prior_reviewer_action_and_preserves_generic_browser():
    source = LAUNCHER.read_text(encoding="utf-8")

    assert "reviewer.displayName" in source
    assert "Assign previous reviewer" in source
    assert "Webfield2.api.post('/edges'" in source
    assert "refreshAssignmentState(liveConfig, Webfield2.api)" in source
    assert "waitForAssignment(config, edge.tail, Webfield2.api, 120)" in source
    assert "continuityAssignmentEdge" in source
    assert "function bindAssignmentAction(config)" in source
    assert "$('#notes').off('click.jmlrPreviousReviewer')" in source
    assert source.index("$('#notes').empty().append") < source.rindex(
        "bindAssignmentAction(liveConfig);"
    )
    assert source.count("jmlr-view-previous-paper") == 1
    assert "View previous paper and its reviews" in source
    assert "Browse all reviewers" in source
    assert "'/edges/browse?'" in source
    assert "Previous_Assignment" not in source


def test_launcher_refreshes_and_waits_for_persisted_assignment_state():
    script = f"""
const redirects = require({json.dumps(str(LAUNCHER))});
const config = {{ assignmentInvitationId: 'JMLR/Reviewers/-/Assignment',
  submissionId: 'current', reviewers: [{{id: '~Reviewer1', displayName: 'R'}}] }};
let calls = 0;
const api = {{ get: (_path, params) => {{
  calls += 1;
  if (_path !== '/edges' || params.invitation !== config.assignmentInvitationId || params.head !== 'current')
    throw new Error('wrong query');
  return Promise.resolve({{edges: calls < 2 ? [] : [{{tail:'~Reviewer1', weight:1}}]}});
}} }};
redirects.waitForAssignment(config, '~Reviewer1', api, 2).then(result =>
  process.stdout.write(JSON.stringify({{calls, assigned:result.reviewers[0].assigned}})));
"""
    result = subprocess.run(
        ["node", "-e", script], check=True, capture_output=True, text=True,
    )
    assert json.loads(result.stdout) == {"calls": 2, "assigned": True}


def test_continuity_action_builds_the_normal_checked_assignment_edge():
    script = f"""
const redirects = require({json.dumps(str(LAUNCHER))});
const edge = redirects.continuityAssignmentEdge({{
  venueId: 'JMLR',
  submissionId: 'current',
  assignmentInvitationId: 'JMLR/Reviewers/-/Assignment',
  paperActionEditorsId: 'JMLR/Paper2/Action_Editors',
  paperActionEditorSignatureId: 'JMLR/Paper2/Action_Editor_abcd',
  paperAuthorsId: 'JMLR/Paper2/Authors'
}}, '~Prior_Reviewer1');
process.stdout.write(JSON.stringify(edge));
"""
    result = subprocess.run(
        ["node", "-e", script],
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(result.stdout) == {
        "invitation": "JMLR/Reviewers/-/Assignment",
        "signatures": ["JMLR/Paper2/Action_Editor_abcd"],
        "readers": [
            "JMLR",
            "JMLR/Paper2/Action_Editors",
            "~Prior_Reviewer1",
        ],
        "nonreaders": ["JMLR/Paper2/Authors"],
        "writers": ["JMLR", "JMLR/Paper2/Action_Editors"],
        "head": "current",
        "tail": "~Prior_Reviewer1",
        "weight": 1,
    }


def test_launcher_renders_an_existing_assignment_as_disabled():
    script = f"""
const redirects = require({json.dumps(str(LAUNCHER))});
const html = redirects.renderWithUrl({{
  previousForumId: 'prior',
  reviewers: [{{ id: '~Prior_Reviewer1', displayName: 'Prior Reviewer', assigned: true }}]
}}, '/edges/browse?kept', 'https://dev.openreview.net');
process.stdout.write(html);
"""
    result = subprocess.run(
        ["node", "-e", script],
        check=True,
        capture_output=True,
        text=True,
    )
    assert '>Assigned</button>' in result.stdout
    assert 'disabled' in result.stdout
    assert 'Previous reviewer assigned.' in result.stdout
    assert '>Assign previous reviewer</button>' not in result.stdout


def test_launcher_preserves_string_api_errors():
    script = f"""
const redirects = require({json.dumps(str(LAUNCHER))});
process.stdout.write(redirects.assignmentErrorMessage('server rejection'));
"""
    result = subprocess.run(
        ["node", "-e", script],
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout == "server rejection"


def test_under_review_overlay_wires_only_the_context_postprocess():
    invitation = json.loads(UNDER_REVIEW.read_text(encoding="utf-8"))
    source = POSTPROCESS.read_text(encoding="utf-8")

    assert invitation == {
        "postprocesses": [
            {
                "script": "{{PYTHON_SCRIPT_JSON:invitations/venue/under_review/postprocess.py}}"
            }
        ]
    }
    assert source.lstrip().startswith("def process(client, edit, invitation):")
    assert source.index("def process") < source.index("PYTHON_SCRIPT_FILE")
    assert "prepare_previous_submission_reviewer_redirects" in source
    assert "post_edge" not in source


def test_prepare_updates_only_the_webfield_and_performs_no_edge_write():
    helper = load_helper()["prepare_previous_submission_reviewer_redirects"]
    current = submission("current", 2, "https://dev.openreview.net/forum?id=prior")
    invitation = SimpleNamespace(web="var EDGE_BROWSER_PARAMS = 'kept';\n// Go!\nmain();")
    writes = []

    class Client:
        def get_note(self, note_id):
            assert note_id == "prior"
            return submission("prior", 1)
        def get_edges(self, invitation, head):
            return [SimpleNamespace(tail="~Reviewer1", ddate=None)] if invitation.endswith("/Assignment") and "Archived" not in invitation else []
        def get_profile(self, profile_id):
            return SimpleNamespace(content={"names": [{"fullname": "Reviewer"}]})
        def get_invitation(self, invitation_id):
            assert invitation_id == "JMLR/Paper2/Reviewers/-/Assignment"
            return invitation
        def get_group(self, group_id):
            assert group_id == "JMLR/Paper2/Action_Editors"
            return SimpleNamespace(members=["~Editor1"])
        def get_groups(self, prefix):
            assert prefix == "JMLR/Paper2/Action_Editor_"
            return [SimpleNamespace(
                id="JMLR/Paper2/Action_Editor_abcd",
                members=["~Editor1"],
            )]
        def post_invitation_edit(self, **kwargs):
            writes.append(kwargs)
        def post_edge(self, *_args, **_kwargs):
            raise AssertionError("redirect preparation must not create an edge")

    helper(Client(), FakeJournal(), current)
    assert len(writes) == 1
    assert writes[0]["invitation"] is invitation
    assert "Reviewer" in invitation.web
    assert '"previousForumId": "prior"' in invitation.web
    assert '"submissionId": "current"' in invitation.web
    assert '"assignmentInvitationId": "JMLR/Reviewers/-/Assignment"' in invitation.web
    assert '"paperActionEditorsId": "JMLR/Paper2/Action_Editors"' in invitation.web
    assert '"paperActionEditorSignatureId": "JMLR/Paper2/Action_Editor_abcd"' in invitation.web
    assert '"paperAuthorsId": "JMLR/Paper2/Authors"' in invitation.web


def test_prepare_waits_for_concurrent_native_assignment_invitation():
    helper = load_helper()["prepare_previous_submission_reviewer_redirects"]
    current = submission("current", 2)
    invitation = SimpleNamespace(web="var EDGE_BROWSER_PARAMS = 'kept';\n// Go!\nmain();")
    lookups = []

    class MissingInvitation(Exception):
        status_code = 404

        def __init__(self):
            super().__init__({"name": "NotFoundError", "status": 404})

    class Client:
        def get_invitation(self, invitation_id):
            lookups.append(invitation_id)
            if len(lookups) == 1:
                raise MissingInvitation()
            return invitation

        def get_edges(self, invitation, head):
            return []

        def post_invitation_edit(self, **_kwargs):
            return None

    helper(Client(), FakeJournal(), current)
    assert lookups == [
        "JMLR/Paper2/Reviewers/-/Assignment",
        "JMLR/Paper2/Reviewers/-/Assignment",
    ]


def test_native_assignment_invitation_wait_does_not_hide_non_not_found_errors():
    wait = load_helper()["wait_for_native_invitation"]

    class Client:
        def get_invitation(self, _invitation_id):
            error = RuntimeError("authorization failed")
            error.status_code = 403
            raise error

    with pytest.raises(RuntimeError, match="authorization failed"):
        wait(Client(), "JMLR/Paper2/Reviewers/-/Assignment", timeout=0, poll_interval=0)


def test_prepare_marks_an_already_assigned_previous_reviewer():
    helper = load_helper()["prepare_previous_submission_reviewer_redirects"]
    current = submission("current", 2, "https://dev.openreview.net/forum?id=prior")
    invitation = SimpleNamespace(web="var EDGE_BROWSER_PARAMS = 'kept';\n// Go!\nmain();")

    class Client:
        def get_note(self, note_id):
            assert note_id == "prior"
            return submission("prior", 1)

        def get_edges(self, invitation, head, tail=None):
            if head == "prior" and invitation.endswith("/Assignment"):
                return [SimpleNamespace(tail="~Reviewer1", ddate=None)]
            if head == "current" and invitation == "JMLR/Reviewers/-/Assignment":
                return [SimpleNamespace(tail="~Reviewer1", ddate=None)]
            return []

        def get_profile(self, profile_id):
            return SimpleNamespace(content={"names": [{"fullname": "Reviewer"}]})

        def get_invitation(self, invitation_id):
            return invitation

        def get_group(self, group_id):
            return SimpleNamespace(members=["~Editor1"])

        def get_groups(self, prefix):
            return [SimpleNamespace(
                id="JMLR/Paper2/Action_Editor_abcd",
                members=["~Editor1"],
            )]

        def post_invitation_edit(self, **_kwargs):
            return None

    helper(Client(), FakeJournal(), current)
    assert '"id": "~Reviewer1"' in invitation.web
    assert '"assigned": true' in invitation.web


def test_missing_prior_installs_only_the_generic_redirect_launcher():
    helper = load_helper()["prepare_previous_submission_reviewer_redirects"]
    invitation = SimpleNamespace(web="var EDGE_BROWSER_PARAMS = 'kept';\n// Go!\nmain();")
    writes = []
    client = SimpleNamespace(get_invitation=lambda _id: invitation, post_invitation_edit=lambda **kwargs: writes.append(kwargs))
    helper(client, FakeJournal(), submission("current", 2))
    assert len(writes) == 1
    assert '"reviewers": []' in invitation.web
    assert '"previousForumId": null' in invitation.web
    assert "JMLRPreviousReviewerRedirects.install" in invitation.web


def test_valid_prior_without_reviewers_retains_previous_forum_context():
    helper = load_helper()["prepare_previous_submission_reviewer_redirects"]
    invitation = SimpleNamespace(web="var EDGE_BROWSER_PARAMS = 'kept';\n// Go!\nmain();")
    writes = []

    class Client:
        def get_note(self, note_id):
            assert note_id == "prior"
            return submission("prior", 1)

        def get_edges(self, invitation, head):
            assert head == "prior"
            return []

        def get_invitation(self, invitation_id):
            assert invitation_id == "JMLR/Paper2/Reviewers/-/Assignment"
            return invitation

        def post_invitation_edit(self, **kwargs):
            writes.append(kwargs)

    current = submission("current", 2, "https://dev.openreview.net/forum?id=prior")
    helper(Client(), FakeJournal(), current)
    assert len(writes) == 1
    assert '"reviewers": []' in invitation.web
    assert '"previousForumId": "prior"' in invitation.web
    assert "JMLRPreviousReviewerRedirects.install" in invitation.web
