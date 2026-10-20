---
name: code-review
description: Review changes to openreview-py for privacy, integrity and workflow correctness. Use when reviewing a pull request, diff, commit, or file in this repository — including changes to the venue, journal, ARR, stages, workflows and venue_request builders, any process or webfield file, profile management, the V1 and V2 API clients, tools.py, tests, CircleCI config, GitHub Actions workflows, or packaging. Covers the readers/nonreaders/signatures lists this library authors, reviewer and area chair anonymity, server-side process-function execution with venue credentials, email notifications, conflict detection, assignment and bid edges, PC-editable invitations, deployed-venue compatibility, and the findings already triaged as false positives in this codebase.
license: MIT
---

# Reviewing openreview-py

Python client and venue-management library for a peer-review platform. It is used three ways, and a diff can affect all three at once:

- **As a client**, by program chairs, journal editors and support staff running scripts and notebooks.
- **As a builder**, when `Venue.setup()`, `Journal.setup()` and the workflow templates post groups and invitations whose `readers`, `writers`, `signatures`, `invitees` and `deanonymizers` the API then enforces.
- **As server-side code**, when the API executes the Python process functions stored on those invitations, importing `openreview` from the package installed on the API server and authenticating as the invitation's first signature.

Three properties drive nearly every real finding:

1. **This library authors access control.** The API decides visibility from `readers`/`nonreaders` set membership, but the lists come from here. A builder that adds `everyone` without checking the submission is public, a process function that posts an edit with hand-written readers instead of the note's, or an email that quotes a review to someone outside its readers, is a leak the server will enforce faithfully.
2. **Anonymity is a readers problem.** Reviewer and area chair identities live in per-paper groups with `anonids: True`; `deanonymizers` says who may map the anonymous id to a profile. A real profile id or name reaching a note, an email, a bibtex entry, a webfield constant or a log is a deanonymization.
3. **Process functions run as the venue.** Whoever can change a `*/process/*.py` file, or a helper it imports, changes what runs with venue, support or super-user credentials in production. They also run again on retry and on redeploy, against venues that were configured by older versions of this code.

**Before commenting, read `references/known-false-positives.md`.** It lists findings already investigated and rejected here. Re-raising them trains the team to skim automated review.

## Non-negotiables by directory

Apply these from this page; open the matching reference for mechanism and edge cases.

### Builders: `openreview/venue/`, `openreview/journal/`, `openreview/arr/`, `openreview/stages/`, `openreview/workflows/`, `openreview/venue_request/` → `references/permission-model.md`, `references/invitation-builders.md`
- `'everyone'` enters a readers list only behind a check that the submission is public (`submission_stage.public`, `journal.is_submission_public()`, `release_to_public`). An ethics review, a retraction, a comment or a decision cannot be more visible than its submission.
- Anonymous committee members are referenced by anonymous group (`get_reviewers_id(number, anon=True)`, `get_area_chairs_id(number, anon=True)`) in `signatures` and in per-reviewer readers. A profile id or the non-anonymous group appears there only when the venue is not anonymous.
- Edit readers mirror note readers (`'${2/note/readers}'`), and `nonreaders` are carried together with `readers`. Dropping a `nonreaders` list while widening `readers` is a finding.
- Assignment, proposed assignment, affinity and bid edges carry `nonreaders: [authors group]`. Conflict edges and invitation `hash_seed` content stay readable by the venue only.
- A builder change must be safe on a venue deployed by an older version: new `domain.content` keys get defaults where they are read, invitation and group ids do not change, and `save_invitation` does not wipe content a PC edited.
- The classic path (`venue_request/`) and the template path (`workflows/`) deploy the same stages. A behaviour change in one usually needs the same change in the other.

### `*/process/` and `*/webfield/` → `references/process-functions.md`, `references/emails.md`
- `client` is the venue, support group or super user. Every `client.post_*` is privileged; readers on anything it posts come from the note, the invitation or `domain.content`, never from a literal.
- A process must be safe to run twice. Date processes guard on `cdate > now` and filter submissions through `openreview.tools.should_match_invitation_source()`; edit processes do not assume the entity is new.
- `domain.content` keys introduced by the PR are read with `domain.get_content_value(key, default)`; `domain.content[key]['value']` on a new key breaks every venue deployed before the PR.
- Pre-processes reject by raising `openreview.OpenReviewException` with a message safe to show the submitter. JS pre-processes set `client.throwErrors = true`.
- Emails sent through the V2 client (`openreview.api.OpenReviewClient`) carry `invitation=`, `signature=` and `sender`. The V1 `openreview.Client.post_message()` accepts neither `invitation` nor `signature`; the `venue_request/`, `journal/journal_request/` and `agora/` processes run on it, so do not ask for those keywords there. Audience rules apply to both clients: review, meta-review and decision text goes only to that note's readers, and anonymous signatures are never resolved to names for recipients outside the deanonymizers.
- A webfield constant substituted with `.replace("var X = '';", ...)` is visible to every user who loads the page. Only venue configuration goes there.

### `openreview/profile/` → `references/profile-management.md`
- Process functions here sign as `~Super_User1` or `openreview.net/Support` and rewrite profiles, groups, notes and edges. A pre-process must verify the requester owns the name, email or paper they are acting on.
- Request notes that contain an email or a name being removed are readable by the requester and support only.
- A rename or removal must cascade to every reference (profile names, notes, edges, groups) or it leaves a dangling identity; that is an integrity finding, not a style one.

### `openreview/api/client.py`, `openreview/openreview.py`, `openreview/tools.py` → `references/client-and-tools.md`
- These run on the API server inside process functions. A signature change breaks stored process code; a behaviour change in a helper is a production change.
- `get_conflicts()`, `get_profile_info()`, `get_neurips_profile_info()`, `get_comprehensive_profile_info()`, `subdomains()` and `duplicate_domains.json` decide who may review whom. Fewer conflicts for the same input needs a reason and a test.
- Profile lookup by email uses `confirmedEmails`. Switching to `emails` lets an unconfirmed address claim a profile.
- Never log a token, an `Authorization` header or a request body. `LogRetry` already prints response text on retry; do not widen what it prints.
- Public method signatures are an API: parameters are added with defaults, never renamed or removed. Python 3.9 is the floor — no `match`, no `X | None`.

### `tests/` → `references/tests.md`
- Every test hits the real servers. Do not suggest mocks or unit tests for process-function behaviour.
- Assert `readers`, `nonreaders` and `signatures` exactly, and select emails by recipient and subject, not list position.
- A test for a bug must fail before the fix. Run and cite tests at the file level.

### `.circleci/`, `.github/workflows/`, `pyproject.toml` → `references/ci-and-packaging.md`
- A new subpackage directory must be added to `[tool.setuptools.packages.find] include` or it is missing from the wheel the API servers install.
- PR builds run only the modified test files first, then the full suite. A library change with no modified test file gets no targeted run; say so when the change deserves one.
- Deploy workflows run on `workflow_dispatch` only and authenticate to GCP with OIDC. No `pull_request_target`, no PR-controlled data in a `run:` block.

## Severity

- **Critical** — a reader outside the intended set can see submission content, review content, reviewer or area chair identity, or profile emails; process-function code reachable by someone other than the venue or support.
- **High** — integrity: conflicts missed, a committee member assigned or able to bid where they should not, authors able to read assignment or bid edges, a signature accepted that the actor cannot hold, a stage transition that leaves submissions in the wrong `venueid` or readers; a change that breaks running venues on redeploy.
- **Medium** — needs specific venue settings or a specific stage ordering; limited exposure such as a bibtex author list on a withdrawn anonymous paper.
- **Low** — defence in depth. **Informational** — hardening.

## What makes a finding worth posting

Name the exact file and line and the concrete path: which venue setting, which stage, which user, what they post or open, what they see or change that they should not. "This could leak data" without the reader set and the entity is a guess.

If unsure whether something is real, say so and explain the uncertainty rather than dropping it silently or asserting it. A hedged true finding is useful; a confident false one costs a reviewer an hour.

Do not pad a review with generic advice — "add error handling", "consider validating input" — that names no specific place. Where an area is well secured, saying so is more useful than inventing a comment.

For a full audit of a stage, a process function or a journal flow rather than a diff review, use the `security-audit` skill.
