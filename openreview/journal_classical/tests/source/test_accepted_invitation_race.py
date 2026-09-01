"""Accepted handoff waits for the native EIC Revision invitation."""

from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "site_config/python_scripts/invitations/venue/accepted/postprocess.py"


class Missing(Exception):
    status_code = 404


class StructuredMissing(Exception):
    def __init__(self):
        super().__init__({"name": "NotFoundError", "message": "hostile", "status": 404})


def load_waiter():
    namespace = {
        "openreview": SimpleNamespace(OpenReviewException=RuntimeError),
    }
    exec(compile(SOURCE.read_text(encoding="utf-8"), str(SOURCE), "exec"), namespace)
    return namespace["wait_for_native_invitation"]


@pytest.mark.parametrize("missing", [Missing(), StructuredMissing()])
def test_waiter_retries_only_not_found_and_returns_native_invitation(monkeypatch, missing):
    expected = object()
    values = iter([missing, missing, expected])
    client = SimpleNamespace(get_invitation=lambda _id: (
        (_ for _ in ()).throw(value) if isinstance((value := next(values)), Exception) else value
    ))
    monkeypatch.setattr("time.sleep", lambda _seconds: None)
    assert load_waiter()(client, "JMLR/Paper1/-/EIC_Revision") is expected


def test_waiter_does_not_hide_transport_or_authorization_errors():
    class Transport(Exception):
        pass
    client = SimpleNamespace(get_invitation=lambda _id: (_ for _ in ()).throw(Transport()))
    with pytest.raises(Transport):
        load_waiter()(client, "JMLR/Paper1/-/EIC_Revision")

    unauthorized = Exception({"name": "ForbiddenError", "message": "hostile", "status": 403})
    client = SimpleNamespace(get_invitation=lambda _id: (_ for _ in ()).throw(unauthorized))
    with pytest.raises(Exception) as caught:
        load_waiter()(client, "JMLR/Paper1/-/EIC_Revision")
    assert caught.value is unauthorized


def test_waiter_has_bounded_generic_timeout(monkeypatch):
    times = iter([0, 0, 2])
    monkeypatch.setattr("time.monotonic", lambda: next(times))
    monkeypatch.setattr("time.sleep", lambda _seconds: None)
    client = SimpleNamespace(get_invitation=lambda _id: (_ for _ in ()).throw(Missing()))
    with pytest.raises(RuntimeError, match="setup did not become ready"):
        load_waiter()(client, "JMLR/Paper1/-/EIC_Revision", timeout=1)
