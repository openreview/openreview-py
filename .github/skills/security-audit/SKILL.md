---
name: security-audit
description: Perform a targeted privacy and integrity audit of an openreview-py stage, process function, builder, journal flow or helper, tracing the readers, signatures, emails and edges it produces for every venue setting and reproducing findings with an integration test. Use when asked to audit security, check who can see a note or an identity, verify anonymity, review conflict detection or assignment visibility, assess a workflow stage end to end, or when the request mentions threat model, data leak, deanonymization or attack surface for any part of this codebase. For reviewing a pull request diff rather than auditing a whole feature, use the code-review skill instead.
license: MIT
---

# Security Audit

A focused audit of one stage, process function, builder, journal flow or helper. Trace what it writes (readers, nonreaders, writers, signatures, invitees, deanonymizers, edges, emails) under every venue setting that reaches it, and — when something is found — reproduce it with an integration test before proposing a fix.

The rules to audit against are in `.github/copilot-instructions.md` and the code-review skill's references (`.github/skills/code-review/references/`). This skill holds only the procedure.

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

**Helper.** Read it, grep for callers across `openreview/` including `*/process/` files, and trace both directions.

**Flow.** Walk the invitations in order (request → pre-process → process → decision → process), recording readers of each note and who may sign each step.

Record every file and line range — findings need them.

## Step 2 — Enumerate the settings

List the venue shapes that reach the target and check each branch:

- Anonymity: double-blind, single-blind and open venues; the journal anonymity settings.
- Roles: which optional committees and reviewer roles the venue enables.
- Visibility: public stages, submission readers, journal submission visibility, and the review and decision release settings.
- Lifecycle: the submission is undecided, withdrawn, desk-rejected, rejected or accepted when the target runs.
- Deployment: the classic and template paths, and a second run on a venue with existing data.

`tests.md` maps each setting to the venue test file that exercises it. Note each combination as covered, not reachable, or not checked.

## Step 3 — Work the references

For the target, work every section below that applies. Not every area applies to every target.

| Area | Sections in `.github/skills/code-review/references/` |
|---|---|
| Readers and nonreaders | `permission-model.md` (Where the lists are built, Public vs restricted, Writers and invitees); `invitation-builders.md` (Dollar-sign pointers, Mirrors and params) |
| Anonymity | `permission-model.md` (Anonymity) |
| Emails | `emails.md` |
| Edges, matching and conflicts | `permission-model.md` (Edges); `workflow-stages.md` (Invariants to check on every stage change); `client-and-tools.md` (Conflict detection, Bulk helpers) |
| Process-function execution | `process-functions.md`; `architecture.md` (Venue configuration, Submission states and invitation source); `known-false-positives.md` |
| Profiles and personal data | `profile-management.md`; `client-and-tools.md` (Profiles and emails, Recruitment links) |
| Workflow integrity | `workflow-stages.md`; `invitation-builders.md` (Dates, PC-editable sub-invitations, Redeploy safety); `architecture.md` (Two deployment paths) |
| Client and helpers | `client-and-tools.md` |

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

Use the severity levels and the bar for a finding in the code-review skill's `SKILL.md`, and for each finding also say whether you read the code path or inferred it.

The Verified Controls section matters. It shows the audit was thorough and stops a short findings list from reading as a shallow one.

## Step 5 — Reproduce with a test

Required for every Critical and High finding, and for Medium where feasible. A leak that cannot be reproduced may not be real. `tests.md` describes the suite, its fixtures, and where a new test goes.

Shape of a reproduction:

1. In the test file whose venue has the setting from the finding, add the test as `tests.md` § Writing a test for a fix describes.
2. Drive the target: post the edit, or wait for the date process, as the role that triggers it.
3. As the user who should be excluded — an author's client for reviewer identity, a reviewer's client for another reviewer's unreleased review — fetch the note, group, edge or message.
4. Assert the outcome that *should* happen: `pytest.raises(openreview.OpenReviewException, match=r'.*Forbidden.*')`, an exact `readers` list, or `len(openreview_client.get_messages(to=..., subject=...)) == 0`.

Show the user the failing output before proposing a fix. If the test passes immediately, either the leak is not real (remove it from the findings) or the test is not reaching the code path (check the setting combination, the lifecycle state and whether the queue was awaited).

## Step 6 — Fix and verify

Apply the fix at the specific file and line, re-run the file, then run the other venue files whose settings share the code path (a `ReviewStage.get_readers()` change touches every conference file). Use the test-runner agent where available.

Ask whether the user wants a PR, and whether multiple confirmed findings should be one PR or several. A PR carries the reproduction test alongside the fix — the test documents the reader set even once it passes.
