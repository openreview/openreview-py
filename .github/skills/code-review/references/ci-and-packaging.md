# CI and Packaging

Most misconfiguration here fails the test run and needs no review comment. Three things do not.

- **Files missing from the wheel.** Tests run from a checkout, so they cannot catch this. A new subpackage directory must be listed in `[tool.setuptools.packages.find] include` in `pyproject.toml`. A new resource directory (`process/`, `webfield/`, data files) needs its own `include` lines in `MANIFEST.in`; the `openreview = ["*"]` package-data pattern matches only files directly under `openreview/`. Either omission imports fine locally and raises on the API servers, which install the released package.
- **New runtime dependencies.** A package added to the dependencies in `pyproject.toml` is installed on the API servers and importable by every process function, so it needs a stated reason. `requirements.txt` is pip-compiled from `pyproject.toml`; dependency changes start there.
- **Workflow triggers.** Production deploy workflows are `workflow_dispatch` only; `deploy-dev.yml` also accepts `repository_dispatch` of type `openreview-py-updated`, which is the supported staging trigger. Flag a new trigger on a production workflow, `pull_request_target`, or PR-controlled data interpolated into a `run:` block.

For context only: CI installs the package on Python 3.9 through 3.13. How tests run in CI is in `tests.md`.
