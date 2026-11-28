from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

def test_role_management_handles_not_found_and_retryable_errors():
    source=(ROOT/'site_config/invitations/venue/role_management/web/web.js').read_text(encoding='utf-8')
    assert "status === 404" in source
    assert "request.fail(function (error)" in source
    assert "request.responseJSON" in source
    assert "request.status" in source
    assert "/not found/i.test(message)" in source
    assert "No venue-level JMLR memberships found." in source
    assert "Enter a valid OpenReview profile ID." in source
    assert "Profile not found or membership lookup failed. Retry Search." in source
    assert "}).catch(" not in source
