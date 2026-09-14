"""The JMLR approval adapter waits for Camera Ready invitation setup."""

from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "site_config/python_scripts/invitations/venue/decision/camera_ready_guidance.py"


class Missing(Exception):
    status_code = 404


class StructuredMissing(Exception):
    def __init__(self):
        super().__init__({"name": "NotFoundError", "message": "hostile", "status": 404})


def load_waiter():
    namespace = {"openreview": SimpleNamespace(OpenReviewException=RuntimeError)}
    exec(compile(SOURCE.read_text(encoding="utf-8"), str(SOURCE), "exec"), namespace)
    return namespace["wait_for_native_invitation"]


@pytest.mark.parametrize("missing", [Missing(), StructuredMissing()])
def test_waiter_retries_only_not_found_and_returns_camera_invitation(monkeypatch, missing):
    expected = object()
    values = iter([missing, missing, expected])

    def get_invitation(_invitation_id):
        value = next(values)
        if isinstance(value, Exception):
            raise value
        return value

    monkeypatch.setattr("time.sleep", lambda _seconds: None)
    assert load_waiter()(SimpleNamespace(get_invitation=get_invitation), "camera") is expected


def test_waiter_does_not_hide_authorization_or_transport_errors():
    forbidden = Exception({"name": "ForbiddenError", "message": "hostile", "status": 403})
    client = SimpleNamespace(get_invitation=lambda _id: (_ for _ in ()).throw(forbidden))
    with pytest.raises(Exception) as caught:
        load_waiter()(client, "camera")
    assert caught.value is forbidden

    class Transport(Exception):
        pass

    transport = Transport("hostile")
    client = SimpleNamespace(get_invitation=lambda _id: (_ for _ in ()).throw(transport))
    with pytest.raises(Transport) as caught:
        load_waiter()(client, "camera")
    assert caught.value is transport


def test_waiter_has_bounded_generic_timeout(monkeypatch):
    times = iter([0, 0, 2])
    monkeypatch.setattr("time.monotonic", lambda: next(times))
    monkeypatch.setattr("time.sleep", lambda _seconds: None)
    client = SimpleNamespace(get_invitation=lambda _id: (_ for _ in ()).throw(Missing()))
    with pytest.raises(RuntimeError, match="Camera-ready JMLR setup did not become ready"):
        load_waiter()(client, "camera", timeout=1)


def test_guidance_waits_instead_of_silently_returning_when_invitation_is_late():
    source = SOURCE.read_text(encoding="utf-8")
    assert "revision = wait_for_native_invitation(" in source
    assert "if not revision:" not in source
    assert "Camera-ready JMLR guidance readback failed." in source
