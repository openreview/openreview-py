# CI, Deployment and Packaging

## CircleCI (`.circleci/config.yml`)

- `install-package` imports the package on Python 3.9, 3.10, 3.11, 3.12 and 3.13. Syntax or dependency problems on the 3.9 floor surface here, not in the test jobs.
- `build-pr-tests` diffs the PR against `master` for `tests/test_*.py` files added or modified. Zero files: the job skips. One to three files: it runs those files. More than three: it defers. Either way the full `build` job runs afterwards, split across 10 containers by timing. So a library change with no touched test file still gets the full suite, but its first signal arrives an hour later; when a PR changes reader logic or a process function and touches no test file, say so.
- Tests run on Python 3.10 against an openreview-web build and an openreview-api checkout fetched at job time. A test that passes locally against a different API branch can fail in CI; check `ci-utils.sh` for the branch selection when a failure looks environmental.
- `deploy-dev` runs only on `master`.

## GitHub Actions (`.github/workflows/`)

- `deploy-dev.yml`, `deploy-prod.yml`, `deploy-prod-api2.yml` are `workflow_dispatch` only, take a `TAG` input, authenticate to GCP with workload identity (`google-github-actions/auth`, no long-lived keys) and run `bin/deploy-openreview-py.sh <TAG>` on each instance through IAP. They install this package on the API servers, which is how process-function code reaches production.
- `publish-pypi.yml` builds with `setup-python` and publishes with `pypa/gh-action-pypi-publish@release/v1` under a `permissions:` block with `id-token: write` (trusted publishing).
- Flag: a new trigger of `pull_request_target`; PR-controlled values (`github.event.pull_request.title`, branch names) interpolated into `run:`; a new `permissions:` grant beyond what the job needs; a new secret read in a job that runs on PRs; third-party actions not pinned to at least a major version tag. Existing actions are pinned by tag, not SHA — moving to SHAs is a welcome hardening but not a finding against a PR that keeps the current style.

## Packaging (`pyproject.toml`)

- `[tool.setuptools.packages.find] include` is an explicit list. A new subpackage directory (`openreview/<new>/`) that is not added there imports fine from a checkout and is **absent from the wheel**, so the API servers and PyPI users get `ModuleNotFoundError`. Check the list whenever a diff adds a directory with an `__init__.py`.
- `package-data` is `openreview = ["*"]`, so `.py` process files, `.js` webfields and `duplicate_domains.json` ship as long as they live under `openreview/`. Data placed elsewhere does not.
- `version` is bumped in dedicated "increase package version" commits. A PR that adds a helper used by a process function does not take effect on a venue until the servers install a release containing it; a reviewer can ask the PR to note the deployment dependency.
- The version is also enforced by the API. `OpenReviewClient` and `Client` send `User-Agent: openreview-py/<version> (Python/<python>)` from `importlib.metadata`; the API answers 426 `ClientVersionError` when the client is older than its configured minimum. A change that alters the User-Agent format, drops it from a request path (the guest-token path builds its own headers), or sends requests without it breaks that check. A PR that requires users to upgrade should say so, because the minimum is raised on the API side, not here.
- Runtime dependencies are bounded (`>=x,<next-major`). `requirements.txt` is pip-compiled from `pyproject.toml`; a dependency change edits `pyproject.toml` and regenerates, not the other way round. `requirements-dev.txt` holds test and docs pins and is what Dependabot bumps.
- A new runtime dependency is a new import on the API servers. Prefer the standard library; if a package is needed, it has to support 3.9 and be acceptable to install on production hosts.

## Local stack (`docker/`)

`run.py` reads `config.json` for the paths and branches of the sibling repositories, mounts this checkout read-only into the API container, and installs it into a venv there so process functions run the code under review. Changes to `docker-compose.yml`, the entrypoints or `run.py` affect every contributor's test runs; a change that pins a different API or web branch for CI parity should say why.
