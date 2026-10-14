from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_action_editor_save_waits_for_persisted_eligibility_projection():
    source = (ROOT / "site_config/invitations/venue/manage_action_editors/web/web.js").read_text(encoding="utf-8")
    assert "loadUntilEligibility" in source
    assert "Saved eligibility is not visible yet. Retry Save." in source
    assert "loadUntilEligibility(id, expected, 10)" in source
