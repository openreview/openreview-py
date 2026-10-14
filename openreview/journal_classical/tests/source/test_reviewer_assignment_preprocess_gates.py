import datetime
import json
import re
from pathlib import Path
from types import SimpleNamespace

import pytest


SITE = Path(__file__).resolve().parents[2] / "site_config"
PUBLIC_ROOT = SITE.parent
PREPROCESS = SITE / "invitations/reviewers/assignment/process_functions/preprocess.py"
NOW = 2_000_000_000_000


class AssignmentError(RuntimeError):
    pass


class Profile:
    def __init__(self, profile_id, emails=()):
        self.id = profile_id
        self.content = {
            "preferredEmail": emails[0] if emails else None,
            "emails": list(emails),
            "preferredEmails": list(emails),
        }

    def get_preferred_email(self):
        return self.content["preferredEmail"]


class Assignment:
    def __init__(self):
        self.conflicts = set()
        self.failures = set()
        self.calls = []

    def compute_conflicts(self, _submission, profile_id):
        self.calls.append(profile_id)
        if profile_id in self.failures:
            raise RuntimeError("unsafe conflict service detail")
        return ["computed"] if profile_id in self.conflicts else []


class Journal:
    venue_id = "JMLR"
    under_review_venue_id = "JMLR/Under_Review"

    def __init__(self):
        self.assignment = Assignment()
        self.reviewers_max_papers = 3

    def get_authors_id(self, number):
        return f"JMLR/Paper{number}/Authors"

    def get_ae_decision_id(self, number):
        return f"JMLR/Paper{number}/-/Decision"

    def get_review_id(self, number):
        return f"JMLR/Paper{number}/-/Review"

    def get_reviewers_id(self, number=None, anon=False):
        if number is None:
            return "JMLR/Reviewers"
        suffix = "/Reviewer_.*" if anon else ""
        return f"JMLR/Paper{number}/Reviewers{suffix}"

    def get_reviewer_assignment_id(self, number=None, archived=False):
        if number is not None:
            return f"JMLR/Paper{number}/Reviewers/-/Assignment"
        if archived:
            return "JMLR/Reviewers/-/Archived_Assignment"
        return "JMLR/Reviewers/-/Assignment"

    def get_reviewer_availability_id(self):
        return "JMLR/Reviewers/-/Assignment_Availability"

    def get_reviewer_pending_review_id(self):
        return "JMLR/Reviewers/-/Pending_Reviews"

    def get_reviewer_invite_assignment_id(self):
        return "JMLR/Reviewers/-/Invite_Assignment"

    def get_ae_conflict_id(self):
        return "JMLR/Action_Editors/-/Conflict"

    def get_reviewer_conflict_id(self):
        return "JMLR/Reviewers/-/Conflict"

    def get_author_submission_id(self):
        return "JMLR/-/Submission"

    def get_reviewers_max_papers(self):
        return self.reviewers_max_papers


def note(note_id="current", number=2):
    return SimpleNamespace(
        id=note_id,
        number=number,
        domain="JMLR",
        invitations=["JMLR/-/Submission"],
        content={
            "venueid": {"value": "JMLR/Under_Review"},
            "authorids": {"value": ["~Author"]},
            "author_list": {"value": ""},
        },
    )


class Client:
    def __init__(self, journal):
        self.journal = journal
        self.current = note()
        self.previous = note("previous", 1)
        self.profiles = {
            "~Editor": Profile("~Editor", ["editor@example.com"]),
            "~AuthorEditor": Profile("~AuthorEditor", ["author@example.com"]),
        }
        self.base_reviewers = {"~Reviewer1"}
        self.active_invitation = True
        self.decision = False
        self.existing_assignment = False
        self.availability_edge = None
        self.external_acceptance = False
        self.pending = 0
        self.custom_max = None
        self.recent_assignments = []
        self.prior_active = False
        self.prior_archived = False
        self.reviews = []
        self.removal_groups = []

    def get_note(self, note_id):
        if note_id == self.current.id:
            return self.current
        if note_id == self.previous.id:
            return self.previous
        for assignment in self.recent_assignments:
            if assignment.head == note_id:
                return note(note_id, getattr(assignment, "paper_number", 9))
        raise RuntimeError(f"missing note {note_id}")

    def get_notes(self, invitation, **_kwargs):
        if invitation == self.journal.get_ae_decision_id(self.current.number):
            return [SimpleNamespace(ddate=None)] if self.decision else []
        if invitation == self.journal.get_review_id(self.current.number):
            return self.reviews
        return []

    def get_groups(self, id=None, member=None, prefix=None, signatory=None, **_kwargs):
        if id == self.journal.get_reviewers_id():
            return [SimpleNamespace()] if member in self.base_reviewers else []
        if prefix is not None and signatory is not None:
            return self.removal_groups
        return []

    def get_edges(self, invitation=None, head=None, tail=None, **_kwargs):
        if invitation in {self.journal.get_ae_conflict_id(), self.journal.get_reviewer_conflict_id()}:
            return []
        if invitation == self.journal.get_reviewer_availability_id():
            return [self.availability_edge] if self.availability_edge else []
        if invitation == self.journal.get_reviewer_pending_review_id():
            return [SimpleNamespace(weight=self.pending)] if self.pending else []
        if invitation == f"{self.journal.get_reviewers_id()}/-/Custom_Max_Papers":
            return [SimpleNamespace(weight=self.custom_max)] if self.custom_max is not None else []
        if invitation == self.journal.get_reviewer_invite_assignment_id():
            return [SimpleNamespace(ddate=None, label="Accepted")] if self.external_acceptance else []
        if invitation == self.journal.get_reviewer_assignment_id(number=self.current.number):
            if head == self.current.id and tail == "~Reviewer1" and self.existing_assignment:
                return [self.assignment_edge(head=self.current.id)]
            return []
        if invitation == self.journal.get_reviewer_assignment_id():
            if head == self.previous.id and tail in (None, "~Reviewer1") and self.prior_active:
                return [self.assignment_edge(head=self.previous.id)]
            if head == self.current.id and tail == "~Reviewer1" and self.existing_assignment:
                return [self.assignment_edge(head=self.current.id)]
            return []
        if invitation == self.journal.get_reviewer_assignment_id(archived=True):
            if head == self.previous.id and tail in (None, "~Reviewer1") and self.prior_archived:
                return [self.assignment_edge(head=self.previous.id, archived=True)]
            return []
        raise AssertionError((invitation, head, tail))

    def get_all_edges(self, domain=None, tail=None):
        assert domain == "JMLR"
        return [edge for edge in self.recent_assignments if edge.tail == tail]

    def assignment_edge(self, head, archived=False, cdate=NOW - 1_000, paper_number=9):
        return SimpleNamespace(
            id=f"edge-{head}-{archived}",
            invitation=self.journal.get_reviewer_assignment_id(archived=archived),
            head=head,
            tail="~Reviewer1",
            ddate=None,
            cdate=cdate,
            paper_number=paper_number,
        )


def _script(path):
    return (SITE / "python_scripts" / path).read_text(encoding="utf-8")


def render_preprocess():
    source = PREPROCESS.read_text(encoding="utf-8")

    def replace_json(match):
        return json.dumps(_script(match.group(1).strip()))

    source = re.sub(r'"?\{\{PYTHON_SCRIPT_JSON:([^}]+)\}\}"?', replace_json, source)
    source = re.sub(
        r"^\s*#?\s*\{\{PYTHON_SCRIPT_FILE:([^}]+)\}\}\s*$",
        lambda match: _script(match.group(1).strip()),
        source,
        flags=re.MULTILINE,
    )
    replacements = {"{{PROD_JOURNAL_ID}}": "JMLR"}
    for old, new in replacements.items():
        source = source.replace(old, new)
    return source


def test_preprocess_starts_with_the_python_entry_point():
    assert PREPROCESS.read_text(encoding="utf-8").startswith(
        "def process(client, edge, invitation):"
    )


@pytest.fixture
def harness():
    journal = Journal()
    client = Client(journal)
    openreview = SimpleNamespace(
        OpenReviewException=AssignmentError,
        journal=SimpleNamespace(
            JournalRequest=SimpleNamespace(get_journal=lambda _client, _venue: journal)
        ),
        tools=SimpleNamespace(
            get_profiles=lambda _client, values: [client.profiles[value] for value in values if value in client.profiles],
            get_invitation=lambda _client, _invitation: SimpleNamespace() if client.active_invitation else None,
            datetime_millis=lambda _value: NOW,
        ),
    )
    namespace = {"openreview": openreview, "datetime": datetime}
    exec(compile(render_preprocess(), str(PREPROCESS), "exec"), namespace)
    edge = SimpleNamespace(
        invitation=journal.get_reviewer_assignment_id(),
        head=client.current.id,
        tail="~Reviewer1",
        tauthor="~Editor",
        signatures=["~Editor"],
        label=None,
        ddate=None,
    )
    return SimpleNamespace(process=namespace["process"], client=client, journal=journal, edge=edge)


def call(harness):
    return harness.process(harness.client, harness.edge, SimpleNamespace(id=harness.edge.invitation))


def rejects(harness, message):
    with pytest.raises(AssignmentError, match=message):
        call(harness)


def test_rejects_wrong_or_inactive_paper_invitation(harness):
    harness.edge.invitation = harness.journal.get_reviewer_assignment_id(number=2)
    rejects(harness, "use JMLR/Reviewers/-/Assignment")
    harness.edge.invitation = harness.journal.get_reviewer_assignment_id()
    harness.client.active_invitation = False
    rejects(harness, "invitation is not active")


def test_rejects_terminal_decision_and_duplicate_assignment(harness):
    harness.client.decision = True
    rejects(harness, "decision has already been posted")
    harness.client.decision = False
    harness.client.existing_assignment = True
    rejects(harness, "already assigned")


@pytest.mark.parametrize("identity_source", ["tauthor", "signature", "profile_email"])
def test_nonempty_journal_conflict_blocks_every_actor_identity(harness, identity_source):
    if identity_source == "tauthor":
        harness.journal.assignment.conflicts.add("~Editor")
    elif identity_source == "signature":
        harness.edge.tauthor = "JMLR/Action_Editors"
        harness.journal.assignment.conflicts.add("~Editor")
    else:
        harness.journal.assignment.conflicts.add("editor@example.com")
    rejects(harness, "Conflicted users can not edit assignments")


def test_actor_conflict_computation_failure_blocks_assignment(harness):
    harness.journal.assignment.failures.add("~Editor")
    rejects(harness, "Can not verify assignment conflicts")


def test_candidate_journal_conflict_blocks_regardless_of_edge_label(harness):
    harness.journal.assignment.conflicts.add("~Reviewer1")
    for label in (None, "Unexpected Override", "Resubmission continuity"):
        harness.edge.label = label
        rejects(harness, "conflict detected")


def test_candidate_conflict_computation_failure_blocks_assignment(harness):
    harness.journal.assignment.failures.add("~Reviewer1")
    rejects(harness, "Can not verify assignment conflicts")


def test_empty_journal_conflict_results_permit_assignment_subject_to_other_gates(harness):
    call(harness)
    assert "~Editor" in harness.journal.assignment.calls
    assert "~Reviewer1" in harness.journal.assignment.calls


def test_external_acceptance_bypasses_load_but_not_conflict(harness):
    harness.edge.signatures = ["JMLR"]
    harness.edge.label = "External Reviewer Acceptance"
    harness.client.pending = 99
    call(harness)
    harness.journal.assignment.conflicts.add("~Reviewer1")
    rejects(harness, "conflict detected")


def test_membership_and_timed_availability_are_non_bypassable(harness):
    harness.client.base_reviewers.clear()
    rejects(harness, "not a member of JMLR/Reviewers")
    harness.client.base_reviewers.add("~Reviewer1")
    harness.client.availability_edge = SimpleNamespace(label="Unavailable", weight=NOW + 86_400_000)
    rejects(harness, "unavailable until")
    harness.client.availability_edge = SimpleNamespace(label="Unavailable", weight=NOW - 1)
    call(harness)


def test_recent_assignment_does_not_create_a_jmlr_cooldown(harness):
    recent = harness.client.assignment_edge("recent", cdate=NOW - 1_000, paper_number=9)
    harness.client.recent_assignments = [recent]
    call(harness)
    harness.client.current.content["previous_JMLR_submission_url"] = {
        "value": "https://dev.openreview.net/forum?id=previous"
    }
    harness.client.prior_archived = True
    call(harness)


def test_default_and_custom_max_load_block_normal_reviewer(harness):
    harness.client.pending = harness.journal.reviewers_max_papers
    rejects(harness, "maximum active paper load of 3")
    harness.client.pending = 2
    harness.client.custom_max = 2
    rejects(harness, "maximum active paper load of 2")


@pytest.mark.parametrize("archived", [False, True])
def test_prior_reviewer_bypasses_only_configured_load(harness, archived):
    harness.client.current.content["previous_JMLR_submission_url"] = {
        "value": "https://openreview.net/forum?mode=edit&id=previous"
    }
    harness.client.prior_active = not archived
    harness.client.prior_archived = archived
    harness.client.pending = 99
    harness.client.custom_max = 1
    call(harness)

    harness.client.base_reviewers.clear()
    rejects(harness, "not a member")
    harness.client.base_reviewers.add("~Reviewer1")
    harness.client.availability_edge = SimpleNamespace(label="Unavailable", weight=NOW + 1)
    rejects(harness, "unavailable until")
    harness.client.availability_edge = None
    harness.journal.assignment.conflicts.add("~Reviewer1")
    rejects(harness, "conflict detected")


@pytest.mark.parametrize(
    ("gate", "message"),
    [
        ("wrong_state", "Can not edit assignments"),
        ("wrong_invitation", "use JMLR/Reviewers/-/Assignment"),
        ("inactive_invitation", "invitation is not active"),
        ("decision", "decision has already been posted"),
        ("duplicate", "already assigned"),
        ("actor_conflict", "Conflicted users can not edit assignments"),
        ("candidate_conflict", "conflict detected"),
        ("membership", "not a member"),
        ("availability", "unavailable until"),
    ],
)
def test_prior_reviewer_cannot_bypass_non_load_gates(harness, gate, message):
    harness.client.current.content["previous_JMLR_submission_url"] = {
        "value": "https://dev.openreview.net/forum?id=previous"
    }
    harness.client.prior_archived = True
    harness.client.pending = 99

    if gate == "wrong_state":
        harness.client.current.content["venueid"] = {"value": "JMLR/Accepted"}
    elif gate == "wrong_invitation":
        harness.edge.invitation = harness.journal.get_reviewer_assignment_id(number=2)
    elif gate == "inactive_invitation":
        harness.client.active_invitation = False
    elif gate == "decision":
        harness.client.decision = True
    elif gate == "duplicate":
        harness.client.existing_assignment = True
    elif gate == "actor_conflict":
        harness.journal.assignment.conflicts.add("~Editor")
    elif gate == "candidate_conflict":
        harness.journal.assignment.conflicts.add("~Reviewer1")
    elif gate == "membership":
        harness.client.base_reviewers.clear()
    elif gate == "availability":
        harness.client.availability_edge = SimpleNamespace(
            label="Unavailable", weight=NOW + 1
        )
    else:
        raise AssertionError(gate)

    rejects(harness, message)


def test_remove_rejects_after_decision_or_submitted_review(harness):
    harness.edge.ddate = NOW
    harness.client.decision = True
    rejects(harness, "decision has already been posted")
    harness.client.decision = False
    harness.client.removal_groups = [SimpleNamespace(id="JMLR/Paper2/Reviewers/Reviewer_1")]
    harness.client.reviews = [SimpleNamespace(signatures=["JMLR/Paper2/Reviewers/Reviewer_1"])]
    rejects(harness, "already posted a review")


def test_retired_local_assignment_policy_stays_absent_from_public_text():
    retired_recruitment_word = bytes.fromhex("76 6f 6c 75 6e 74 65 65 72").decode()
    retired_terms = {
        "hard" + "_conflict",
        "hard" + " conflict",
        "author-" + "declared conflict",
        "conflict_" + "of_interests",
        "openreview conflict " + "override",
        "dev_ignore_" + "openreview_computed_conflicts",
        "solicit_" + "reviewers",
        "solicit " + "reviewers",
        "reviewer " + retired_recruitment_word,
        retired_recruitment_word + " reviewer",
        "self-service " + "reviewer recruitment",
    }
    hits = {}
    for source_root in (PUBLIC_ROOT / "docs", SITE, PUBLIC_ROOT / "tests"):
        for path in source_root.rglob("*"):
            if not path.is_file() or path.suffix not in {
                ".py",
                ".js",
                ".json",
                ".md",
                ".txt",
                ".html",
            }:
                continue
            if any(part in {"__pycache__", ".pytest_cache", "generated"} for part in path.parts):
                continue
            content = path.read_text(encoding="utf-8").lower()
            matched = sorted(term for term in retired_terms if term in content)
            if matched:
                hits[str(path.relative_to(PUBLIC_ROOT))] = matched
    assert hits == {}


def test_preprocess_contains_no_raw_email_address():
    source = PREPROCESS.read_text(encoding="utf-8")
    assert re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", source) is None
