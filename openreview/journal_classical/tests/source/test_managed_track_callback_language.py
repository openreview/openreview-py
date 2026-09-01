from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_manage_tracks_preprocess_starts_with_python_function_token():
    source = (ROOT / "site_config/python_scripts/invitations/venue/tracks/manage_preprocess.py").read_text(encoding="utf-8")
    assert source.startswith("def process(")
