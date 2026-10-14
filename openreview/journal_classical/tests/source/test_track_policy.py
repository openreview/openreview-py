"""Focused contracts for JMLR's track-policy adapter over Journal."""

import json
import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "site_config"


def source(relative: str) -> str:
    return (SITE / relative).read_text(encoding="utf-8")


def document(relative: str):
    return json.loads(source(relative))


def load_process(relative: str):
    namespace = {"openreview": SimpleNamespace(OpenReviewException=OpenReviewException)}
    exec(compile(source(relative), relative, "exec"), namespace)
    return namespace["process"]


def load_registry():
    namespace = {"openreview": SimpleNamespace(OpenReviewException=OpenReviewException)}
    exec(
        compile(source("python_scripts/invitations/venue/tracks/registry.py"), "track_registry.py", "exec"),
        namespace,
    )
    return namespace


def test_track_configuration_has_one_base_role_and_one_shared_managed_classifier():
    settings = document("openreview.json")["defaults"]
    tracks = settings["tracks"]

    assert tracks["Regular"] == {
        "default": True,
        "eligibility_invitation": "JMLR/Action_Editors/-/Regular_Ineligible",
        "eligibility_mode": "exclude",
    }
    assert {spec["eligibility_invitation"] for key, spec in tracks.items() if key != "Regular"} == {
        "JMLR/Action_Editors/-/Track_Eligible"
    }
    assert all(spec["eligibility_mode"] == "include" for key, spec in tracks.items() if key != "Regular")
    assert not any("eligibility_group" in spec or "availability_group" in spec for spec in tracks.values())
    assert not ({"oss_action_editor", "award_action_editor"} & set(settings["role_groups"]))


def test_only_dev_conflict_fixture_is_retained_outside_journal_settings():
    settings = document("openreview.json")
    defaults = settings["defaults"]
    dev = settings["environments"]["dev"]

    assert "invitations" not in defaults
    assert "invitations" not in dev
    retired_fixture = "dev_ignore_" + "openreview_computed_conflicts"
    assert retired_fixture not in dev["request_form"]
    assert "new_assignment_cooldown_days" not in json.dumps(settings)


def test_registry_is_public_ordered_and_only_refreshes_submission_choices_and_timer():
    registry_group = document("global_settings/groups/tracks.json")
    registry = source("python_scripts/invitations/venue/tracks/registry.py")

    assert registry_group["id"] == "JMLR/Tracks"
    assert registry_group["readers"] == ["everyone"]
    records = json.loads(registry_group["content"]["tracks"]["value"])
    assert [record["id"] for record in records] == ["Award", "OSS"]
    assert "Regular is permanent and is not a managed track" in registry
    assert "Tracks cannot be deleted; set an ending date instead" in registry
    assert "open_track_ids" in registry
    assert "future_boundaries" in registry
    assert "matching_track_ids" not in registry
    assert "slug_from_name" not in registry
    assert "Assignment_Availability" not in registry
    assert "get_ae_assignment_id" not in registry


def test_registry_executes_stable_schema_and_no_deletion_policy():
    registry = load_registry()
    valid = [{"id": "OSS", "name": "Open Source Software", "beginning_date": None, "ending_date": None}]

    assert registry["validate_track_records"](valid) == valid
    with pytest.raises(OpenReviewException, match="cannot be deleted"):
        registry["validate_track_records"]([], previous=valid)
    for broken, message in (
        ([{"id": "Regular", "name": "Other"}], "not a managed track"),
        ([{"id": "bad-id", "name": "Bad"}], "Invalid track identifier"),
        ([{"id": "OSS", "name": ""}], "requires a display name"),
        ([{"id": "OSS", "name": "One"}, {"id": "OSS", "name": "Two"}], "Duplicate"),
    ):
        with pytest.raises(OpenReviewException, match=message):
            registry["validate_track_records"](broken)


def test_registry_executes_aoe_inclusive_dates_and_future_boundaries():
    registry = load_registry()
    record = {"id": "OSS", "name": "OSS", "beginning_date": "2026-08-14", "ending_date": "2026-08-14"}
    start = registry["aoe_boundary_millis"]("2026-08-14")
    after_end = registry["aoe_boundary_millis"]("2026-08-14", end=True)

    assert registry["track_is_open"](record, start)
    assert registry["track_is_open"](record, after_end - 1)
    assert not registry["track_is_open"](record, start - 1)
    assert not registry["track_is_open"](record, after_end)
    assert registry["future_boundaries"]([record], start - 1) == [start, after_end]


def test_eligibility_edges_are_labeled_public_classifiers_with_private_expired_history():
    cases = {
        "regular_ineligible": {"const": "Regular Ineligible"},
        "track_eligible": {"regex": "^[A-Za-z][A-Za-z0-9_]{0,63}$"},
    }
    for directory, label_param in cases.items():
        base = f"invitations/action_editors/{directory}"
        invitation = document(f"{base}/invitation/invitation.json")
        edge = document(f"{base}/edge/edge.json")
        preprocess = source(f"{base}/process_functions/preprocess.py")

        assert invitation["readers"] == ["everyone"]
        assert edge["head"]["param"]["const"] == "JMLR/Action_Editors"
        assert edge["tail"]["param"]["type"] == "profile"
        assert edge["label"]["param"] == label_param
        assert "if not edge.ddate and edge.tail not in" in preprocess
        assert "['JMLR/Editors_In_Chief', edge.tail] if edge.ddate else ['everyone']" in preprocess


def run_eligibility_preprocess(directory, *, active=True, expired=False, readers=None, label="OSS"):
    process = load_process(f"invitations/action_editors/{directory}/process_functions/preprocess.py")

    class Client:
        def get_group(self, group_id):
            if group_id == "JMLR/Tracks":
                return SimpleNamespace(content={"tracks": {"value": '[{"id":"OSS"}]'}})
            return SimpleNamespace(members=["~AE1"] if active else [])

    process(
        Client(),
        SimpleNamespace(
            tail="~AE1", ddate=123 if expired else None,
            readers=readers if readers is not None else (["JMLR/Editors_In_Chief", "~AE1"] if expired else ["everyone"]),
            label="Regular Ineligible" if directory == "regular_ineligible" else label,
        ),
        SimpleNamespace(),
    )


def test_eligibility_preprocess_executes_membership_label_and_reader_rules():
    run_eligibility_preprocess("regular_ineligible")
    run_eligibility_preprocess("track_eligible")
    run_eligibility_preprocess("track_eligible", active=False, expired=True)
    with pytest.raises(OpenReviewException, match="current Action Editor membership"):
        run_eligibility_preprocess("track_eligible", active=False)
    with pytest.raises(OpenReviewException, match="Unknown managed JMLR track"):
        run_eligibility_preprocess("track_eligible", label="Unknown")
    with pytest.raises(OpenReviewException, match="readers must be"):
        run_eligibility_preprocess("regular_ineligible", expired=True, readers=["everyone"])


class OpenReviewException(Exception):
    pass


def run_assignment_adapter(*, track="Regular", conflict=False, previous=False,
                           unavailable=False, eligible=True, base_member=True,
                           actor_author=False, active=True, native_bound=False):
    adapter = source("invitations/action_editors/assignment/process_functions/preprocess.py")
    adapter = adapter.replace(
        "# {{PYTHON_SCRIPT_FILE:invitations/venue/ae_assignment_continuity.py}}",
        source("python_scripts/invitations/venue/ae_assignment_continuity.py"),
    )
    adapter = adapter.replace(
        "from openreview.journal.process import ae_assignment_pre_process as journal_preprocess",
        "journal_preprocess = openreview.journal.process.ae_assignment_pre_process",
    )
    assignment_ids = {
        False: "JMLR/Action_Editors/-/Assignment",
        True: "JMLR/Action_Editors/-/Assignment_Archived",
    }
    journal = SimpleNamespace(
        assignment=SimpleNamespace(
            compute_conflicts=lambda note, tail: ["conflict"] if conflict else []
        ),
        get_authors_id=lambda number: f"JMLR/Paper{number}/Authors",
        is_active_submission=lambda note: active,
        get_action_editors_id=lambda: "JMLR/Action_Editors",
        get_ae_assignment_id=lambda archived=False: assignment_ids[archived],
        get_ae_availability_id=lambda: "JMLR/Action_Editors/-/Assignment_Availability",
    )
    previous_url = "https://openreview.net/forum?id=previous" if previous else None
    submission = SimpleNamespace(
        number=7,
        content={
            "track_id": {"value": track},
            **({"previous_JMLR_submission_url": {"value": previous_url}} if previous else {}),
        },
    )

    class Client:
        def get_note(self, note_id):
            return submission

        def get_groups(self, **kwargs):
            return [SimpleNamespace(id=kwargs.get("id"))] if actor_author else []

        def get_group(self, group_id):
            if group_id == "JMLR/Tracks":
                return SimpleNamespace(content={"tracks": {"value": '[{"id":"OSS"}]'}})
            return SimpleNamespace(members=["~AE1"] if base_member else [])

        def get_edges(self, invitation, **kwargs):
            if kwargs.get("head") == "previous" and invitation in assignment_ids.values():
                return [SimpleNamespace()] if previous and invitation == assignment_ids[False] else []
            if invitation == journal.get_ae_availability_id():
                return [SimpleNamespace(label="Unavailable")] if unavailable else []
            if invitation == "JMLR/Action_Editors/-/Regular_Ineligible":
                return [] if eligible else [SimpleNamespace()]
            if invitation == "JMLR/Action_Editors/-/Track_Eligible":
                return [SimpleNamespace()] if eligible else []
            return []

    native_module = SimpleNamespace()
    original_native_openreview = SimpleNamespace(marker="original-native")
    if native_bound:
        native_module.openreview = original_native_openreview
    calls = []

    def native_process(client, edge, invitation):
        calls.append("native")
        assert native_module.openreview is openreview_namespace
        assert native_module.openreview.journal.Journal() is journal
        if conflict:
            raise OpenReviewException(f"Conflict detected for {edge.tail}.")
        if client.get_edges(invitation=journal.get_ae_availability_id(), tail=edge.tail):
            raise OpenReviewException(
                f"Action Editor {edge.tail} is currently unavailable."
            )

    original_journal_factory = lambda: SimpleNamespace(marker="original")
    native_module.process = native_process
    openreview_namespace = SimpleNamespace(
        OpenReviewException=OpenReviewException,
        journal=SimpleNamespace(
            Journal=original_journal_factory,
            JournalRequest=SimpleNamespace(get_journal=lambda client, venue_id: journal),
            process=SimpleNamespace(ae_assignment_pre_process=native_module),
        ),
    )
    namespace = {"openreview": openreview_namespace}
    exec(compile(adapter, "assignment_preprocess.py", "exec"), namespace)
    try:
        namespace["process"](
            Client(),
            SimpleNamespace(head="new", tail="~AE1", tauthor="~EIC", ddate=None),
            SimpleNamespace(),
        )
    finally:
        assert openreview_namespace.journal.Journal is original_journal_factory
        if native_bound:
            assert native_module.openreview is original_native_openreview
        else:
            assert not hasattr(native_module, "openreview")
    return calls


def test_assignment_proceeds_from_native_availability_to_track_gate():
    with pytest.raises(OpenReviewException, match="not eligible for OSS"):
        run_assignment_adapter(track="OSS", eligible=False)


def test_ordinary_assignment_delegates_conflict_and_availability_to_journal():
    with pytest.raises(OpenReviewException, match="Conflict detected"):
        run_assignment_adapter(conflict=True)
    with pytest.raises(OpenReviewException, match="currently unavailable"):
        run_assignment_adapter(unavailable=True)
    assert run_assignment_adapter() == ["native"]
    assert run_assignment_adapter(native_bound=True) == ["native"]


def test_prior_ae_continuity_bypasses_availability_and_track_but_not_conflict():
    assert run_assignment_adapter(
        track="OSS", previous=True, unavailable=True, eligible=False
    ) == []
    with pytest.raises(OpenReviewException, match="Conflict detected"):
        run_assignment_adapter(
            track="OSS", previous=True, conflict=True,
            unavailable=True, eligible=False,
        )
    with pytest.raises(OpenReviewException, match="not a current Action Editor"):
        run_assignment_adapter(previous=True, base_member=False)
    with pytest.raises(OpenReviewException, match="Authors cannot edit"):
        run_assignment_adapter(previous=True, actor_author=True)
    with pytest.raises(OpenReviewException, match="active submission"):
        run_assignment_adapter(previous=True, active=False)


def test_assignment_adapter_delegates_ordinary_gates_then_applies_track_policy():
    adapter = source("invitations/action_editors/assignment/process_functions/preprocess.py")
    continuity = adapter.index("continuity = not edge.ddate")
    native = adapter.index("journal_preprocess.process")
    eligibility = adapter.index("Regular_Ineligible")
    assert continuity < native < eligibility
    assert adapter.count("journal_preprocess.process") == 1
    assert "openreview.journal.Journal = lambda: journal" in adapter
    assert "journal_preprocess.openreview = openreview" in adapter
    assert "del journal_preprocess.openreview" in adapter
    assert "finally:" in adapter
    assert "/Action_Editors/-/Track_Eligible" in adapter
    assert "get_ae_max_papers" not in adapter
    assert "get_ae_custom_max_papers_id" not in adapter


def test_assignment_preprocess_is_python_first_token_and_has_no_javascript_twin():
    relative = "invitations/action_editors/assignment/process_functions/preprocess.py"
    adapter = source(relative)
    compile(adapter.replace(
        "# {{PYTHON_SCRIPT_FILE:invitations/venue/ae_assignment_continuity.py}}", ""
    ), relative, "exec")
    assert adapter.startswith("def process(client, edge, invitation):")
    assert not (SITE / "invitations/action_editors/assignment/process_functions/preprocess.js").exists()


def test_recommendation_adapter_preserves_journal_availability_gate():
    adapter = source("invitations/action_editors/recommendation/process_functions/preprocess.py")

    assert "only collected for Regular submissions" in adapter
    assert "not collected for resubmissions" in adapter
    assert "Regular_Ineligible" in adapter
    assert "get_ae_availability_id" in adapter
    assert "get_ae_max_papers" not in adapter
    assert "get_ae_custom_max_papers_id" not in adapter


def run_recommendation_adapter(*, track="Regular", resubmission=False, ineligible=False,
                               unavailable=False):
    journal = SimpleNamespace(
        get_ae_availability_id=lambda: "availability",
    )

    class Client:
        def get_note(self, note_id):
            content = {"track_id": {"value": track}}
            if resubmission:
                content["previous_JMLR_submission_url"] = {"value": "https://openreview.net/forum?id=old"}
            return SimpleNamespace(content=content)

        def get_edges(self, invitation, **kwargs):
            if invitation == "JMLR/Action_Editors/-/Regular_Ineligible":
                return [SimpleNamespace()] if ineligible else []
            if invitation == "availability":
                return [SimpleNamespace(label="Unavailable")] if unavailable else []
            return []

    namespace = {
        "openreview": SimpleNamespace(
            OpenReviewException=OpenReviewException,
            journal=SimpleNamespace(JournalRequest=SimpleNamespace(get_journal=lambda client, venue_id: journal)),
        )
    }
    relative = "invitations/action_editors/recommendation/process_functions/preprocess.py"
    exec(compile(source(relative), relative, "exec"), namespace)
    namespace["process"](Client(), SimpleNamespace(ddate=None, head="paper", tail="~AE1"), SimpleNamespace())


def test_recommendation_preprocess_executes_journal_and_jmlr_gates():
    run_recommendation_adapter()
    with pytest.raises(OpenReviewException, match="only collected for Regular"):
        run_recommendation_adapter(track="OSS")
    with pytest.raises(OpenReviewException, match="not collected for resubmissions"):
        run_recommendation_adapter(resubmission=True)
    with pytest.raises(OpenReviewException, match="currently unavailable"):
        run_recommendation_adapter(unavailable=True)


def test_submission_track_is_required_and_immutable():
    field = document("openreview.json")["defaults"]["request_form"]["submission_additional_fields"]["track_id"]
    callback = document("invitations/venue/submission/invitation/invitation.json")
    preprocess = source("python_scripts/invitations/venue/submission/preprocess.py")

    assert field["value"]["param"] == {
        "type": "string",
        "input": "select",
        "enum": ["Regular", "OSS", "Award"],
        "default": "Regular",
        "optional": False,
    }
    assert callback["preprocess"] == "{{PYTHON_SCRIPT_JSON:invitations/venue/submission/preprocess.py}}"
    assert "Track is immutable after submission" in preprocess
    assert "Track {requested} is not open for new submissions" in preprocess
    assert "Resubmission track must match the previous paper" in preprocess


def run_submission_preprocess(*, requested, existing=None, beginning=None, ending=None):
    process = load_process("python_scripts/invitations/venue/submission/preprocess.py")
    note = SimpleNamespace(id="paper" if existing is not None else None, content={"track_id": {"value": requested}})

    class Client:
        def get_note(self, note_id):
            return SimpleNamespace(content={"track_id": {"value": existing}})

        def get_group(self, group_id):
            records = [{"id": "OSS", "name": "OSS", "beginning_date": beginning, "ending_date": ending}]
            return SimpleNamespace(content={"tracks": {"value": json.dumps(records)}})

    process(Client(), SimpleNamespace(note=note), SimpleNamespace())


def test_submission_preprocess_executes_immutability_closed_track_and_aoe_boundary():
    with pytest.raises(OpenReviewException, match="immutable"):
        run_submission_preprocess(requested="OSS", existing="Regular")

    aoe = datetime.timezone(datetime.timedelta(hours=-12))
    today = datetime.datetime.now(aoe).date()
    with pytest.raises(OpenReviewException, match="not open"):
        run_submission_preprocess(requested="OSS", ending=(today - datetime.timedelta(days=1)).isoformat())
    with pytest.raises(OpenReviewException, match="not open"):
        run_submission_preprocess(requested="OSS", beginning=(today + datetime.timedelta(days=1)).isoformat())

    # Both boundaries are inclusive in the author-facing AoE calendar.
    run_submission_preprocess(requested="OSS", beginning=today.isoformat(), ending=today.isoformat())


def test_no_parallel_track_role_or_availability_source_exists():
    paths = {path.relative_to(SITE).as_posix().lower() for path in SITE.rglob("*") if path.is_file()}

    assert not any("oss_action_editors" in path or "award_action_editors" in path for path in paths)
    assert not any("track_availability" in path for path in paths)
