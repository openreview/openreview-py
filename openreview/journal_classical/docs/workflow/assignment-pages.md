# Assignment Pages And Buttons

Assignment actions are paper-specific. A user should start from a paper row,
paper page, or paper-specific assignment page so conflict checks, role context,
back links, audit wording, and candidate eligibility all refer to one selected
paper.

The normal EIC console sequence is:

1. Click `Create assignment pages` from the EIC Pending Tasks row.
2. Wait for the row to refresh into setup-ready state.
3. Use `Assign Action Editor` for ordinary submissions, or
   `Auto-assign previous AE/reviewers` to retry or accelerate eligible
   resubmission continuity before the two-hour automation succeeds.
4. On the assignment page, select a candidate and submit
   `Assign selected action editor`.

## Assignment Page Flow

Assignment pages keep JMLR's custom paper-specific pages and hubs. They may be
backed by an OpenReview Edge Browser-compatible structured contract for
assignment data and semantics, but the normal visible workflow is not the raw
OpenReview Edge Browser UI.

| Step | Visible Surface | What It Means |
| --- | --- | --- |
| Setup needed | EIC Pending Tasks row | The paper is submitted and has no handling Action Editor. The row shows `Create assignment pages` only; it should not yet link to the paper page or assignment page. |
| Setup in progress | EIC Pending Tasks row | Assignment setup is running. Assignment controls remain hidden until setup readiness is recorded. |
| Setup failed or stale | EIC Pending Tasks row | Assignment setup did not finish cleanly or became stale. The row may show `Retry setup`; assignment controls remain hidden until retry succeeds. |
| Setup ready | EIC Pending Tasks row | Assignment pages are ready. Ordinary new submissions may show `Assign Action Editor`. Eligible resubmissions may show `Auto-assign previous AE/reviewers` until previous-AE continuity is assigned. |
| Paper-page launcher | Paper page action | `Assign Action Editor` opens the paper-specific assignment page. It is navigation only; assignment selection happens on the dedicated page. |
| Assignment page | Paper Action Editors assignment page | EICs review candidates, search Action Editors, select one eligible candidate, and submit `Assign selected action editor`. |
| Reviewer assignment | Paper Reviewers assignment page | The handling AE or EIC manages reviewer assignment through checked reviewer-assignment tools. |

## Button Reference

| Button Or Link | Who Sees It | When It Appears | Effect |
| --- | --- | --- | --- |
| `Create assignment pages` | Non-conflicted Editors-in-Chief | Submitted paper with no handling AE and no setup-ready status. | Creates or refreshes paper-specific AE and reviewer assignment pages. It does not assign an AE or reviewers. |
| Paper-page link | Non-conflicted Editors-in-Chief | Only after assignment setup is ready. | Opens the paper page so the EIC can inspect the paper and use paper-specific actions. |
| `Assign Action Editor` | Non-conflicted Editors-in-Chief | Ordinary setup-ready submitted papers, and paper pages after setup readiness. | Opens the paper-specific Action Editor assignment page. It does not assign by itself. |
| `Auto-assign previous AE/reviewers` | Non-conflicted Editors-in-Chief | Eligible resubmissions after setup readiness when continuity candidates exist and the two-hour previous-AE automation has not already assigned an AE. | Manually retries or accelerates the shared previous-continuity backend action. The action assigns the previous AE through the checked AE path; selected previous-reviewer carry-forward is best-effort through the AE assignment process. |
| `Auto-assign action editor` | Non-conflicted Editors-in-Chief on the assignment page | Paper-specific assignment page. | Opens a ranked candidate preview. It does not change workflow state. |
| `Search action editors` | Non-conflicted Editors-in-Chief on the assignment page | Paper-specific assignment page. | Searches current Action Editors by name, email, institution, or OpenReview profile id. |
| `Assign selected action editor` | Non-conflicted Editors-in-Chief on the assignment page | After one eligible candidate is selected. | Submits the paper-specific AE assignment through the checked workflow path. |
| `Remove current Action Editor` and `Remove selected action editor` | Non-conflicted Editors-in-Chief on the assignment page | Only when a current handling Action Editor is assigned. | The checkbox confirms the requested removal, and the submit button removes the current handling AE before a different AE can be assigned. |
| `Assign reviewers` or reviewer-management actions | Handling Action Editor or EIC | Paper reviewer assignment surfaces after the paper is ready for reviewer assignment. | Adds, invites, or removes reviewers through checked reviewer-assignment paths. New assignments and invitations use the reviewer due date shown on the assignment surface. |

## Visibility Rules

- Before setup readiness, the pending row must not expose the paper-page link,
  `Assign Action Editor`, or `Auto-assign previous AE/reviewers`.
- `Create assignment pages` is setup only. It must be safe to retry and must not
  create duplicate active assignments.
- Eligible resubmissions schedule a separate two-hour previous-AE continuity
  check. It submits the same backend action as the EIC retry button, runs only
  after assignment setup is ready and no AE has already been assigned, and uses
  previous-AE assignment as the success criterion. Selected previous-reviewer
  carry-forward may follow best-effort.
- Setup readiness should be visible to Editors-in-Chief from the assignment
  workflow so they can continue with the correct paper-specific assignment
  action.
- While setup is in progress, failed, or stale, assignment controls remain
  hidden. EICs should wait for readiness or use `Retry setup` when offered.
- For eligible resubmissions, the pending row should show
  `Auto-assign previous AE/reviewers` instead of also showing a generic
  `Assign Action Editor` row button until previous-AE continuity succeeds.
  Manual fallback is through the paper page.
- Authored or conflicted EICs must not see operational assignment controls for
  that paper.
- Candidate preview and search do not assign anyone. Only
  `Assign selected action editor` mutates the handling AE assignment.
- If a paper already has a handling AE, the EIC must use
  `Remove current Action Editor` and submit `Remove selected action editor`
  before assigning a different AE.
- Backend assignment checks remain authoritative even when a browser row looks
  selectable.

## Permission Matrix

Assignment-page permission is paper-specific. A role may have journal-wide
responsibility and still be denied assignment controls on an authored or
conflicted paper.

| Surface | Allowed Roles | Must Hide Or Block |
| --- | --- | --- |
| EIC Pending Tasks setup row | Non-conflicted Editors-in-Chief. | Authors, reviewers, Action Editors, Production Editors, signed-out users, and authored or hard-conflicted EICs. |
| Paper-page assignment launcher | Non-conflicted Editors-in-Chief after setup readiness. | Everyone before setup readiness; authored or hard-conflicted EICs; ordinary authors, reviewers, AEs, PE, and public users. |
| Action Editor assignment page | Non-conflicted Editors-in-Chief. | Direct links from denied roles must not expose candidate lists, search results, submit controls, or paper-private assignment signals. |
| Reviewer assignment page | Handling Action Editor and non-conflicted Editors-in-Chief while reviewer assignment is active. | Authors, ordinary reviewers, Production Editors, public users, conflicted operational roles, and post-decision paper states. |
| Resubmission continuity assignment | Non-conflicted Editors-in-Chief when prior eligible participants exist. | Ordinary new submissions, resubmissions without eligible continuity candidates, and any authored or hard-conflicted EIC context. |

Denied users may see public or role-appropriate paper content, but they must not
see assignment candidate lists, hidden eligibility signals, selected-candidate
state, assignment submit controls, operational setup notes, or paper-private
reviewer and AE identity details.

## Candidate Visibility And Selection

- Candidate tables may show names, institutions, role status, load,
  availability, cooldown, matching or affinity signals, and conflict status when
  the viewer is allowed to assign for that paper.
- The AE candidate pool is track-specific: OSS submissions show OSS Action
  Editors, and regular submissions show regular Action Editors.
- Candidate rows must explain why a person cannot be selected when the reason
  is known, such as unavailable, inactive, at load limit, in cooldown, not in
  the required role, or hard author conflict.
- Hard author conflicts from paper authors, author identifiers, normalized
  author-list matches, or declared conflicts are not selectable.
- OpenReview-positive conflicts are warning states, not hard author conflicts.
  They may be selectable only through the explicit override path shown to the
  allowed EIC or AE role.
- Availability, cooldown, load, and role membership problems are not conflict
  overrides. They remain blockers or disabled states when the workflow says the
  candidate is not eligible.
- Candidate preview, search, and selection state are private operational
  information. Authors, reviewers, PE, public users, and unrelated signed-in
  users must not see it.

## Direct Links And Role Context

- Opening an assignment page directly must apply the same role and paper
  permission checks as opening it from a console or paper page.
- Links from EIC and AE consoles must preserve the active role context so a
  multi-role user does not accidentally see or submit using the wrong role.
- Active Papers and status tables may link to the paper page for inspection,
  but they must not bypass setup readiness or checked assignment controls.

## Reviewer Assignment Page Rules

- Reviewer assignment starts from the paper-specific reviewer assignment page,
  not from a raw role-administration page or unchecked assignment surface.
- The reviewer assignment page may use a structured Edge Browser-backed
  contract to identify the checked assignment source, candidate evidence, and
  filter semantics, but staff should continue to see the JMLR reviewer hub.
- Reviewer assignment controls should live on the reviewer assignment page.
  The paper forum must not show reviewer-assignment launchers or inline
  controls that add or remove reviewer assignments.
- Existing-reviewer assignment candidates follow hard-conflict,
  advisory-conflict, availability, load, cooldown, and backend-authoritative
  rules. External email invitations are checked for known conflicts and existing
  JMLR reviewer membership, and after acceptance may bypass standard reviewer
  max-load and cooldown checks.
- Assign previous reviewers, auto-assign reviewers, search reviewers, and invite
  new reviewer flows use the `Review due date` selected on the reviewer
  assignment page.
- Existing assigned reviewers, pending external requests, accepted external
  reviewers, declined responses, and expired requests should be shown only
  to allowed operational roles.
See [OpenReview Model](openreview-model.md) for the platform terms behind paper
pages, role pages, assignment records, and checked workflow actions.

## Validation

Run `python3 scripts/check_tree.py` after changing this page.
