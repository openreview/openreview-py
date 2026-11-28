"""Unit contracts for JMLR publication metadata projection."""

from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
HELPER = ROOT / "site_config/python_scripts/invitations/venue/publication_metadata.py"
ACCEPTED = ROOT / "site_config/python_scripts/invitations/venue/accepted/postprocess.py"


def load_helper():
    namespace = {}
    exec(compile(HELPER.read_text(encoding="utf-8"), str(HELPER), "exec"), namespace)
    return namespace["build_publication_metadata"]


@pytest.mark.parametrize(
    ("track_id", "expected_special_issue"),
    [
        ("Regular", None),
        ("OSS", "MLOSS"),
        ("Award", None),
        ("Future_Track", None),
    ],
)
@pytest.mark.parametrize("code_url", [None, "https://github.com/example/project"])
def test_projection_preserves_exact_track_and_applies_only_explicit_policy(
    track_id, expected_special_issue, code_url
):
    build = load_helper()
    content = {
        "track_id": {"value": track_id},
        "abstract": {"value": "See https://example.invalid/not-publication-metadata"},
        "cover_letter": {"value": "Repository: https://example.invalid/ignored"},
        "supplementary_material": {"value": "/attachment/ignored.zip"},
    }
    if code_url is not None:
        content["code"] = {"value": code_url}

    result = build(
        {"id": "26-00001", "title": "Paper"},
        content,
        {"OSS": {"special_issue": "MLOSS"}},
    )

    assert result["track_id"] == track_id
    assert result.get("special_issue") == expected_special_issue
    if code_url is None:
        assert "extra_links" not in result
    else:
        assert result["extra_links"] == [["code", code_url]]
    assert "track_name" not in result
    assert "track_url" not in result


def test_projection_owns_reserved_fields_instead_of_trusting_base_metadata():
    build = load_helper()

    result = build(
        {
            "id": "26-00001",
            "track_id": "stale",
            "track_name": "stale",
            "track_url": "https://stale.invalid",
            "special_issue": "stale",
            "extra_links": [["code", "https://stale.invalid"]],
        },
        {"track_id": {"value": "Regular"}},
        {"OSS": {"special_issue": "MLOSS"}},
    )

    assert result == {"id": "26-00001", "track_id": "Regular"}


@pytest.mark.parametrize("track_id", [None, ""])
def test_projection_rejects_a_missing_canonical_track(track_id):
    build = load_helper()
    content = {} if track_id is None else {"track_id": {"value": track_id}}

    with pytest.raises(ValueError, match="canonical track_id"):
        build({}, content, {"OSS": {"special_issue": "MLOSS"}})


def test_accepted_projection_consumes_shared_identity_and_preserves_public_urls():
    source = ACCEPTED.read_text(encoding="utf-8")

    assert "camera_ready_template_fields.py" in source
    assert "template_field_namespace = {}" in source
    assert "camera_ready_fields['camera_ready_accepted_year']" in source
    assert "camera_ready_fields['camera_ready_volume']" in source
    assert "camera_ready_fields['camera_ready_publication_id']" in source
    assert "https://www.jmlr.org/papers/v{volume}/{publication_id}.html" in source
    assert "'pdf': f'https://www.jmlr.org/papers/" not in source
    assert "/papers/volume" not in source
    assert "'year': accepted_year" in source
    assert "'id': publication_id" in source
