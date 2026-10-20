# Process Functions

Files under `openreview/venue/process/`, `openreview/journal/process/`, `openreview/arr/process/`, `openreview/profile/process/`, `openreview/venue_request/process/`, `openreview/workflows/process/`, `openreview/workflows/workflow_process/` and `openreview/agora/process/` are not imported by this package. Builders read them with `get_process_content()` and store the text on an invitation (`process`, `preprocess`, `dateprocesses`, `postprocesses`). The API executes them.

## Execution model

- The server supplies `openreview`, `datetime`, `json` and `re` already imported, plus an authenticated `client`, and calls the function. Nothing else is available; a process that needs `urllib.parse`, `Crypto.Hash` or `csv` imports it inside the function body. A module-level import in a process file is fine in Python but a top-level statement other than `def` or `import` runs before the call and has no `client`.
- Entry points: `process(client, edit, invitation)` for note, group, edge and tag edits; `process(client, invitation)` for date processes and cron processes; `process_update(client, entity, invitation, existing_entity)` when the invitation declares it. JS files (`*.js` beside the Python ones) use `async function process(client, edge, invitation)` and should set `client.throwErrors = true` so a failed call rejects the edit instead of continuing.
- `token` is minted for `invitation.signatures[0]`. For venue invitations that is the venue group; for `venue_request/` and `workflows/` support flows it is `openreview.net/Support`; for `profile/` it is `~Super_User1` or support. Everything `client` does in a process is done with those credentials.
- `openreview` is the package installed on the API server. A helper in `tools.py` or a client method is therefore server-side code when a process calls it, and a signature change there breaks every stored process that uses it until the server is upgraded and the venue is redeployed.
- A pre-process rejects an edit by raising `openreview.OpenReviewException('message')`. The message is shown to the submitter, so it must not include internals such as other users' ids, group members or stack text. A process (not pre-process) that raises records an error on the edit and the job retries.
- `print()` output becomes the stored process log, readable by the venue. Tokens, email addresses and profile email lists do not belong there.

## The super-process wrappers

`journal/invitation.py` (`get_super_process_content`, `get_super_dateprocess_content`), `arr/invitation.py`, `workflows/templates.py` and `workflows/workflows.py` store a short wrapper as the process and keep the real script in the meta invitation's `content` (for example `invitation_edit_script`, `group_edit_script`). The wrapper does:

```python
script = meta_invitation.content["<field>"]['value']
funcs = { 'openreview': openreview, 'datetime': datetime, ... }
exec(script, funcs)
funcs['process'](client, ...)
```

This is deliberate: it lets one script serve many invitations and be updated in one place. It is safe because the meta invitation's `writers` are the venue and support. The things to flag are a wrapper that reads the script from somewhere a non-venue user can write (a note, a group another role edits, an edit's content), a new `funcs` entry that hands the script something it should not have, and any `exec` or `eval` outside these wrappers.

## Rules

**Readers come from data, not literals.** When a process posts a note edit, a group edit or an edge, its `readers`, `nonreaders`, `writers` and `signatures` come from the entity it is reacting to, from the invitation it is posting through, or from `domain.content`. A literal reader list in a process is right for the venue it was written against and wrong for the next one. The venue id itself is the one acceptable literal, taken from `domain.id`.

**Idempotent and re-entrant.** Jobs retry, PCs redeploy, and date processes fire again when dates are edited. Patterns that make this safe:

- `if cdate > now: return` at the top of a date process, so an invitation scheduled for the future does nothing when its parent is re-saved.
- `if edge.tcdate != edge.tmdate: return` or checking `edit.note.ddate` to distinguish create, update and delete.
- Looking the entity up before creating it (`openreview.tools.get_group`, `get_invitation`, `get_note` return `None` on not-found) rather than catching a duplicate error.
- `client.post_invitation_edit(..., replacement=False)` and `post_group_edit` that add to `members` instead of overwriting.

**Filter submissions by source.** Date processes that fan out over submissions list them with `client.get_all_notes(invitation=submission_id, ...)` and then keep only those where `openreview.tools.should_match_invitation_source(client, invitation, note, domain=domain)` is true. Skipping the filter acts on withdrawn, desk-rejected and already-decided papers; #3283 added a regression test for exactly that.

**Configurable names.** Read `submission_name`, `reviewers_name`, `review_name`, `area_chairs_name`, `reviewers_anon_name` and the `*_id` keys from `domain.content`. Build per-paper ids with `f'{venue_id}/{submission_name}{number}/{reviewers_name}'`, never with `Paper` or `Reviewers` spelled out. Use `openreview.tools.pretty_id()` for human-readable text.

**New keys need defaults.** `domain.get_content_value('key', default)` for anything introduced in the same PR or recently. `domain.content['key']['value']` is only safe for keys every deployed venue has had since it was created (`meta_invitation_id`, `submission_id`, `submission_name`, `program_chairs_id`, `title`). The parent invitation's content has the same problem: `parent_invitation.get_content_value('users_to_notify', [])`.

**Do not assume content.** `submission.content.get('title', {}).get('value')` rather than `submission.content['title']['value']` — venues define their own submission forms (#3193).

**Bulk work is bounded.** Fan-outs go through `openreview.tools.concurrent_requests(fn, items, desc=..., max_workers=...)` or `post_bulk_edges`. An unbounded thread pool or a sequential loop over thousands of submissions is a timeout, and the retry starts over.

**Wait when ordering matters.** `client.post_note_edit(..., await_process=True)` and `delete_edges(..., wait_to_finish=True)` exist because a process that posts an edit and then reads its result races the queue. A sequence that deletes edges and immediately posts replacements needs the wait (#3209).

**Journal processes resolve the journal.** `journal/invitation.py` `get_process_content()` rewrites `openreview.journal.Journal()` into `JournalRequest.get_journal(client, request_form_id)` when the journal was created from a request form. A journal process must call `openreview.journal.Journal()` on one line exactly so the rewrite matches; any other way of constructing it runs with default settings on request-form journals.

## What is usually fine

- A process using `client.get_group(edit.domain)` and trusting `domain.content`: the venue wrote it.
- A process signing as `venue_id` for notifications and reader updates: that is the token it holds.
- Retrying a failed `post_message` or skipping a notification when `recipients` is empty (#3142).
- Imports inside the function body.
