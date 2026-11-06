# openreview-py

Python client library and venue-management toolkit for [OpenReview](https://openreview.net), a scientific peer-review platform. Python 3.9+, `requests`, no framework.

This file holds what is true for every file. The review rules for each area of the code are in the `code-review` skill (`.github/skills/code-review/`), each stated once, in the reference for that area.

- **This library writes access control; the API enforces it.** Every `readers`, `nonreaders`, `writers`, `signatures`, `invitees` and `deanonymizers` list built here becomes data the API trusts. A wrong list in a builder or a process function is a leak the server will faithfully enforce.
- **Process functions are server-side code.** Files under any `*/process/` directory are stored on invitations and run by the API with the credentials of the invitation's first signature, usually the venue. They `import openreview` from the package installed on the API server, so a change to `openreview/tools.py` or `openreview/api/client.py` changes what runs with those credentials in production.
- **Anonymity is a readers problem.** Reviewer and area chair identities live in per-paper groups with `anonids: True`, and only a group's `deanonymizers` may see who is behind an anonymous id. The profile id, name or email of an anonymous member must never reach a note, email, bibtex entry, webfield constant or log that anyone else reads.
- **Deployed venues are live data.** Builders run again on redeploy, and process functions read their configuration from the venue group's `content`. Renaming an invitation, a group or a `domain.content` key changes behaviour for venues already running.

## Rules for every file

**Secrets and logs.** Never hardcode tokens, passwords or API keys outside `tests/`; clients take credentials from arguments or the environment. Never `print()` or log a token, an `Authorization` header, a request body or a profile's emails; process-function output is a stored log.

**Code execution.** `exec()` appears only in the super-process wrappers that run a script stored in the venue's meta invitation. Any new `exec()` or `eval()`, and any path where a user-supplied string reaches one, is critical.

**Tests.** Every test is an integration test against the real API servers started by `docker/run.py`. Tests in one file share server state and run in order, so they are run at the file level. Do not suggest mocks or unit tests.

## What not to comment on

- **Formatting and style.** No linter or formatter is configured, and spacing, quote style, import order and line length vary across `master`. Never suggest running a formatter over a glob.
- **Comments.** Builder and process code deliberately carries few comments; do not ask for more. Public methods in `api/client.py` and `tools.py` do carry docstrings, used by the Sphinx docs and the OpenReview internal agent, and a new public method there should too.
- **Test credentials.** `Helpers.strong_password` in `tests/conftest.py` and the `openreview.net` super user login are local-stack fixtures committed on purpose. No production credentials are committed.

The other findings already triaged as false positives are in `.github/skills/code-review/references/known-false-positives.md`.
