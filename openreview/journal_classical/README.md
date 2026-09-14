# JMLR OpenReview Configuration

This repository contains the source and reviewable workflow documentation for
JMLR's OpenReview venue configuration.

Contents:

- `site_config/`: OpenReview venue configuration source.
- `docs/roles/`: role-oriented user documentation owned by this public template.
- `docs/reference/`: public style-file and manuscript references.
- `docs/workflow/`: workflow, policy, and contributor documentation.
- `tests/source/`: source-only pytest checks that do not require credentials.

Start with [docs/index.md](docs/index.md). Source changes should keep the
user-facing documentation and OpenReview configuration in sync.

Run the checks before proposing source changes from this directory:

```bash
python3 scripts/check_source_assembly.py
python3 -m pytest -c source_pyproject.toml tests/source
```

The private integration repository owns environment rendering, apply plans,
and checks that require private configuration. Public validation never applies
source to DEV or production.
