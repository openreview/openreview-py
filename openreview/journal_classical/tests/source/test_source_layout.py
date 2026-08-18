"""The functional boundary of JMLR's lean source tree.

JMLR runs on ``openreview.journal``. The interesting property of this tree is
therefore what it does *not* contain: code belongs here only for a documented
JMLR policy or compatibility gap. Areas are enumerated rather than discovered.

See ``docs/system/integration_design/lean-journal-delta.md``.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE_CONFIG = ROOT / "site_config"
JOURNAL_WEBFIELDS = ROOT.parent / "journal" / "webfield"

# Journal cannot supply these: they are the venue's own settings and wording.
REQUIRED_AREAS = ("openreview.json", "email_templates", "message_templates")

# Code is allowed only where a tier 3 policy lives. Web-fragment JavaScript is
# assembled into one of those process-code owners; message templates remain text.
CODE_AREAS = ("invitations", "python_scripts", "global_settings", "web_fragments")

def source_files() -> list[Path]:
    return sorted(path for path in SITE_CONFIG.rglob("*") if path.is_file())


def test_required_source_areas_exist():
    for area in REQUIRED_AREAS:
        assert (SITE_CONFIG / area).exists(), f"missing required source area: site_config/{area}"


def test_no_file_overrides_a_journal_webfield():
    """The line is override, not JavaScript.

    A JMLR page on a JMLR-owned group is fine: journal never writes it, so it
    cannot drift. A JMLR copy of a webfield
    journal owns is not, because journal's setup rewrites that file -- every
    upgrade either reverts JMLR's version or silently conflicts with it.

    Filename collision is the test because it is what journal's setup keys on.
    """
    journal_owned = {path.name for path in JOURNAL_WEBFIELDS.glob("*.js")}
    assert journal_owned, "could not read journal's webfields; the check would pass vacuously"

    clashes = sorted(
        str(path.relative_to(SITE_CONFIG))
        for path in SITE_CONFIG.rglob("*.js")
        if path.name in journal_owned
    )
    assert not clashes, f"these shadow a journal webfield and will be overwritten on setup: {clashes}"


def test_ui_helpers_never_return():
    """The helper bundle existed only to assemble the console fork.

    Unlike global_settings, this area has no readmission path: each retained
    standalone page owns its small compatibility behavior directly.
    """
    assert not (SITE_CONFIG / "ui_helpers").exists(), "site_config/ui_helpers is back"


def test_message_templates_are_text_and_executable_browser_fragments_are_separate():
    assert not list((SITE_CONFIG / "message_templates").rglob("*.js"))
    fragments = sorted(
        str(path.relative_to(SITE_CONFIG / "web_fragments"))
        for path in (SITE_CONFIG / "web_fragments").rglob("*.js")
    )
    assert fragments == ["assignment_launchers/previous_reviewer_redirects.js"]


def test_code_lives_only_in_a_tier_three_area_and_names_its_reason():
    """Every code file must say which journal behaviour it cannot use.

    This is the rule that keeps the delta small, and it is enforced here rather
    than trusted, because the failure mode is gradual: one reasonable-looking
    file at a time, each individually defensible.
    """
    for path in source_files():
        if path.suffix not in {".py", ".js"}:
            continue
        relative = path.relative_to(SITE_CONFIG)
        assert relative.parts[0] in CODE_AREAS, (
            f"{relative} is code outside a tier 3 area {CODE_AREAS}"
        )
        head = "\n".join(path.read_text(encoding="utf-8").splitlines()[:40]).lower()
        assert "journal" in head, (
            f"{relative} carries no recorded reason naming the journal behaviour it cannot use"
        )
