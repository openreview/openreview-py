import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SITE_CONFIG = ROOT / "site_config"
DOCS = ROOT / "docs"
ARCHITECTURE = ROOT / "docs/site_config/architecture.md"

CATEGORY = re.compile(r"^\*\*(.+) — ([\d,]+)\*\*$")
ENTRY = re.compile(r"^(.+\.(?:py|js)) — ([\d,]+)$")
FEATURE_ROW = re.compile(r"^\| ([^|*]+) \| ([\d,]+) \|")


def parse_exclusive_manifest():
    text = ARCHITECTURE.read_text(encoding="utf-8")
    manifest = text.split("## Exclusive Path Manifest", 1)[1].split(
        "Reproduce the raw baseline", 1
    )[0]
    categories = {}
    entries = []
    current = None
    in_text_block = False
    for line in manifest.splitlines():
        category = CATEGORY.fullmatch(line)
        if category:
            current = category.group(1)
            categories[current] = {
                "declared": int(category.group(2).replace(",", "")),
                "entries": [],
            }
            continue
        if line == "```text":
            in_text_block = True
            continue
        if line == "```":
            in_text_block = False
            continue
        if in_text_block and line:
            match = ENTRY.fullmatch(line)
            assert match, f"invalid manifest entry: {line!r}"
            assert current is not None
            path = match.group(1)
            count = int(match.group(2).replace(",", ""))
            categories[current]["entries"].append((path, count))
            entries.append((current, path, count))
    return text, categories, entries


def test_exclusive_path_manifest_is_complete_unique_and_current():
    text, categories, entries = parse_exclusive_manifest()
    feature_totals = {
        match.group(1).strip(): int(match.group(2).replace(",", ""))
        for line in text.splitlines()
        if (match := FEATURE_ROW.match(line))
    }

    assert {name: data["declared"] for name, data in categories.items()} == (
        feature_totals
    )
    assert len(entries) == 46
    path_counts = Counter(path for _category, path, _count in entries)
    assert {path: count for path, count in path_counts.items() if count != 1} == {}

    documented = set(path_counts)
    actual = {
        str(path.relative_to(SITE_CONFIG))
        for path in SITE_CONFIG.rglob("*")
        if path.is_file() and path.suffix in {".py", ".js"}
    }
    assert documented == actual

    for category, data in categories.items():
        assert sum(count for _path, count in data["entries"]) == data["declared"]
    assert sum(data["declared"] for data in categories.values()) == 3_537

    for _category, relative, documented_lines in entries:
        path = SITE_CONFIG / relative
        assert path.is_file()
        assert path.resolve().is_relative_to(SITE_CONFIG.resolve())
        assert path.read_bytes().count(b"\n") == documented_lines


def test_architecture_map_keeps_ownership_risk_and_handoff_boundaries_explicit():
    text, _categories, _entries = parse_exclusive_manifest()

    assert "## Ownership Boundary" in text
    assert "normal assignment, conflicts, availability, load limits" in text
    assert "allowing an unavailable or currently track-ineligible previous AE" in text
    assert "JMLR defines no second availability rule" in text
    assert "the final public OpenReview record" in text
    assert "restricted bundle and status note" in text
    assert "cannot change the public final record" in text
    assert "The 168-line reviewer assignment preprocess" in text
    assert "## Validation" in text
    assert "tests/source/test_site_config_architecture_map.py" in text
    assert "46 executable-source files" in text
    assert "unclassified, duplicate, missing, or resized path" in text
    assert "total other than 3,535" in text
    assert "## Resolved Architecture Decisions" in text
    assert "## Unresolved Questions" not in text
    for decision in (
        "Reviewer preprocess size",
        "Review and rejection delegation",
        "Assignment template proxies",
        "Runtime track editing",
        "EIC compatibility landing",
        "Production handoff scope",
    ):
        assert f"| {decision} |" in text
    assert "camera_ready_template_fields.py` owns those deterministic identity fields" in text
    assert "test does not exist" not in text.lower()
    assert "future static checker" not in text.lower()


def test_implementation_layer_name_appears_only_in_the_source_map():
    for path in DOCS.rglob("*.md"):
        if path == ARCHITECTURE:
            continue
        assert not re.search(
            r"\bjournal\b", path.read_text(encoding="utf-8"), re.I
        ), path


def test_reviewer_assignment_ownership_is_not_recast_as_jmlr_policy():
    text, _categories, _entries = parse_exclusive_manifest()

    retired_claim = "JMLR-specific " + bytes.fromhex(
        "68 61 72 64 2d 76 65 72 73 75 73 2d 63 6f 6d 70 75 74 65 64 "
        "63 6f 6e 66 6c 69 63 74 20 74 72 65 61 74 6d 65 6e 74"
    ).decode()
    assert retired_claim not in text
    assert (
        "The preprocess uses Journal's conflict result directly; assignment-edge "
        "normalization remains a compatibility layer pending upstream "
        "characterization."
        in text
    )
    assert (
        "External acceptance and continuity retain their bounded load-only paths; "
        "JMLR defines no conflict taxonomy or general load bypass."
        in text
    )
    assert (
        "Continuity context and email wording plus a checked dedicated assignment "
        "action around the native Edge Browser"
        in text
    )

    for component in (
        "**168-line validator:**",
        "**101-line edge helper:**",
        "**67-line process wrapper:**",
    ):
        assert component in text
    assert "three compatibility surfaces" in text
