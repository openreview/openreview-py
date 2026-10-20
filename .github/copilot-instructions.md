# openreview-py

Python client library and venue-management toolkit for [OpenReview](https://openreview.net), a scientific peer-review platform. Python 3.9+, `requests`, no framework.

The permission model as this library authors it, the process-function execution model, per-directory review rules, and the findings already triaged as false positives are in the `code-review` skill (`.github/skills/code-review/`). This file holds only what is true everywhere.

- **This library writes access control; the API enforces it.** Every `readers`, `nonreaders`, `writers`, `signatures`, `invitees` and `deanonymizers` list built here becomes data the API trusts. A wrong list in an invitation builder or a process function is a leak the server will faithfully enforce.
- **Process functions are server-side code.** Files under any `*/process/` directory are read as strings and stored on invitations. The API runs them with a token minted for the invitation's first signature, normally the venue itself, `openreview.net/Support`, or `~Super_User1`. They `import openreview` from the package installed on the API server, so a change to `openreview/tools.py` or `openreview/api/client.py` is a change to what runs with venue credentials in production.
- **Anonymity is a readers problem.** Reviewer and area chair identities live in per-paper groups with `anonids: True`; who can see the mapping is the group's `deanonymizers`. Anonymous notes are signed with the anonymous group id, never the profile id.
- **Deployed venues are live data.** Builders run again on redeploy and process functions read their configuration from the venue group's `content`. Renaming an invitation, a group, or a `domain.content` key changes behaviour for venues already running.

## Security rules that apply to every file

**Secrets** — Never hardcode tokens, passwords or API keys outside `tests/`. Clients take credentials from arguments or environment. Never `print()` a token, an `Authorization` header, a full request body or a profile's `emails` in library code; process-function output becomes a stored log.

**Identity exposure** — Never put a profile id, name, or email of an anonymous reviewer or area chair into a note, an email body, a bibtex entry, a webfield constant, or a log. Resolve anonymous groups to members only where the result stays with the venue or the deanonymizers.

**Email** — On the V2 client, `post_message()` carries `invitation=` (the venue's meta invitation) and `signature=` (the venue id); the V1 `openreview.Client` accepts neither. On both: review, meta-review and decision content goes only to the readers of that note, and `ignoreRecipients` excludes the actor and groups that must not receive it.

**Code execution** — `exec()` appears only in the "super process" wrappers that load a script stored in the venue's meta invitation content. Any new `exec()` or `eval()`, and any path where a user-supplied string reaches one, is critical.

**Conflicts** — `openreview.tools.get_conflicts()` and the profile-info functions beside it decide who may review whom. A change that yields fewer conflicts for the same profiles needs a stated reason and a test.

## Tests

Every test is an integration test against the real API servers, started by `docker/run.py`. Tests in one file share server state, run in order, and depend on earlier tests. Run tests at the file level. Do not suggest mocks or unit tests for process-function behaviour.

## What not to comment on

- **Formatting and style.** No linter or formatter is configured. Line length, quote style, blank lines and import order are not findings.
- **Comments.** The codebase deliberately carries few inline comments. Do not ask for docstrings or comments on internal code.
- **Test credentials.** `Helpers.strong_password` in `tests/conftest.py` and the `openreview.net` super user login are intentional fixtures.

`.github/skills/code-review/references/known-false-positives.md` has the full triaged list.
