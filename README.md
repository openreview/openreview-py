OpenReview Python library
=========================

[![CircleCI](https://circleci.com/gh/openreview/openreview-py.svg?style=svg)](https://circleci.com/gh/openreview/openreview-py)
[![Documentation Status](https://readthedocs.org/projects/openreview-py/badge/?version=latest)](https://openreview-py.readthedocs.io/en/latest/?badge=latest)
[![CodeCov](https://codecov.io/gh/openreview/openreview-py/branch/master/graph/badge.svg)](https://codecov.io/gh/openreview/openreview-py)

Prerequisites
-------------

Python 3.9 or newer is required to use openreview-py.

Installation
------------

There are two ways to install the OpenReview python library.

Using `pip`:

```bash
pip install openreview-py
```

From the repository:

```bash
git clone https://github.com/openreview/openreview-py.git
cd openreview-py
pip install -e .
```

> Note: Depending on your Python installation you may need to use the command  `pip3` instead of `pip`.

### Production / CI Installation

For reproducible deployments, install the package using the pinned lock file as constraints:

```bash
pip install -c requirements.txt .
```

For development (editable install with pinned dependencies):

```bash
pip install -c requirements.txt -e .
```

### Updating Dependencies

This project uses [pip-tools](https://pip-tools.readthedocs.io/) to manage dependency versions. `pyproject.toml` declares compatible version ranges, while `requirements.txt` (production) and `requirements-dev.txt` (test + docs) contain the exact pinned versions.

To update all dependencies to the latest compatible versions:

```bash
pip-compile pyproject.toml -o requirements.txt --strip-extras
pip-compile pyproject.toml --extra test --extra docs -o requirements-dev.txt --strip-extras
```

To update a single package:

```bash
pip-compile --upgrade-package requests pyproject.toml -o requirements.txt --strip-extras
```

> **Note:** `pip-compile` resolves for the Python version of the running interpreter, so the numpy pin in the generated lock files will only match that version. After running `pip-compile`, manually replace the numpy line in both lock files with environment-marked entries:
> ```
> numpy==2.0.2 ; python_version < '3.10'
> numpy==2.2.6 ; python_version == '3.10'
> numpy==2.4.3 ; python_version >= '3.11'
> ```

Usage
-----

The openreview-py library can be used to easily access and modify any data stored in the OpenReview system.

For more information, see [the official reference](https://openreview-py.readthedocs.io/en/latest/).
You can also check the [OpenReview docs](https://docs.openreview.net/getting-started/using-the-api/installing-and-instantiating-the-python-client) for examples and How-To Guides

Run Tests with Docker (Recommended)
------------------------------------

The easiest way to run the integration tests is with Docker Compose. This requires [Docker](https://docs.docker.com/get-docker/) and that the following sibling repositories are cloned next to `openreview-py`:

```bash
├── openreview-api        # https://github.com/openreview/openreview-api
├── openreview-api-v1     # https://github.com/openreview/openreview-api-v1
├── openreview-web        # https://github.com/openreview/openreview-web
└── openreview-py         # this repo
```

Set up your config file, then run tests:

```bash
cd docker
cp config.example.json config.json
# Edit config.json with your repo paths (required before first run)

# Run a specific test file (services start, tests run, then everything tears down)
./run.py tests/test_client.py

# Run a specific test with verbose output
./run.py tests/test_client.py::TestClient::test_get_groups -v

# Run all tests (takes a long time)
./run.py
```

Each test run starts infrastructure (MongoDB, Redis, Elasticsearch, web), restarts API servers with a clean database via `npm run cleanStart`, runs the tests, and **tears down all services** when done. All services share a network namespace so `localhost` works everywhere, reusing the same `circleci.json` configs used in CI.

### Serve Mode (Manual Browser Testing)

Start all services with ports exposed to your host machine for manual browser testing:

```bash
# Start services only (browse http://localhost:3030)
./run.py --serve

# Populate the database by running a test, then keep services running
./run.py --serve tests/test_icml_conference.py

# Preserve existing data across restarts (skip cleanStart)
./run.py --serve --no-clean
```

Press `Ctrl+C` to stop. If `keep_infra` is enabled, only API servers are stopped and infrastructure stays running. Otherwise, all services are torn down. You can also run `docker compose down` from another terminal to stop everything.

Combine with `--shell` to get an interactive shell while services are running:

```bash
# Serve with shell access (browse + run scripts/tests)
./run.py --serve --shell

# Populate DB, then drop into shell for manual testing
./run.py --serve --shell tests/test_icml_conference.py
```

### Interactive Shell

Drop into a container shell for debugging or manual pytest runs:

```bash
# Shell in the test container (Python + pytest)
./run.py --shell

# Shell into a specific service
./run.py --shell api-v2
```

### Branch Selection

Use specific branches for sibling repos:

```bash
# Override branches via CLI
./run.py --branch-api-v2 feature/new-endpoint tests/test_client.py

# Or configure defaults in docker/config.json (copy from config.example.json)
cp config.example.json config.json
# Edit config.json with your paths and branches
```

### Other Options

```bash
# Start infrastructure without running tests or exposing ports
./run.py --setup-only

# Skip cleanStart to preserve existing database (works with any mode)
./run.py --no-clean tests/test_client.py
./run.py --serve --no-clean

# Keep infrastructure (mongo, redis, ES, web) running after tests finish
./run.py --keep-infra tests/test_client.py
```

### Configuration

Copy `docker/config.example.json` to `docker/config.json` before your first run. The config file is required and gitignored.

```json
{
  "api_v1": { "path": "../../openreview-api-v1", "branch": "main" },
  "api_v2": { "path": "../../openreview-api",    "branch": "feature/x" },
  "web":    { "path": "../../openreview-web",     "branch": "" },
  "mode": "test",
  "auto_checkout": true,
  "keep_infra": false
}
```

- **path**: Relative to `docker/` or absolute. Defaults to sibling directories.
- **branch**: Branch to auto-checkout before starting. Empty means use whatever is checked out.
- **mode**: Default mode (`test`, `serve`). CLI flags override this.
- **auto_checkout**: Set to `false` to disable auto-checkout. `--no-checkout` also disables it.
- **keep_infra**: Set to `true` to keep infrastructure (mongo, redis, ES, web) running after tests. API servers are always torn down in test mode. `--keep-infra` also enables it.

### Cleanup

```bash
# Remove containers (keep volumes for faster next run)
docker compose down

# Full clean (remove volumes too)
docker compose down -v
```

> Note: The first run takes several minutes to pull images and install dependencies. Subsequent runs are much faster thanks to cached named volumes for `node_modules` and Python virtual environments.

Run Tests Locally
-----------------

To run tests without Docker, you need to manually start the required services.

### Test Setup

The OpenReview API V1, OpenReview API V2, and OpenReview Web frontend must be cloned and configured to run on ports 3000, 3001, and 3030 respectively. For more information on how to install and configure those services see the README for each project:

- [OpenReview API V1](https://github.com/openreview/openreview-api-v1)
- [OpenReview API V2](https://github.com/openreview/openreview-api)
- [OpenReview Web](https://github.com/openreview/openreview-web)

Install the package with test dependencies:

```bash
pip install -e ".[test]"
```

Download the proper Firefox Selenium driver for your OS [from GitHub](https://github.com/mozilla/geckodriver/releases), and place the `geckodriver` executable in the directory `openreview-py/tests/drivers`. When you are done your folder structure should look like this:

```bash
├── openreview-py
│   ├── tests
│   │   ├── data
│   │   ├── drivers
│   │   │    └── geckodriver
```

### Running Tests

Start both OpenReview API versions and the web frontend:

Inside the OpenReview API V1 directory
```bash
npm run cleanStart
```

Inside the OpenReview API V2 directory
```bash
npm run cleanStart
```

Inside the OpenReview Web directory
```bash
SUPER_USER=openreview.net npm run dev
```

Once all three services are running, start the tests:
```bash
pytest
```

> Note: If you have previously set environment variables with your OpenReview credentials, make sure to clear them before running the tests: `unset OPENREVIEW_USERNAME && unset OPENREVIEW_PASSWORD`

To run a single set of tests from a file, you can include the file name as an argument. For example:

```bash
pytest tests/test_client.py
```
