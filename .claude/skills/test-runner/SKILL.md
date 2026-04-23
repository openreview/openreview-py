---
name: test-runner
description: "Run pytest tests in the openreview-py repository, including starting the required API servers. Use this skill whenever the user wants to run tests, validate code changes, check if tests pass, start/restart test servers, start services for browser testing, open an interactive shell, or mentions a specific test file. Also use when you've just written a significant chunk of code that should be tested. Even if the user just says 'run tests' or 'does this pass?', this skill applies."
---

# Test Runner

Run pytest tests and manage the development stack for the openreview-py project using Docker Compose. The `docker/run.py` script manages the full stack (MongoDB, Redis, Elasticsearch, API servers, web frontend) automatically.

## Step 1: Check Prerequisites

Verify Docker is available by running `docker info`. If Docker is not running, tell the user to start Docker Desktop or the Docker daemon.

## Step 2: Determine what the user needs

Based on the user's request, determine the appropriate `run.py` command. The script supports these modes and options:

### Modes

**Test mode** (default) — Run tests then tear down:
```bash
cd <project_root>/docker && python3 run.py <pytest_args>
```
- `python3 run.py tests/test_client.py` — run a specific test file
- `python3 run.py tests/test_client.py::TestClient::test_get_groups` — run a specific test
- `python3 run.py` — run all tests (warn: takes a long time)

**Serve mode** — Start services for manual browser testing:
```bash
cd <project_root>/docker && python3 run.py --serve
cd <project_root>/docker && python3 run.py --serve tests/test_icml_conference.py
cd <project_root>/docker && python3 run.py --serve --shell
cd <project_root>/docker && python3 run.py --serve --shell tests/test_icml_conference.py
```
The `--shell` flag can be combined with `--serve` to get an interactive shell while services are running with ports exposed. Useful for running scripts/tests interactively while browsing `localhost:3030`.

**Shell mode** — Interactive shell in a container:
```bash
cd <project_root>/docker && python3 run.py --shell          # test container (Python + pytest)
cd <project_root>/docker && python3 run.py --shell api-v1   # API v1 container
cd <project_root>/docker && python3 run.py --shell api-v2   # API v2 container
cd <project_root>/docker && python3 run.py --shell web      # web container
```

### Options (can be combined with any mode)

- `--no-clean` — Preserve existing database (skip API server restart/cleanStart)
- `--keep-infra` — Keep infrastructure (mongo, redis, ES, web) running after tests finish
- `--branch-api-v1 <branch>` — Checkout a specific branch in the api-v1 repo before starting
- `--branch-api-v2 <branch>` — Checkout a specific branch in the api-v2 repo before starting
- `--branch-web <branch>` — Checkout a specific branch in the web repo before starting
- `--no-checkout` — Skip auto-checkout even if config enables it

### Configuration

Users can create `docker/config.json` (from `docker/config.example.json`) to set default repo paths, branches, mode, and `keep_infra`. CLI flags override config settings.

## Step 3: Delegate to the test-runner agent

Launch the **test-runner agent** using the Agent tool. In the prompt, include the **exact command** to run based on Step 2.

If the user just says "run tests" without specifying which, ask them which test file or test to run **before** launching the agent.

Do NOT start servers or run tests in the main conversation — this produces excessive log output and blocks the user. The agent handles it in the background.
