# Editorial Policies

These policies describe the stable behavior that JMLR OpenReview configuration
changes should preserve.

## Resubmission

- A paper may use one direct resubmission path only when the decision permits resubmission.
- Different rounds of the same work should preserve the paper title unless the editorial workflow explicitly changes it.
- Previous-round links and reviewer continuity are visible only where the role and paper stage require them.

## Assignment

- Editors-in-Chief use `Edit AE` from the compatibility landing or the standard
  Action Editor Edge Browser; JMLR does not create a second assignment page.
- Assignment controls should be visible only to roles that can use them for the current paper stage.
- Ordinary Action Editor assignment requires current base membership, current availability, and eligibility for the paper's immutable Regular or managed track.
- Track-eligibility changes affect future ordinary assignments. Validated
  previous-AE continuity first requires an active submission, a non-author
  authorized actor accepted by the native assignment surface, and no authoritative
  conflict; it may then proceed even when the previous AE is currently
  unavailable or not eligible for the current track.
  JMLR does not add a second Action Editor quota gate at final assignment.
- Prior-reviewer continuity is narrower: after its authoritative actor,
  paper-state, duplicate, conflict, membership, and availability gates pass,
  it may bypass only the ordinary active-reviewer load limit.

## Review And Identity

- JMLR review is single blind: editors and reviewers may see author identity,
  but authors must not see reviewer identity, Action Editor identity, reviewer
  assignment state, reviewer ratings, or hidden editorial operational records.
- Reviewer identity and single-blind visibility rules must remain stable across
  paper pages, role consoles, and released review content.
- Stale controls should disappear or report that they are no longer active instead of performing a second incompatible action.
- Repeated decline responses may remain available when the visible form still asks for a decline reason; accepting after decline should not silently reverse the declined state.

## Camera Ready And Publication

- Camera-ready verification creates the final public OpenReview record.
- OpenReview has no later publication gate for the external jmlr.org handoff.
  Its accepted-paper `Retraction` and `Retraction Approval` controls can retract
  the OpenReview accepted record; see
  [Accepted-paper retraction](actions/retraction.md).
- Production Editors receive a private worklist and download handoff by email,
  publish on the JMLR website manually, and privately record the external URLs
  and completion.
- OpenReview cannot edit or retract an already published external jmlr.org page;
  that follow-up remains manual.
