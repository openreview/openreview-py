"""Camera Ready upload waits for the native Verification invitation."""

from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "site_config/python_scripts/invitations/venue/camera_ready_revision/postprocess.py"


class Missing(Exception):
    status_code = 404


def load_waiter():
    namespace = {"openreview": SimpleNamespace(OpenReviewException=RuntimeError)}
    exec(compile(SOURCE.read_text(encoding="utf-8"), str(SOURCE), "exec"), namespace)
    return namespace["wait_for_native_invitation"]


def test_waiter_retries_only_not_found_and_returns_verification(monkeypatch):
    expected = object()
    values = iter([Missing(), expected])

    def get_invitation(_invitation_id):
        value = next(values)
        if isinstance(value, Exception):
            raise value
        return value

    monkeypatch.setattr("time.sleep", lambda _seconds: None)
    assert load_waiter()(SimpleNamespace(get_invitation=get_invitation), "verification") is expected


def test_waiter_propagates_non_not_found_and_has_bounded_timeout(monkeypatch):
    forbidden = Exception({"name": "ForbiddenError", "status": 403})
    with pytest.raises(Exception) as caught:
        load_waiter()(
            SimpleNamespace(get_invitation=lambda _id: (_ for _ in ()).throw(forbidden)),
            "verification",
        )
    assert caught.value is forbidden

    times = iter([0, 0, 2])
    monkeypatch.setattr("time.monotonic", lambda: next(times))
    monkeypatch.setattr("time.sleep", lambda _seconds: None)
    with pytest.raises(RuntimeError, match="verification setup did not become ready"):
        load_waiter()(
            SimpleNamespace(get_invitation=lambda _id: (_ for _ in ()).throw(Missing())),
            "verification",
            timeout=1,
        )


def test_callback_uses_bounded_wait_instead_of_immediate_optional_lookup():
    source = SOURCE.read_text(encoding="utf-8")
    assert "verification = wait_for_native_invitation(client, verification_id)" in source
    assert "openreview.tools.get_invitation" not in source
