---
name: test-runner
description: "Run pytest tests in the openreview-py repository, including starting the required API servers. Use this skill whenever the user wants to run tests, validate code changes, check if tests pass, start/restart test servers, or mentions a specific test file. Also use when you've just written a significant chunk of code that should be tested. Even if the user just says 'run tests' or 'does this pass?', this skill applies."
---

# Test Runner

Run pytest tests for the openreview-py project using Docker Compose. The `docker/run.py` script manages the full stack (MongoDB, Redis, Elasticsearch, API servers, web frontend) automatically.

## Step 1: Check Prerequisites

1. Verify Docker is available by running `docker info`. If Docker is not running, tell the user to start Docker Desktop or the Docker daemon.

2. Optionally mention that `docker/config.json` can be created from `docker/config.example.json` to customize repo paths, branches, or default mode. This is not required — defaults work if sibling repos are in the standard locations.

## Step 2: Delegate to the test-runner agent

Launch the **test-runner agent** using the Agent tool. Pass the user's test target in the agent prompt. Examples:
- "Run tests in tests/test_client.py"
- "Run test_login_user in tests/test_client.py"
- "Run the full test suite"

If the user just says "run tests" without specifying which, ask them which test file or test to run **before** launching the agent.

Do NOT start servers or run tests in the main conversation — this produces excessive log output and blocks the user. The agent handles it in the background.
