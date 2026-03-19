---
name: test-runner
description: "Run pytest tests in the openreview-py repository, including starting the required API servers. Use this skill whenever the user wants to run tests, validate code changes, check if tests pass, start/restart test servers, or mentions a specific test file. Also use when you've just written a significant chunk of code that should be tested. Even if the user just says 'run tests' or 'does this pass?', this skill applies."
---

# Test Runner

Run pytest tests for the openreview-py project. This skill ensures the environment is configured, then delegates to the test-runner agent which handles server startup and test execution in the background.

## Step 1: Load Environment Config

Check if the environment config file exists at `.claude/test-runner-env.json` (relative to the repo root). This file stores the Python environment activation command and API repository paths.

If the file exists, read it and skip to Step 3. It has this structure:
```json
{
  "env_activation": "<shell command to activate the Python environment>",
  "api_v1_path": "/path/to/openreview-api-v1",
  "api_v2_path": "/path/to/openreview-api"
}
```

If the file does not exist, proceed to Step 2.

## Step 2: Set Up Environment (first time only)

Ask the user for three pieces of information:

1. **Python environment activation command** — the shell command to activate a Python environment where openreview-py is installed. Common examples:
   - **virtualenv / venv**: `source /path/to/.venv/bin/activate`
   - **conda**: `conda activate openreview-py`
   - **System Python**: `true` (no-op, if openreview-py is installed globally)

2. **Path to `openreview-api-v1` repository** — this serves API v1 on port 3000.

3. **Path to `openreview-api` repository** — this serves API v2 on port 3001.

**Note for conda users:** If the user provides a bare `conda activate <env>` command, convert it to the inline form before saving:
```
eval "$(conda shell.bash hook 2>/dev/null)" && conda activate <env>
```
Fresh shell sessions (including subagents) don't have conda initialized. The `eval` hook sets up conda so that `conda activate` works. Without this, commands will fail with "conda: command not found" or the environment won't actually activate. This conversion is not needed for virtualenv/venv — `source` works in any shell.

After collecting the info, verify the environment works:
```bash
<env_activation> && python -c "import openreview; print('openreview imported successfully')"
```
If the import fails, tell the user and do not proceed — the correct Python environment is essential because the API servers use PythonShell internally, which relies on the PATH python.

Save the config to `.claude/test-runner-env.json` so this setup only happens once.

## Step 3: Delegate to the test-runner agent

Once the config file exists, launch the **test-runner agent** using the Agent tool. The agent handles everything else autonomously in the background: killing stale server processes, starting API v1 and v2 with `cleanStart`, polling for readiness, and running the requested tests.

Pass the user's test target in the agent prompt. Examples:
- "Run tests in tests/test_client.py"
- "Run test_login_user in tests/test_client.py"
- "Run the full test suite"

If the user just says "run tests" without specifying which, ask them which test file or test to run **before** launching the agent.

Do NOT start servers or run tests in the main conversation — this produces excessive log output and blocks the user. The agent handles it quietly in the background.
