"""Linked-resubmission continuity waits for concurrent paper-group setup."""

from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "site_config/python_scripts/invitations/venue/submission/postprocess.py"


class Missing(Exception):
    status_code = 404


class StructuredMissing(Exception):
    def __init__(self):
        super().__init__({"name": "NotFoundError", "message": "hostile", "status": 404})


def load_waiter():
    namespace = {"openreview": SimpleNamespace(OpenReviewException=RuntimeError)}
    exec(compile(SOURCE.read_text(encoding="utf-8"), str(SOURCE), "exec"), namespace)
    return namespace["wait_for_native_groups"]


@pytest.mark.parametrize("missing", [Missing(), StructuredMissing()])
def test_waiter_retries_only_missing_groups_and_shares_one_deadline(monkeypatch, missing):
    calls = []
    remaining = {"authors": 2, "aes": 1}

    def get_group(group_id):
        calls.append(group_id)
        key = group_id.rsplit("/", 1)[-1].lower()
        if remaining[key]:
            remaining[key] -= 1
            raise missing
        return SimpleNamespace(id=group_id)

    monkeypatch.setattr("time.sleep", lambda _seconds: None)
    load_waiter()(SimpleNamespace(get_group=get_group), ["authors", "aes"])
    assert calls == ["authors", "aes", "authors", "aes", "authors"]


def test_waiter_does_not_hide_authorization_or_transport_errors():
    forbidden = Exception({"name": "ForbiddenError", "message": "hostile", "status": 403})
    client = SimpleNamespace(get_group=lambda _id: (_ for _ in ()).throw(forbidden))
    with pytest.raises(Exception) as caught:
        load_waiter()(client, ["authors"])
    assert caught.value is forbidden

    class Transport(Exception):
        pass

    transport = Transport("hostile")
    client = SimpleNamespace(get_group=lambda _id: (_ for _ in ()).throw(transport))
    with pytest.raises(Transport) as caught:
        load_waiter()(client, ["authors"])
    assert caught.value is transport


def test_waiter_has_bounded_generic_timeout(monkeypatch):
    times = iter([0, 0, 2])
    monkeypatch.setattr("time.monotonic", lambda: next(times))
    monkeypatch.setattr("time.sleep", lambda _seconds: None)
    client = SimpleNamespace(get_group=lambda _id: (_ for _ in ()).throw(Missing()))
    with pytest.raises(RuntimeError, match="Linked submission setup did not become ready"):
        load_waiter()(client, ["authors"], timeout=1)


def test_process_waits_for_authors_and_action_editors_before_reader_bridge():
    source = SOURCE.read_text(encoding="utf-8")
    wait = "wait_for_native_groups(client, ("
    bridge = "ensure_previous_submission_access_for_current_ae(client, journal, note)"
    assert source.index(wait) < source.index(bridge)
    block = source[source.index(wait):source.index(bridge)]
    assert "journal.get_authors_id(number=note.number)" in block
    assert "journal.get_action_editors_id(number=note.number)" in block
