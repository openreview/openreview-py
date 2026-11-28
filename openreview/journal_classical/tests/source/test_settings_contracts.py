"""What ``openreview.json`` is allowed to contain.

Tier 1 is where JMLR policy is supposed to live, so the risk here is not a wrong
value but an inert one. A setting journal never reads looks like configuration
and changes nothing, and a setting above a platform limit is worse than
ignored: it is rejected at write time, and the run dies before the work starts.

Both checks are made against ``openreview.journal`` itself rather than a copied
list, so they follow the pinned version instead of drifting from it.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SETTINGS = json.loads((ROOT / "site_config" / "openreview.json").read_text(encoding="utf-8"))
JOURNAL_DIR = ROOT.parent / "journal"

# Journal hard-codes the weight enum on its quota invitations for every venue:
# Custom_Max_Papers 6-15, Local_Custom_Max_Papers 0-15. A larger number is not a
# stricter policy, it is an unusable one -- the edge write is refused with
# "weight must be equal to one of the allowed values" and the batch dies before
# the solver is reached. Dev had drifted to 16 and 20; source never set either.
QUOTA_CEILING = 15
QUOTA_KEYS = ("action_editors_max_papers", "reviewers_max_papers")

# Keys JMLR's own pipeline consumes, which journal has no concept of. The track
# model lives in the top-level `tracks` block.
JMLR_OWNED_SETTINGS = {
    "automatic_decision_approval",
    "automatic_desk_rejection_approval",
}

# Removed by explicit decision. Listed by name because a silent reappearance is
# indistinguishable from a setting that was never dropped.
RETIRED_SETTINGS = {
    "conflict_" + "of_interests": "Journal/OpenReview conflict computation is authoritative",
    "action_editor_new_assignment_cooldown_days": "assignment cooldown removed",
    "reviewer_new_assignment_cooldown_days": "reviewer assignment cooldown removed in favor of Journal policy",
    "assignment_delay": "journal takes this as a setup parameter, not a setting",
    "submission_name": "journal takes this as a constructor parameter, not a setting",
    "publication_mode": "the current Production Editor workflow uses explicit source objects, not this setting",
    "publication_export_enabled": "the current private handoff has no request-setting switch",
    "openreview_publication_enabled": "Journal owns OpenReview publication independently of the JMLR worklist",
    "oss_action_editors_enabled": "managed tracks are registry records, not feature flags",
    "oss_action_editors_max_papers": "all Action Editors use Journal's shared load ceiling",
    "open_source_software": "replaced by the track_id field",
}


def test_production_editor_is_a_handoff_role_not_a_console_mode():
    groups = SETTINGS["defaults"]["role_groups"]
    assert groups["production_editor"] == "JMLR/Production_Editors"
    assert groups["pe"] == groups["production_editor"]


def test_tracks_use_the_shared_labeled_managed_classifier():
    for scope, block in settings_blocks().items():
        tracks = block.get("tracks", {})
        if not tracks:
            continue
        assert tracks["Regular"] == {
            "default": True,
            "eligibility_invitation": "JMLR/Action_Editors/-/Regular_Ineligible",
            "eligibility_mode": "exclude",
        }
        for track_id, spec in block.get("tracks", {}).items():
            if track_id != "Regular":
                assert spec["eligibility_invitation"] == "JMLR/Action_Editors/-/Track_Eligible"
                assert spec["eligibility_mode"] == "include"
            assert spec["eligibility_mode"] == ("exclude" if spec.get("default") else "include")
            assert not ({"eligibility_group", "availability_group", "action_editors_max_papers"} & set(spec))


def settings_blocks() -> dict[str, dict]:
    blocks = {"defaults": SETTINGS.get("defaults", {})}
    for env, override in SETTINGS.get("environments", {}).items():
        blocks[env] = override
    return blocks


def journal_setting_keys() -> set[str]:
    keys: set[str] = set()
    for path in JOURNAL_DIR.rglob("*.py"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        # Journal is not consistent about case: AE_anonymity sits beside
        # number_of_reviewers, so a lowercase-only pattern silently reports a
        # real setting as inert.
        keys.update(re.findall(r"settings\.get\(\s*'([A-Za-z0-9_]+)'", text))
        keys.update(re.findall(r'settings\.get\(\s*"([A-Za-z0-9_]+)"', text))
        keys.update(re.findall(r"settings\[\s*'([A-Za-z0-9_]+)'\s*\]", text))
    return keys


def test_journal_settings_are_discoverable():
    """Guard the guard: if this drops to nothing, the checks below pass vacuously."""
    assert len(journal_setting_keys()) > 30


def test_every_request_form_setting_is_read_by_journal_or_owned_by_jmlr():
    known = journal_setting_keys() | JMLR_OWNED_SETTINGS
    inert = {
        f"{scope}.{key}"
        for scope, block in settings_blocks().items()
        for key in block.get("request_form", {})
        if key not in known
    }
    assert not inert, f"settings nothing reads: {sorted(inert)}"


def test_editor_quotas_fit_the_platform_enum():
    checked = 0
    for scope, block in settings_blocks().items():
        for key in QUOTA_KEYS:
            value = block.get("request_form", {}).get(key)
            if value is None:
                continue
            checked += 1
            assert value <= QUOTA_CEILING, f"{scope}.{key} is {value}, above the enum ceiling {QUOTA_CEILING}"
    assert checked, "no editor quota settings found to check"


def test_jmlr_concurrent_load_defaults_have_one_source_of_truth():
    defaults = SETTINGS["defaults"]["request_form"]
    dev = SETTINGS["environments"]["dev"]["request_form"]

    assert defaults["action_editors_max_papers"] == 9
    assert "action_editors_max_papers" not in dev
    assert defaults["reviewers_max_papers"] == 2
    assert dev["reviewers_max_papers"] == 3


def test_reviewer_assignment_policy_has_no_jmlr_cooldown_setting():
    defaults = SETTINGS["defaults"]
    dev = SETTINGS["environments"]["dev"]
    prod = SETTINGS["environments"]["prod"]

    assert "reviewer_new_assignment_cooldown_days" not in defaults.get("invitations", {})
    assert "reviewer_new_assignment_cooldown_days" not in dev.get("invitations", {})
    retired_fixture = "dev_ignore_" + "openreview_computed_conflicts"
    assert retired_fixture not in defaults["request_form"]
    assert retired_fixture not in dev["request_form"]
    assert retired_fixture not in prod.get("request_form", {})


def test_jmlr_automatic_decision_approval_defaults_to_enabled():
    defaults = SETTINGS["defaults"]["request_form"]

    assert defaults["automatic_decision_approval"] is True


def test_jmlr_automatic_desk_rejection_approval_defaults_to_enabled():
    defaults = SETTINGS["defaults"]["request_form"]

    assert defaults["automatic_desk_rejection_approval"] is True


def test_camera_ready_author_guidelines_url_is_inherited_by_every_environment():
    defaults = SETTINGS["defaults"]["request_form"]["website_urls"]

    assert defaults["camera_ready_author_guidelines"] == (
        "https://www.jmlr.org/format/authors-guide.html"
    )
    for environment in ("dev", "prod"):
        overrides = (
            SETTINGS["environments"][environment]
            .get("request_form", {})
            .get("website_urls", {})
        )
        assert "camera_ready_author_guidelines" not in overrides


def test_lean_journal_request_baseline_stays_explicit():
    settings = SETTINGS["defaults"]["request_form"]

    assert settings["submission_public"] is False
    assert settings["author_anonymity"] is False
    assert settings["AE_anonymity"] is True
    assert settings["submission_license"] == "CC BY-SA 4.0"
    assert settings["number_of_reviewers"] == 3
    assert settings["ae_recommendation_period"] == 1
    assert settings["reviewer_assignment_period"] == 1
    assert settings["review_period"] == 8
    assert settings["discussion_period"] == 2
    assert settings["recommendation_period"] == 2
    assert settings["decision_period"] == 1
    assert settings["camera_ready_period"] == 4
    assert settings["camera_ready_verification_period"] == 1
    assert settings["archived_action_editors"] is True
    assert settings["archived_reviewers"] is True
    assert settings["expert_reviewers"] is True
    assert settings["external_reviewers"] is True
    assert settings["expertise_model"] == "specter+mfr"


def test_retired_settings_stay_retired():
    for scope, block in settings_blocks().items():
        for area in ("request_form", "invitations"):
            for key in block.get(area, {}):
                assert key not in RETIRED_SETTINGS, (
                    f"{scope}.{area}.{key} is back: {RETIRED_SETTINGS.get(key)}"
                )
