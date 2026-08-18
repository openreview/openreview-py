"""Rendered assignment wrappers select wording and delegate mechanics to Journal."""

from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "site_config"


class OpenReviewException(Exception):
    pass


def render_process(role: str) -> str:
    path = SITE / "invitations" / role / "assignment" / "process_functions" / "process.py"
    rendered = path.read_text(encoding="utf-8").replace("{{PROD_JOURNAL_ID}}", "JMLR")
    includes = {
        "action_editors": [
            "python_scripts/invitations/venue/ae_assignment_continuity.py",
            "python_scripts/invitations/venue/previous_submission_ae_reader_bridge.py",
        ],
        "reviewers": [
            "python_scripts/invitations/venue/under_review/previous_submission_reviewer_policy.py"
        ],
    }
    for include in includes[role]:
        rendered = rendered.replace(
            f"# {{{{PYTHON_SCRIPT_FILE:{include.removeprefix('python_scripts/')}}}}}",
            (SITE / include).read_text(encoding="utf-8"),
        )
    template_role = "ae" if role == "action_editors" else "reviewer"
    for kind in ("initial", "continuity"):
        marker = f'"{{{{EMAIL_TEMPLATE_JSON:{template_role}/assignment_{kind}.txt}}}}"'
        template = (SITE / "email_templates" / template_role / f"assignment_{kind}.txt").read_text(
            encoding="utf-8"
        )
        rendered = rendered.replace(marker, json.dumps(template))
    assert "{{EMAIL_TEMPLATE_JSON:" not in rendered
    assert "{{PYTHON_SCRIPT_FILE:" not in rendered
    return rendered


class Journal:
    venue_id = "JMLR"

    def get_action_editors_id(self, number=None):
        return "JMLR/Action_Editors" if number is None else f"JMLR/Paper{number}/Action_Editors"

    def get_ae_assignment_id(self, archived=False):
        return f"JMLR/Action_Editors/-/{'Archived_' if archived else ''}Assignment"

    def get_reviewers_id(self):
        return "JMLR/Reviewers"

    def get_reviewer_assignment_id(self, archived=False):
        return f"JMLR/Reviewers/-/{'Archived_' if archived else ''}Assignment"

    def get_author_submission_id(self):
        return "JMLR/-/Submission"

    def get_review_id(self, number):
        return f"JMLR/Paper{number}/-/Review"

    def get_ae_decision_id(self, number):
        return f"JMLR/Paper{number}/-/Decision"

    def get_meta_invitation_id(self):
        return "JMLR/-/Edit"


class Client:
    def __init__(self, role: str, continuity: bool):
        self.role = role
        self.continuity = continuity
        content = {"title": {"value": "Current"}}
        if continuity:
            content["previous_JMLR_submission_url"] = {
                "value": "https://openreview.net/forum?id=previous"
            }
        self.submission = SimpleNamespace(id="current", number=2, content=content)
        self.previous = SimpleNamespace(
            id="previous",
            number=1,
            domain="JMLR",
            invitations=["JMLR/-/Submission"],
            content={"title": {"value": "Previous"}},
            readers=["everyone"],
        )

    def get_note(self, note_id):
        return self.previous if note_id == "previous" else self.submission

    def get_edges(self, invitation, head=None, tail=None, **kwargs):
        if not self.continuity or head != "previous":
            return []
        expected = "JMLR/Action_Editors/-/Assignment" if self.role == "action_editors" else "JMLR/Reviewers/-/Assignment"
        if invitation != expected:
            return []
        assigned_tail = tail or ("~ActionEditor1" if self.role == "action_editors" else "~Reviewer1")
        return [SimpleNamespace(tail=assigned_tail, ddate=None)]

    def get_group(self, group_id, *args, **kwargs):
        return SimpleNamespace(
            id=group_id,
            members=[],
            content={"assignment_email_template_script": {"value": "Journal default"}},
        )

    def get_notes(self, **_kwargs):
        return []

    def post_note_edit(self, **_kwargs):
        raise AssertionError("the fixture has no prior reviews to repair")


def execute_selector(monkeypatch, role: str, continuity: bool, *, fail=False):
    selected = []
    calls = {}
    journal = Journal()
    root_module = ModuleType("openreview")
    root_module.OpenReviewException = OpenReviewException
    journal_module = ModuleType("openreview.journal")
    process_package = ModuleType("openreview.journal.process")
    process_module = ModuleType(
        "openreview.journal.process.ae_assignment_process"
        if role == "action_editors"
        else "openreview.journal.process.reviewer_assignment_process"
    )

    def journal_process_update(client, edge, invitation, existing_edge):
        resolved_journal = journal_module.Journal()
        group_id = journal.get_action_editors_id() if role == "action_editors" else journal.get_reviewers_id()
        selected.append(client.get_group(group_id).content["assignment_email_template_script"]["value"])
        calls.update(
            count=calls.get("count", 0) + 1,
            resolved_journal=resolved_journal,
            edge=edge,
            invitation=invitation,
            existing_edge=existing_edge,
        )
        if fail:
            raise RuntimeError("upstream assignment failed")
        return "journal-result"

    process_module.process_update = journal_process_update
    journal_module.JournalRequest = SimpleNamespace(get_journal=lambda client, venue_id: journal)
    original_journal_factory = lambda: (_ for _ in ()).throw(
        AssertionError("the wrapper must supply the resolved journal")
    )
    journal_module.Journal = original_journal_factory
    journal_module.process = process_package
    root_module.journal = journal_module
    module_name = "ae_assignment_process" if role == "action_editors" else "reviewer_assignment_process"
    setattr(process_package, module_name, process_module)
    monkeypatch.setitem(sys.modules, "openreview", root_module)
    monkeypatch.setitem(sys.modules, "openreview.journal", journal_module)
    monkeypatch.setitem(sys.modules, "openreview.journal.process", process_package)
    monkeypatch.setitem(sys.modules, process_module.__name__, process_module)

    namespace = {"openreview": root_module}
    exec(compile(render_process(role), f"{role}_assignment_process.py", "exec"), namespace)
    client = Client(role, continuity)
    tail = "~ActionEditor1" if role == "action_editors" else "~Reviewer1"
    edge = SimpleNamespace(head="current", tail=tail, ddate=None)
    invitation = SimpleNamespace(id="assignment")
    existing_edge = SimpleNamespace(id="old")
    try:
        result = namespace["process_update"](client, edge, invitation, existing_edge)
    except Exception as error:
        result = error
    assert calls == {
        "count": 1,
        "resolved_journal": journal,
        "edge": edge,
        "invitation": invitation,
        "existing_edge": existing_edge,
    }
    assert journal_module.Journal is original_journal_factory
    return result, selected[0], process_module


@pytest.mark.parametrize("role,template_role", (("action_editors", "ae"), ("reviewers", "reviewer")))
@pytest.mark.parametrize("continuity,kind", ((False, "initial"), (True, "continuity")))
def test_rendered_wrapper_selects_expected_template_and_delegates(monkeypatch, role, template_role, continuity, kind):
    result, selected, journal_process = execute_selector(monkeypatch, role, continuity)
    expected = (SITE / "email_templates" / template_role / f"assignment_{kind}.txt").read_text(encoding="utf-8")
    assert result == "journal-result"
    assert selected == expected
    assert journal_process.openreview is sys.modules["openreview"]
    assert journal_process.datetime is datetime


def test_ae_wrapper_bounds_upstream_failure_and_restores_factory(monkeypatch):
    result, selected, _journal_process = execute_selector(
        monkeypatch, "action_editors", False, fail=True
    )

    assert isinstance(result, OpenReviewException)
    assert str(result) == "Action Editor assignment process failed."
    assert selected


def test_all_assignment_templates_format_with_journal_fields():
    fields = {
        "short_name": "JMLR", "submission_number": 2, "submission_title": "Example",
        "invitation_url": "https://openreview.net/forum?id=current", "contact_info": "editors@example.org",
        "number_of_reviewers": 3, "review_period_length": 8, "review_duedate": "Oct 9",
        "submission_length": "", "ack_invitation_url": "https://openreview.net/forum?id=current&invitationId=ack",
        "reviewers_max_papers": 2, "venue_id": "JMLR", "review_visibility": "visible to all reviewers",
        "website": "https://jmlr.org", "assigned_action_editor": "Action Editor",
    }
    for path in sorted((SITE / "email_templates").glob("*/assignment_*.txt")):
        rendered = path.read_text(encoding="utf-8").format(**fields)
        assert "{{fullname}}" in rendered
        assert "Example" in rendered


def test_ae_assignment_templates_direct_editor_to_review_approval():
    for kind in ("initial", "continuity"):
        template = (
            SITE / "email_templates" / "ae" / f"assignment_{kind}.txt"
        ).read_text(encoding="utf-8")
        assert "Review Approval" in template
        assert '"Appropriate for Review"' in template
        assert '"Desk Reject"' in template
        assert "normal Decision form" not in template


def test_wrappers_do_not_copy_journal_assignment_state_machine():
    for role in ("action_editors", "reviewers"):
        source = (SITE / "invitations" / role / "assignment" / "process_functions" / "process.py").read_text()
        assert "journal_process.process_update" in source
        for mutation in ("add_members_to_group", "remove_members_from_group", "post_note_edit", "post_message"):
            assert mutation not in source


def test_assignment_dateprocesses_start_with_the_python_entry_point():
    for role in ("action_editors", "reviewers"):
        source = (
            SITE
            / "invitations"
            / role
            / "assignment"
            / "process_functions"
            / "process.py"
        ).read_text(encoding="utf-8")
        assert source.startswith(
            "def process_update(client, edge, invitation, existing_edge):"
        )
