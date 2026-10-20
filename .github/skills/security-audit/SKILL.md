---
name: security-audit
description: Perform a targeted privacy and integrity audit of an openreview-py stage, process function, builder, journal flow or helper, tracing the readers, signatures, emails and edges it produces for every venue setting and reproducing findings with an integration test. Use when asked to audit security, check who can see a note or an identity, verify anonymity, review conflict detection or assignment visibility, assess a workflow stage end to end, or when the request mentions threat model, data leak, deanonymization or attack surface for any part of this codebase. For reviewing a pull request diff rather than auditing a whole feature, use the code-review skill instead.
license: MIT
---

# Security Audit

A focused audit of one stage, process function, builder, journal flow or helper. Trace what it writes (readers, nonreaders, writers, signatures, invitees, deanonymizers, edges, emails) under every venue setting that reaches it, and — when something is found — reproduce it with an integration test before proposing a fix.

## Target

The user supplies one of:

- a stage — review, meta review, decision, bidding, matching, withdrawal, camera-ready, ethics review
- a process function — `venue/process/review_process.py`, `journal/process/review_process.py`
- a builder — `set_review_invitation`, `Matching._create_edge_invitation`, `set_post_submission_invitation`
- a helper — `tools.get_conflicts`, `tools.get_profiles`, `get_user_hash_key`
- a flow — name removal, profile merge, reviewer recruitment, journal submission to decision

If it is ambiguous, ask which before starting.

## Step 1 — Map what the target writes

Build a complete picture before looking for flaws.

**Stage or builder.** Find the `create_*_stage()` method in `venue/venue.py` or `journal/journal.py`, the `set_*_invitation()` it calls, and the `*Stage` class in `stages/venue_stages.py` that resolves readers. List every reader, nonreader, writer, signature and invitee expression in the invitation template, including `${...}` pointers, and what each resolves to per child invitation. Note which `Venue` or `journal.settings` attributes each branch depends on.

**Process function.** Read the file and every `client.post_*` and `client.post_message` call in it. For each, record the readers it writes or the recipients it mails and where those values come from (the note, the invitation, `domain.content`, a literal). Note which `domain.content` keys are read without defaults.

**Helper.** Read it, grep for callers across `openreview/` including `*/process/` files, and trace both directions. A helper called from a process runs with venue credentials.

**Flow.** Walk the invitations in order (request → pre-process → process → decision → process), recording readers of each note and who may sign each step.

Record every file and line range — findings need them.

## Step 2 — Enumerate the settings

List the venue shapes that reach the target and check each branch:

- Anonymity: double-blind, single-blind (`test_non_anonnymous_venue.py`), open (`test_workshop_no_anonymity.py`); journal `author_anonymity`, `AE_anonymity`, `reviewer_to_reviewer_anonymity`.
- Roles: `use_area_chairs`, `use_senior_area_chairs`, `use_ethics_chairs`, `use_ethics_reviewers`, `use_secondary_area_chairs`, multiple `reviewer_roles`.
- Visibility: `public` on the stage, `submission_stage.readers`, journal `submission_visibility`, `release_to_reviewers`, `release_to_authors`, `review_release`.
- Lifecycle: the submission is active, withdrawn, desk-rejected, rejected or accepted when the target runs.
- Deployment path: classic `venue_request/` and template `workflows/`.
- Redeploy: the target runs a second time on a venue with existing data.

Note each combination as covered, not reachable, or not checked.

## Step 3 — Work the checklist

`references/checklist.md` covers eight categories: readers and nonreaders, anonymity, emails, edges and matching, process-function execution, profile and PII handling, workflow integrity, and the client and helpers. Not every item applies to every target — work the relevant ones. `.github/skills/code-review/references/permission-model.md` has the full treatment of where the lists are built and how they change across stages.

## Step 4 — Write the report

```
# Security Audit: <target>

## Scope
- Target:
- Files reviewed: <with line ranges>
- Settings covered: <from Step 2, with "not checked" called out>

## Findings

### <CRITICAL|HIGH|MEDIUM|LOW> — <short title>
- Location: file:line
- Setting: which venue configuration and lifecycle state reaches it
- Issue: what is written or sent, to whom, that should not be
- Impact: what the unintended reader learns or can do
- Reproducible: yes / no / uncertain
- Recommendation: how to fix it

## Verified Controls
<readers, nonreaders, signatures, emails and guards that ARE correct, with the setting they were checked under>

## Summary
Critical: N   High: N   Medium: N   Low: N   Informational: N
```

**Severity.** Critical — a reader outside the intended set can see submission content, review content, reviewer or area chair identity, or profile emails; process code reachable by someone other than the venue or support. High — integrity: missed conflicts, authors able to read assignment or bid edges, a signature accepted that the actor cannot hold, a stage transition leaving wrong `venueid` or readers, a change that breaks running venues on redeploy. Medium — needs specific settings or ordering, or has limited exposure. Low — defence in depth. Informational — hardening.

Every finding names the file and line, the setting combination, the entity and the unintended reader, and whether you read the code path or inferred it. If unsure something is real, say so.

The Verified Controls section matters. It shows the audit was thorough and stops a short findings list from reading as a shallow one. Do not pad with generic advice that names no specific gap.

## Step 5 — Reproduce with a test

Required for every Critical and High finding, and for Medium where feasible. A leak that cannot be reproduced may not be real.

The suite is pytest integration tests run through `docker/run.py` against real API servers. Fixtures and helpers are in `tests/conftest.py`: `openreview_client` is the V2 super user, `helpers.create_user(email, first, last)` returns a logged-in client for a new user, `helpers.await_queue_edit(openreview_client, edit_id=...)` waits for the process that an edit triggers. Tests within a file share state and run in order.

Shape of a reproduction:

1. Pick the test file whose venue has the setting from the finding (`test_iclr_conference_v2.py` for SACs and ethics, `test_journal.py` for TMLR-style journals, `test_*_with_templates.py` for the workflow path, and so on), and add the test at the end of the file so it reuses the venue and users already created.
2. Drive the target: post the edit, or wait for the date process, as the role that triggers it.
3. As the user who should be excluded — an author's client for reviewer identity, a reviewer's client for another reviewer's unreleased review — fetch the note, group, edge or message.
4. Assert the outcome that *should* happen: `pytest.raises(openreview.OpenReviewException, match=r'.*Forbidden.*')`, an exact `readers` list, or `len(openreview_client.get_messages(to=..., subject=...)) == 0`.

Written that way the test **fails while the bug exists** and passes once fixed. Run the whole file, never the single test, and show the user the failing output before proposing a fix.

If the test passes immediately, either the leak is not real (remove it from the findings) or the test is not reaching the code path (check the setting combination, the lifecycle state and whether the queue was awaited).

## Step 6 — Fix and verify

Apply the fix at the specific file and line, re-run the file, then run the other venue files whose settings share the code path (a `ReviewStage.get_readers()` change touches every conference file). Use the test-runner agent where available.

Ask whether the user wants a PR, and whether multiple confirmed findings should be one PR or several. A PR carries the reproduction test alongside the fix — the test documents the reader set even once it passes.
