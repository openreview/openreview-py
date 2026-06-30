from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from build import site_config_public


def test_jmlr_settings_resolve_from_merged_source_config():
    config = site_config_public.load_source_openreview_config("dev")

    assert site_config_public.public_journal_id("dev", config) == "JMLR"
    assert site_config_public.venue_display_name(config) == "Journal of Machine Learning Research"
    assert site_config_public.venue_short_name(config) == "JMLR"
    assert site_config_public.venue_settings(config) is config["request_form"]
    assert site_config_public.is_submission_public(config) is False
    assert site_config_public.is_action_editor_anonymous(config) is True
    assert site_config_public.has_oss_action_editors(config) is True
    assert site_config_public.publication_mode(config) == "camera_ready_mark_published"
    assert site_config_public.publication_export_enabled(config) is True
    assert site_config_public.openreview_publication_enabled(config) is True

    assert config["request_form"]["action_editors_max_papers"] == 4
    assert config["request_form"]["reviewers_max_papers"] == 3

    replacements = site_config_public.invitation_replacements("dev", config, "JMLR")
    assert replacements["{{VENUE_DISPLAY_NAME_JSON}}"] == '"Journal of Machine Learning Research"'
    assert replacements["{{VENUE_SHORT_NAME_JSON}}"] == '"JMLR"'
    assert replacements["{{AE_ANONYMITY_JSON}}"] == "true"
    assert replacements["{{OSS_ACTION_EDITORS_ENABLED_JSON}}"] == "true"
    assert replacements["{{PUBLICATION_MODE_JSON}}"] == '"camera_ready_mark_published"'
    assert replacements["{{PUBLICATION_EXPORT_ENABLED_JSON}}"] == "true"
    assert replacements["{{OPENREVIEW_PUBLICATION_ENABLED_JSON}}"] == "true"
    assert replacements["{{EXPERTISE_MODEL}}"] == "specter+mfr"
    assert replacements["{{EXPERTISE_MODEL_JSON}}"] == '"specter+mfr"'


def test_journal_style_settings_fallbacks_preserve_existing_config_shape():
    config = {
        "venue_id": "TEST",
        "request_form": {
            "submission_public": False,
        },
        "role_groups": {
            "oss_action_editor": "TEST/OSS_Action_Editors",
        },
    }

    assert site_config_public.venue_display_name(config) == "TEST"
    assert site_config_public.venue_short_name(config) == "TEST"
    assert site_config_public.is_submission_public(config) is False
    assert site_config_public.is_action_editor_anonymous(config) is False
    assert site_config_public.has_oss_action_editors(config) is True
    assert site_config_public.publication_mode(config) == "camera_ready_mark_published"
    assert site_config_public.publication_export_enabled(config) is True
    assert site_config_public.openreview_publication_enabled(config) is True


def test_explicit_feature_settings_override_fallbacks():
    config = {
        "venue_id": "TEST",
        "official_venue_name": "Test Journal",
        "abbreviated_venue_name": "TJ",
        "request_form": {
            "AE_anonymity": True,
            "oss_action_editors_enabled": False,
            "publication_mode": "openreview_only",
            "publication_export_enabled": False,
            "openreview_publication_enabled": True,
        },
        "role_groups": {
            "oss_action_editor": "TEST/OSS_Action_Editors",
        },
    }

    assert site_config_public.venue_display_name(config) == "Test Journal"
    assert site_config_public.venue_short_name(config) == "TJ"
    assert site_config_public.is_action_editor_anonymous(config) is True
    assert site_config_public.has_oss_action_editors(config) is False
    assert site_config_public.publication_mode(config) == "openreview_only"
    assert site_config_public.publication_export_enabled(config) is False
    assert site_config_public.openreview_publication_enabled(config) is True


def test_publication_mode_derives_flags_when_not_explicitly_overridden():
    config = {
        "venue_id": "TEST",
        "request_form": {
            "publication_mode": "journal_export",
        },
    }
    assert site_config_public.publication_export_enabled(config) is True
    assert site_config_public.openreview_publication_enabled(config) is False

    config["request_form"]["publication_mode"] = "openreview_only"
    assert site_config_public.publication_export_enabled(config) is False
    assert site_config_public.openreview_publication_enabled(config) is True


def test_disabled_oss_action_editors_remove_oss_submission_field_from_rendered_config():
    config = site_config_public.load_source_openreview_config("dev")
    config = copy.deepcopy(config)
    config["request_form"]["oss_action_editors_enabled"] = False

    rendered = site_config_public.rendered_openreview_config(config)

    assert site_config_public.has_oss_action_editors(config) is False
    assert "open_source_software" not in rendered["request_form"]["submission_additional_fields"]
    assert "open_source_software" in config["request_form"]["submission_additional_fields"]


def test_disabled_oss_action_editors_remove_oss_submission_field_from_rendered_invitation(tmp_path):
    config = site_config_public.load_source_openreview_config("dev")
    config = copy.deepcopy(config)
    config["request_form"]["oss_action_editors_enabled"] = False
    reply_path = tmp_path / "invitations" / "venue" / "submission" / "edit" / "reply.json"
    reply_path.parent.mkdir(parents=True)
    reply_path.write_text(
        '{"edit": {"note": {"content": {"open_source_software": {"value": true}, "title": {"value": "x"}}}}}\n',
        encoding="utf-8",
    )

    site_config_public.remove_disabled_oss_invitation_fields(tmp_path, config)

    rendered = json.loads(reply_path.read_text(encoding="utf-8"))
    assert "open_source_software" not in rendered["edit"]["note"]["content"]
    assert "title" in rendered["edit"]["note"]["content"]


def test_disabled_oss_action_editors_remove_oss_submission_field_from_top_level_invitation(tmp_path):
    config = site_config_public.load_source_openreview_config("dev")
    config = copy.deepcopy(config)
    config["request_form"]["oss_action_editors_enabled"] = False
    reply_path = tmp_path / "invitations" / "venue" / "submission" / "edit" / "reply.json"
    reply_path.parent.mkdir(parents=True)
    reply_path.write_text(
        '{"note": {"content": {"open_source_software": {"value": true}, "title": {"value": "x"}}}}\n',
        encoding="utf-8",
    )

    site_config_public.remove_disabled_oss_invitation_fields(tmp_path, config)

    rendered = json.loads(reply_path.read_text(encoding="utf-8"))
    assert "open_source_software" not in rendered["note"]["content"]
    assert "title" in rendered["note"]["content"]


def test_disabled_oss_action_editors_do_not_require_oss_max_papers_replacement():
    config = {
        "venue_id": "TEST",
        "site_url": "https://example.test",
        "request_form": {
            "editors_email": "editors@example.test",
            "action_editors_max_papers": 4,
            "reviewers_max_papers": 3,
            "oss_action_editors_enabled": False,
        },
        "invitations": {},
    }

    replacements = site_config_public.invitation_replacements("dev", config, "TEST")

    assert replacements["{{OSS_ACTION_EDITORS_ENABLED_JSON}}"] == "false"
    assert replacements["{{OSS_ACTION_EDITORS_MAX_PAPERS}}"] == "4"


def test_expertise_model_placeholders_are_replaced_in_rendered_sources():
    config = site_config_public.load_source_openreview_config("dev")
    replacements = site_config_public.invitation_replacements("dev", config, "JMLR")

    rendered_assignment = site_config_public.render_global_setting_source(
        "assign_action_editor_webfield.js",
        replacements,
    )
    rendered_overlay = site_config_public.render_python_script(
        "invitations/venue/submission/paper_action_editor_assignment_overlay.py",
        replacements,
    )
    rendered_hub = site_config_public.render_python_script(
        "invitations/venue/under_review/reviewer_assignment_hub.py",
        replacements,
    )

    assert "{{EXPERTISE_MODEL" not in rendered_assignment
    assert "{{EXPERTISE_MODEL" not in rendered_overlay
    assert "{{EXPERTISE_MODEL" not in rendered_hub
    assert 'var EXPERTISE_MODEL = "specter+mfr";' in rendered_assignment


def test_false_mode_replacements_are_rendered_as_json_literals():
    config = site_config_public.load_source_openreview_config("dev")
    config = copy.deepcopy(config)
    config["request_form"].update(
        {
            "AE_anonymity": False,
            "oss_action_editors_enabled": False,
            "publication_export_enabled": False,
            "openreview_publication_enabled": False,
        }
    )

    replacements = site_config_public.invitation_replacements("dev", config, "JMLR")

    assert replacements["{{AE_ANONYMITY_JSON}}"] == "false"
    assert replacements["{{OSS_ACTION_EDITORS_ENABLED_JSON}}"] == "false"
    assert replacements["{{PUBLICATION_EXPORT_ENABLED_JSON}}"] == "false"
    assert replacements["{{OPENREVIEW_PUBLICATION_ENABLED_JSON}}"] == "false"


def test_disabled_oss_action_editors_guard_assignment_setup_source():
    config = site_config_public.load_source_openreview_config("dev")
    config = copy.deepcopy(config)
    config["request_form"]["oss_action_editors_enabled"] = False
    replacements = site_config_public.invitation_replacements("dev", config, "JMLR")

    rendered = site_config_public.render_python_script(
        "invitations/venue/setup_assignments/process_functions/process.py",
        replacements,
    )

    assert 'oss_action_editors_enabled = "false" == "true"' in rendered
    assert "if not oss_action_editors_enabled:" in rendered
    assert "return candidates" in rendered


def test_production_editor_camera_ready_email_uses_configured_publication_instructions():
    config = site_config_public.load_source_openreview_config("dev")
    replacements = site_config_public.invitation_replacements("dev", config, "JMLR")

    template = site_config_public.render_email_template(
        "production_editor/camera_ready_approved.txt",
        replacements,
    )
    rendered_process = site_config_public.render_python_script(
        "invitations/venue/camera_ready_verification/content_process_functions/process.py",
        replacements,
    )

    assert "{publication_processing_instructions}" in template
    assert "def production_editor_camera_ready_instructions():" in rendered_process
    assert "publication_processing_instructions=production_editor_camera_ready_instructions()" in rendered_process


def test_mark_published_makes_openreview_paper_and_public_files_public():
    source = (
        site_config_public.SITE_CONFIG_DIR
        / "invitations"
        / "venue"
        / "mark_camera_ready_published"
        / "content_process_functions"
        / "process.py"
    ).read_text(encoding="utf-8")

    assert "readers=['everyone']" in source
    assert "nonreaders=[]" in source
    assert "odate=now if submission.odate is None else None" in source
    assert "pdate=now if submission.pdate is None else None" in source
    assert "def public_file_content():" in source
    public_file_block = source.split("def public_file_content():", 1)[1].split(
        "if submission.content.get('venueid'", 1
    )[0]
    assert "'pdf': {\n                'readers': {'delete': True}" in source
    assert "content['supplementary_material'] = {\n                'readers': {'delete': True}" in source
    assert "'publication_metadata'" not in public_file_block


def test_invalid_publication_mode_is_rejected():
    config = {
        "venue_id": "TEST",
        "request_form": {
            "publication_mode": "unexpected",
        },
    }

    with pytest.raises(ValueError, match="Unsupported publication_mode"):
        site_config_public.publication_mode(config)


def test_request_form_must_be_an_object():
    with pytest.raises(ValueError, match="request_form must be an object"):
        site_config_public.venue_settings({"request_form": []})
