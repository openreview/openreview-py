# Known False Positives

Findings already investigated in this repository and rejected, beyond the ones listed in `.github/copilot-instructions.md`. Each entry records *why*, so that a genuine variant can still be recognised rather than the whole class being waved away. Re-raising these is worse than staying silent: it trains the team to skim automated review.

## Code patterns

**`exec(script, funcs)` in the super-process wrappers** (`process-functions.md` § The super-process wrappers). The meta invitation that holds the script is writable by the venue and support only, and the wrapper runs under the venue's token anyway, so the `exec` grants nothing the venue did not already have. Report only a wrapper that reads its script from somewhere a non-venue role can write (a note, a group another role edits, an edit's content), or a new `funcs` entry that hands the script something it should not have. `journal/process/official_recommendation_pre_process.py` runs an `additional_validation` script from the journal settings (`journal.get_official_recommendation_additional_validation()`), which only the Editors-in-Chief and support can set, under the same reasoning.

**`jwt.decode(self.token, options={"verify_signature": False})` in `api/client.py` and `openreview.py`.** Reads the expiry of the client's own token to decide when to log in again. openreview-py never makes authorization decisions; the server verifies the token on every request.

**`print()` in process functions and tests.** Process output is the stored process log and `print` is the only logging available to a process; tests print for debugging in CI logs. Counts, ids and progress are expected.

**`random.choices` in `tools.create_hash_seed()`.** Existing, triaged. A PR that touches the function should switch to `secrets.choice`; a PR that does not touch it should not be asked to.

**`verify_signature`, `expiresIn`, `tokenExpiresIn` parameters.** Session-length controls exposed to script authors on purpose; the server caps the maximum.

**Deprecated parameters kept alive.** `openreview.tools.get_invitation_source()` and several builders accept legacy string forms (`'all_submissions'`, `reply_to`, `source_submissions_query`) alongside the dict form. The branches marked deprecated exist for venues deployed on the old form; removing them is a breaking change, not a cleanup.

**Long functions and large files.** `venue/invitation.py`, `journal/invitation.py`, `tools.py` and most test files are thousands of lines, and many tests are hundreds of lines because they walk a whole venue. Length alone is not a finding, and refactoring suggestions without a defect are noise.

## Tests and the local stack

**Hardcoded venue ids, names and emails in `tests/`.** `TestVenue.cc`, `ICLR.cc/2026/Conference`, `TMLR`, fixed emails such as `reviewer_venue_one@mail.com` (the activation path is local-only) and `localhost:3000` / `localhost:3001` base URLs are the fixture vocabulary of the suite.

**`tests/drivers/geckodriver`** is provided by the Docker image.

**`docker/config.json`** is gitignored; `config.example.json` holds paths and branch names, not secrets.
