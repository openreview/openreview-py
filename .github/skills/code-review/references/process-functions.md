# Process Functions

Process files live under `openreview/venue/process/`, `openreview/journal/process/`, `openreview/arr/process/`, `openreview/profile/process/`, `openreview/venue_request/process/`, `openreview/workflows/process/`, `openreview/workflows/workflow_process/` and `openreview/agora/process/`. The package never imports them: builders read them with `get_process_content()` and store the text on an invitation as `process`, `preprocess`, `dateprocesses` or `postprocesses`.

## Execution model

- **Entry points.** `process(client, edit, invitation)` for note, group, edge and tag edits; `process(client, invitation)` for date and cron processes; `process_update(client, entity, invitation, existing_entity)` when the invitation declares it. JS files (`*.js` beside the Python ones) use `async function process(client, edge, invitation)` and set `client.throwErrors = true` so a failed call rejects the edit instead of continuing.
- **Who `client` is.** For venue invitations the first signature is the venue group; for `venue_request/` and `workflows/` support flows it is `openreview.net/Support`; for `profile/` it is `~Super_User1` or support. Everything `client` does in a process is done with those credentials.
- **Names available to a process file.** The API supplies `openreview`, `datetime`, `json` and `re` already imported, plus `client`. Anything else (`urllib.parse`, `csv`, or `from Crypto.Hash import HMAC, SHA256` for the `pycryptodome` dependency) is imported inside the function body, which is required, not a finding. A top-level statement other than `def` or `import` runs before the call and has no `client`.
- **Names available to a stored script.** A script run by a super-process wrapper (below) sees exactly that wrapper's `funcs` dict, plus Python builtins and whatever the script imports or defines; the wrapper's own imports are not inherited. The dicts differ: journal wrappers pass `openreview` and `datetime` (date variants add `date_index` and `days_late_map`); the workflow recruitment wrapper in `workflows/templates.py` also passes `re`, which `committee_recruitment` scripts use without importing it; the ARR revision pre-process wrapper in `arr/invitation.py` passes only `openreview`, so even `datetime` is unavailable there. A name in none of those three sources is a real `NameError`. Before reporting one, find the wrapper that runs the script and read its `funcs`.
- **Signature changes in the package.** A changed signature in `tools.py` or a client method breaks every stored process that calls it until the server is upgraded and the venue is redeployed.
- **Errors.** A pre-process rejects an edit by raising `openreview.OpenReviewException('message')`. The message is shown to the submitter, so it must not include internals such as other users' ids, group members or stack text. A process (not pre-process) that raises records an error on the edit and the job retries.

## The super-process wrappers

`journal/invitation.py` (`get_super_process_content`, `get_super_dateprocess_content`), `arr/invitation.py`, `workflows/templates.py` and `workflows/workflows.py` store a short wrapper as the process and keep the real script in the meta invitation's `content` (for example `invitation_edit_script`, `group_edit_script`), so one script serves many invitations and is updated in one place. The wrapper does:

```python
script = meta_invitation.content["<field>"]['value']
funcs = { 'openreview': openreview, 'datetime': datetime, ... }
exec(script, funcs)
funcs['process'](client, ...)
```

When this is and is not a finding is in `known-false-positives.md`.

## Rules

**Readers come from data, not literals.** When a process posts a note edit, a group edit or an edge, its `readers`, `nonreaders`, `writers` and `signatures` come from the entity it is reacting to, from the invitation it is posting through, or from `domain.content`. A literal reader list in a process is right for the venue it was written against and wrong for the next one. The venue id itself is the one acceptable literal, taken from `domain.id`.

**Idempotent and re-entrant.** Jobs retry, PCs redeploy, and date processes fire again when dates are edited. Patterns that make this safe:

- `if cdate > now: return` at the top of a date process, so an invitation scheduled for the future does nothing when its parent is re-saved.
- `if edge.tcdate != edge.tmdate: return` or checking `edit.note.ddate` to distinguish create, update and delete.
- Looking the entity up before creating it rather than catching a duplicate error. The `tools.get_*` lookup helpers differ in which errors return `None` (`client-and-tools.md` § Errors).
- `client.post_invitation_edit(..., replacement=False)` and `post_group_edit` that add to `members` instead of overwriting.

**Do not assume content.** `submission.content['title']['value']` raises `KeyError` when the venue's form has no such field; venues define their own submission forms. `submission.content.get('title', {}).get('value')` does not raise, but it yields `None`, and formatting `None` into an f-string produces the text `None` in a subject or email body rather than an error. So a missing-key lookup is a crash finding; a `.get()` chain feeding an f-string is at most a wording defect, not a crash.

**Bulk work is bounded.** Fan-outs go through `openreview.tools.concurrent_requests(fn, items, desc=..., max_workers=...)` or `post_bulk_edges` / `post_bulk_tags`. An unbounded thread pool or a sequential loop over thousands of submissions is a timeout, and the retry starts over.

**Wait when ordering matters.** `client.post_note_edit(..., await_process=True)` and `delete_edges(..., wait_to_finish=True)` exist because a process that posts an edit and then reads its result races the queue. A sequence that deletes edges and immediately posts replacements needs the wait.

**Journal processes resolve the journal.** `journal/invitation.py` `get_process_content()` rewrites `openreview.journal.Journal()` into `JournalRequest.get_journal(client, request_form_id)` when the journal was created from a request form. A journal process must call `openreview.journal.Journal()` on one line exactly so the rewrite matches; any other way of constructing it runs with default settings on request-form journals.

## What is usually fine

- A process using `client.get_group(edit.domain)` and trusting `domain.content`: the venue wrote it.
- A process signing as `venue_id` for notifications and reader updates: that is the token it holds.
