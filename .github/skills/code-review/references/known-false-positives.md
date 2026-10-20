# Known False Positives

Findings that have already been investigated in this repository and rejected. Each entry records *why*, so that a genuine variant can still be recognised rather than the whole class being waved away.

Re-raising these is worse than staying silent: it trains the team to skim automated review.

## Code patterns

**`exec(script, funcs)` in the super-process wrappers.**
`journal/invitation.py` (`get_super_process_content`, `get_super_dateprocess_content`), `arr/invitation.py`, `workflows/templates.py` and `workflows/workflows.py` store a short wrapper as the invitation's process and keep the real script in the venue's meta invitation `content`. The meta invitation is writable by the venue and support only, and the wrapper runs under the venue's token anyway, so the `exec` grants nothing the venue did not already have. Do not report these. *Do* report a wrapper that reads the script from a note, a group a non-venue role can edit, or an edit's content; a new `funcs` entry; and any `exec` or `eval` elsewhere. `journal/process/official_recommendation_pre_process.py` runs an `additional_validation` script taken from the journal settings (`journal.get_official_recommendation_additional_validation()`), which only the Editors-in-Chief and support can set, under the same reasoning.

**`jwt.decode(self.token, options={"verify_signature": False})` in `api/client.py` and `openreview.py`.**
Reads the expiry of the client's own token to decide when to log in again. It is not an authentication decision; the server verifies the token on every request. Flag it only if a code path starts trusting decoded claims for authorization.

**Webfield `.replace("var VENUE_ID = '';", ...)` substitution.**
`venue/group.py`, `journal/group.py`, `venue_request/venue_request.py` and others personalise JavaScript templates by string replacement with venue-configured values (ids, names, counts). The values are not user input and the page runs with the viewer's own token. Not an injection finding. A value with venue-only readers (`hash_seed`, tokens, email lists) being substituted *would* be a finding.

**`print()` inside process functions.**
Process output is the stored process log, and `print` is the only logging mechanism available in the wrapped script. Printing counts, ids and progress is expected. Printing tokens, emails or profile email lists is not.

**Imports inside `def process(...)`.**
For a process file the API executes directly, the server supplies only `openreview`, `datetime`, `json` and `re`; anything else must be imported inside the function, and an in-function `import` is not a finding. `from Crypto.Hash import HMAC, SHA256` inside a pre-process is the intended use of the `pycryptodome` dependency. This exemption does not extend to scripts run by the super-process wrappers (`journal/invitation.py`, `arr/invitation.py`, `workflows/templates.py`, `workflows/workflows.py`): their `exec` namespace holds only `openreview` and `datetime` (plus `date_index` and `days_late_map` for date processes), so a stored script using `json` or `re` without importing them is a genuine `NameError`.

**`random.choices` in `tools.create_hash_seed()`.**
Existing, triaged. A PR that touches the function should switch to `secrets.choice`; a PR that does not touch it should not be asked to.

**`verify_signature`, `expiresIn`, `tokenExpiresIn` parameters.**
Session-length controls exposed to script authors on purpose; the server caps the maximum.

**Hardcoded venue ids and names in `tests/`.**
`TestVenue.cc`, `ICLR.cc/2026/Conference`, `TMLR`, non-ASCII submission names such as `提交`, fixed test emails like `reviewer_venue_one@mail.com`, and `localhost:3000` / `localhost:3001` base URLs are the fixture vocabulary of the suite.

**Long functions and large files.**
`venue/invitation.py`, `journal/invitation.py`, `tools.py` and most test files are thousands of lines. Length alone is not a finding and refactoring suggestions without a defect are noise.

## Credentials

**`Helpers.strong_password` in `tests/conftest.py`.**
The shared password for every test user and for the `openreview.net` super user in the local stack. Committed deliberately so the suite runs without setup. Not a leaked credential.

**The `openreview.net` super user login in fixtures and `docker/`.**
Local-stack only. No production credentials are committed.

**`docker/config.json`.**
Gitignored; `config.example.json` holds paths and branch names, not secrets.

## Conventions

**No linter, no formatter.**
Nothing in `pyproject.toml` or the repository configures ruff, flake8, black or isort. Spacing around `=` in keyword arguments, quote style, import order, trailing whitespace and line length vary across files on `master`. Formatting-only comments are noise. Never suggest running a formatter over a glob.

**Few comments and docstrings.**
Internal code is deliberately sparse on comments. Do not ask for docstrings on builder or process code; the public client methods in `api/client.py` and `tools.py` do carry docstrings for the Sphinx docs, and a new public method there should too.

**Deprecated parameters kept alive.**
`openreview.tools.get_invitation_source()` and several builders accept legacy string forms (`'all_submissions'`, `reply_to`, `source_submissions_query`) alongside the dict form. The branches marked deprecated exist for venues deployed on the old form; removing them is a breaking change, not a cleanup.

**Duplicate-looking builders.**
`venue_request/` and `workflows/` implement the same stages twice because they are two deployment paths. Suggesting one be deleted in favour of the other is out of scope for a PR review.

## Rules that were narrowed after firing falsely

Rules in this skill are scoped to new code and name their exemptions, following the api repository's experience with rules that fired on compliant code:

- `'everyone'` in readers is flagged only when no public check guards it, not wherever it appears.
- Literal reader lists are flagged in process functions and new builders; `[venue_id]` from `domain.id` and `[venue.id]` in builders are the baseline, not a literal.
- Missing `ignoreRecipients` is flagged when the actor or an excluded group is in `recipients`, not on every `post_message`.
- Missing `should_match_invitation_source()` is flagged on fan-outs over submissions, not on lookups of a single note by id.
- `domain.content[key]['value']` is flagged for keys introduced recently, not for `meta_invitation_id`, `submission_id`, `submission_name`, `program_chairs_id` and `title`, which every venue has.
