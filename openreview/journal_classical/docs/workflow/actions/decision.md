# Decision

Decision actions record the editorial outcome for a paper.

| Area | Behavior |
| --- | --- |
| Decision form | Used by the handling Action Editor or EIC role when the paper state allows a decision. |
| Pre-AE EIC rejection | Before the first Action Editor assignment, the EIC paper-page `Decision` form is narrowed to `Reject without resubmission` with editable comments. |
| Post-AE decisions | After the first Action Editor assignment, EIC and handling AE use the normal Decision form with all configured editorial outcomes. |
| Early rejection | After AE assignment, early rejection uses the normal decision action; it should not require a separate `Desk Reject` button on the AE paper page. |
| Author notification | Released decisions become visible to authors and trigger the configured decision communication. |
| Follow-up actions | The decision controls whether resubmission, camera-ready revision, or publication preparation can proceed. |

## Decision Rules

- Decisions should be submitted only by the handling Action Editor or an
  allowed Editor-in-Chief role while the paper state permits a decision.
- The pre-AE EIC Decision form is only for terminal suitability rejection. It
  should offer `Reject without resubmission` only.
- After an Action Editor has been assigned, both EIC and handling AE decision
  access should use the normal outcome set: `Accept`, `Accept after minor
  revisions`, `Reject with encouragement to resubmit`, and `Reject without
  resubmission`.
- A submitted decision is the durable editorial outcome for that round. Later
  workflow actions should follow the decision result rather than creating a
  second competing outcome.
- Early rejection uses the same Decision action and should not introduce a
  separate desk-reject path.
- Decision release controls the author-visible outcome, any allowed
  resubmission path, camera-ready eligibility, and whether reviewer rating or
  follow-up editorial tasks become available.
- Reviewer ratings are optional editorial metadata after review work; they are
  not a separate author-facing or reviewer-facing decision.
