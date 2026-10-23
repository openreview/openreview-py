---
name: code-review
description: Review changes to openreview-py for privacy, integrity and workflow correctness. Use when reviewing a pull request, diff, commit, or file in this repository — including changes to the venue, journal, ARR, stages, workflows and venue_request builders, any process or webfield file, profile management, the V1 and V2 API clients, tools.py, tests, CircleCI config, GitHub Actions workflows, or packaging. Covers the readers/nonreaders/signatures lists this library authors, reviewer and area chair anonymity, server-side process-function execution with venue credentials, email notifications, conflict detection, assignment and bid edges, PC-editable invitations, deployed-venue compatibility, and the findings already triaged as false positives in this codebase.
license: MIT
---

# Reviewing openreview-py

`.github/copilot-instructions.md` states the four properties behind most real findings here and the rules that apply to every file. Every other rule is stated once, in the reference for the area of the code it governs, so the rules for a change are in the references for the code it touches.

## Before commenting

1. Read `references/architecture.md` and `references/known-false-positives.md`.
2. For each area the diff touches, read the references in the table below.
3. Verify file locations and line numbers in the code before citing them; the references can drift as code moves.

| The diff touches | Read in `references/` |
|---|---|
| Builders in `venue/`, `journal/`, `arr/`, `stages/`, `workflows/`, `venue_request/` | `permission-model.md`, `invitation-builders.md`, `workflow-stages.md` |
| `venue/matching.py` | the builder references, plus `client-and-tools.md` § Conflict detection |
| Any `*/process/` or `workflows/workflow_process/` file | `process-functions.md`, `permission-model.md`, and `emails.md` when it sends mail |
| Any `*/webfield/` file | `invitation-builders.md` § Webfields |
| `profile/` | `profile-management.md` |
| `api/client.py`, `openreview.py`, `tools.py` | `client-and-tools.md` |
| Recruitment: `*/recruitment.py`, `*recruitment*process.py` | `client-and-tools.md` § Recruitment links |
| `tests/` | `tests.md` |
| `pyproject.toml`, `MANIFEST.in`, `.circleci/`, `.github/workflows/` | `ci-and-packaging.md` |

## Severity

- **Critical** — a reader outside the intended set can see submission content, review content, reviewer or area chair identity, or profile emails; process-function code reachable by someone other than the venue or support.
- **High** — integrity: conflicts missed, a committee member assigned or able to bid where they should not, authors able to read assignment or bid edges, a signature accepted that the actor cannot hold, a stage transition that leaves submissions in the wrong `venueid` or readers; a change that breaks running venues on redeploy.
- **Medium** — needs specific venue settings or a specific stage ordering; limited exposure such as a bibtex author list on a withdrawn anonymous paper.
- **Low** — defence in depth.
- **Informational** — hardening.

## What makes a finding worth posting

Name the exact file and line and the concrete path: which venue setting, which stage, which user, what they post or open, what they see or change that they should not. "This could leak data" without the reader set and the entity is a guess.

If unsure whether something is real, say so and explain the uncertainty rather than dropping it silently or asserting it. A hedged true finding is useful; a confident false one costs a reviewer an hour.

Do not pad a review with generic advice — "add error handling", "consider validating input" — that names no specific place. Where an area is well secured, saying so is more useful than inventing a comment.

For a full audit of a stage, a process function or a journal flow rather than a diff review, use the `security-audit` skill.
