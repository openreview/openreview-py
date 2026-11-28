# Reviewer Assignment

Reviewer assignment is a checked paper-specific workflow. The handling Action
Editor and Editors-in-Chief may add, invite, or remove reviewers when the paper
state allows it.

| Control | Effect |
| --- | --- |
| Assign reviewers | Shows current reviewers and ranked candidates, then applies explicit assignments. |
| Search reviewers | Searches existing JMLR reviewers by name, email, or OpenReview profile id, then assigns selected eligible reviewers only after explicit submit. |
| Manual reviewer assignment | Adds eligible reviewers through checked assignment, using the reviewer due date shown on the assignment surface. |
| Invite external reviewer | Sends a paper-specific reviewer request when allowed, using the reviewer due date shown on the assignment surface. |
| Remove reviewer | Before decision, removes or expires an active reviewer assignment from the assignment status table when the reviewer has not submitted a review. |
| Previous reviewers | On a linked resubmission, lists each qualifying immediately previous reviewer by a profile-safe name with an explicit `Assign previous reviewer` action. |
| View previous paper and its reviews | Opens the validated immediately previous forum in the current OpenReview environment. The linked-resubmission process grants the current paper-scoped AE group read access to submission, decision, and review records throughout the validated prior chain. |
| Browse all reviewers | Opens the ordinary reviewer browser with its unchanged generated URL. |

Existing-reviewer assignment checks include role eligibility, paper conflicts,
availability, active load, and paper state. A validated prior reviewer may
bypass only the ordinary active-load limit through the dedicated continuity
action; the checked backend still enforces every other gate. External invite
acceptance still uses OpenReview's authoritative conflict,
identity/membership, and availability checks, but retains its established load
exception. Direct mutation of reviewer groups is not an ordinary user workflow.

If affinity scores are missing, they may still be processing. The Action Editor
may return later for ranked recommendations or select a reviewer now. Every
assignment is checked against current conflicts, availability, and reviewer
load when submitted.

For a linked resubmission with a validated, readable immediately previous
forum, the launcher uses this exact order:

1. The heading `Previous reviewers`, when at least one qualifying name exists.
2. A list of the qualifying names with one explicit `Assign previous reviewer`
   action per name, when any exist.
3. The note `OpenReview permissions determine whether you can view the previous
   paper and its reviews.`
4. One link labeled `View previous paper and its reviews`.
5. The separate generic action `Browse all reviewers`.

The dedicated action submits the same global reviewer-assignment edge
as the native browser, signed by the paper's anonymous Action Editor identity.
It exists because the standard Edge Browser disables candidates at their ordinary
load limit before JMLR's backend can recognize a prior-reviewer continuity
exception. The action does not change the reviewer's configured load. Current
membership, OpenReview conflict result, availability,
duplicate-assignment, and paper-state checks remain authoritative; only the
documented prior-reviewer active-load gate is bypassed. `Browse all reviewers`
retains the unchanged browser and normal load behavior for every other
candidate.

The launcher derives assignment state from active global reviewer-assignment
edges every time it is prepared. A qualifying previous reviewer who is already
assigned is rendered with a disabled `Assigned` button and the status `Previous
reviewer assigned.` Reloading the page must not expose another assignment action
or submit a duplicate edge.

Every active reviewer assignment should receive a stable numeric reviewer label
such as `Reviewer 1`; the assignment process repairs that metadata when needed.

The required reviewer count is paper-specific. If no paper-specific value has
been set, JMLR uses the venue default. Changing the count updates assignment
progress, review-release readiness, decision reminders, and console progress
for that paper. The required reviewer count is an integer from 1 to 5, and the
assignment surface prevents more than 5 active reviewer assignments.

The reviewer due date for new reviewer assignments and external reviewer
requests is chosen on the reviewer assignment surface. It defaults from the
configured review period and may be adjusted before submitting new assignments
or invitations. Auto-assign reviewers, search reviewers, and invite new
reviewer flows all use this review due date.

## Multi-reviewer Assignment Batches

Multi-select reviewer assignment uses sequential behavior:

1. Process one selected reviewer at a time.
2. Verify the active global individual assignment edge and membership through an
   anonymous reviewer group listed in the paper's root `Reviewers` group.
3. Record that reviewer as `Verified` or `Failed` before starting the next
   selected reviewer. A failure does not stop later reviewers from being
   attempted.
4. After every selected reviewer has a terminal outcome, report the batch as
   `complete`, `partial`, or `failed` and identify each reviewer outcome.

The UI must not claim that all selected reviewers were assigned unless every
reviewer is verified. The submit control remains busy until the batch reaches a
terminal result. Source tests execute an initial reviewer failure followed by
later successes, and managed browser validation checks the same edge and group
membership contract.

## Visibility And Permissions

- The reviewer assignment entry is available only to the handling Action Editor
  and non-conflicted Editors-in-Chief while reviewer management is active.
- Direct URLs must enforce the same role, conflict, and paper-stage checks as
  console and paper-page navigation.
- Denied users may see public or role-appropriate paper content, but must not
  see reviewer candidate lists, selected-reviewer state, external-request
  private status, reviewer identity metadata beyond their allowed role, or
  submit controls.
- Raw role-administration views and unchecked assignment tools are not the
  ordinary reviewer-management workflow.

## Candidate And Status Display

- Candidate rows should show enough status for the editor to understand the
  choice: reviewer identity, affiliation, eligibility, availability, active
  load, matching signal when available, and conflict status.
- Qualifying previous reviewers are deduplicated by profile id and shown using
  profile name fields only, with one explicit continuity assignment button.
  Duplicate display names include profile ids, and missing names fall back to
  profile ids. Names are never derived from email addresses, and reviewer email
  addresses are never shown.
- `View previous paper and its reviews` uses the current environment's forum
  route for the validated immediately previous forum. On submission and before
  every later AE assignment, an idempotent reader bridge adds the current
  paper-scoped AE group to every prior submission, decision, and review in the
  validated linked chain. It never changes historical paper-group membership
  or record content.
- Initial submissions and papers with absent, invalid, or unreadable history
  retain only `Browse all reviewers`, without an empty heading, access note, or
  warning. If the immediately previous forum is validated and readable but has
  no qualifying reviewer names, omit the heading and name list but retain the
  access note, previous-paper link, and generic browser action.
- Candidate rows must not expose reviewer email addresses in the assignment
  table.
- OpenReview's conflict detection, including author conflicts, is authoritative. JMLR
  does not parse author or declaration fields and does not define separate
  conflict classes.
- A conflict result follows the native assignment surface. If that surface
  exposes a supported explicit override, only the authorized AE or EIC may use
  it; JMLR does not create another override policy.
- Existing assigned reviewers, pending external requests, accepted external
  reviewers, declined responses, conflict-detected responses, and expired
  requests should remain visible to allowed operational roles so the paper's
  reviewer state is auditable.
- Search, preview, and selecting candidates do not mutate reviewer assignment.
  Assignment changes require an explicit submit action.
- Reviewer removal is a reviewer assignment surface action. It should not appear
  as a standalone root paper-page action.
- Reviewer removal is available only before decision while reviewer management
  is active.
- Reviewers who have already submitted a review are not removable through
  reviewer assignment.

## External Invitations And Eligibility

- External assignment and acceptance use the authoritative OpenReview
  conflict result. JMLR does not derive another result from paper fields.
- External reviewer invite links should resolve to Accept or Decline outcomes
  for the intended invitee. Accept should assign only the resolved eligible
  profile; an unresolved or conflict-blocked acceptance should not create a raw
  email assignment. Decline should record a declined response without assigning
  the invitee.
- Repeated or contradictory invite responses should follow the visible active,
  expired, accepted, or declined state instead of creating duplicate reviewer
  assignments.
- External reviewer responses are bound to the exact emailed invite record.
  The invited email remains the durable invite identity even after OpenReview
  resolves the accepting profile, and arbitrary email addresses must not be
  inserted as response-note readers.
- Accept requires an active logged-in OpenReview profile. If the profile does
  not list the invited email, JMLR records an identity-linkage warning while
  retaining the invited email on the edge. An unresolved Accept is not recorded
  as pending sign-up and does not send a follow-up email.
- External invitations expire after the configured no-response interval without
  reminder email. Declining an invitation must not remove a reviewer assignment
  created independently of that invitation.
- If acceptance cannot finish its reviewer-assignment update, the recorded
  response remains historical and JMLR sends a fresh external invitation. The
  replacement has a new response link; a previously consumed link is not
  reopened or reused.

See [OpenReview Model](../openreview-model.md) for platform terms that may
appear in troubleshooting or validation evidence.
