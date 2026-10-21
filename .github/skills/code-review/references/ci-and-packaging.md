# CI and Packaging

Most misconfiguration here fails the test run and needs no review comment. Two things do not, because tests run from a checkout, not from the installed wheel.

- **Files missing from the wheel.** A new subpackage directory must be listed in `[tool.setuptools.packages.find] include` in `pyproject.toml`. A new resource directory (`process/`, `webfield/`, data files) needs its own `include` lines in `MANIFEST.in`; the `openreview = ["*"]` package-data pattern matches only files directly under `openreview/`. Either omission imports fine locally and raises on the API servers, which install the released package.
- **Workflow triggers.** Production deploy workflows are `workflow_dispatch` only; `deploy-dev.yml` also accepts `repository_dispatch` of type `openreview-py-updated`, which is the supported staging trigger. Flag a new trigger on a production workflow, `pull_request_target`, or PR-controlled data interpolated into a `run:` block.

For context only: PR builds run the modified test files first (up to three), then the full suite split across ten containers; the package is installed on Python 3.9 through 3.13 and tests run on 3.10. `requirements.txt` is pip-compiled from `pyproject.toml`, so dependency changes go in `pyproject.toml`.
