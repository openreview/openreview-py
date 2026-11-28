# Decision

Decision actions record the editorial outcome for a paper.

| Area | Behavior |
| --- | --- |
| Decision form | Used by the handling Action Editor or EIC role when the paper state allows a decision. |
| Pre-AE EIC rejection | Before the first Action Editor assignment, the EIC uses the paper-page `Desk Rejection` action. It records editable brief reasons and directly makes the submission terminal; it does not require a second EIC approval. |
| Assigned-AE suitability gate | Immediately after AE assignment, the handling AE uses Review Approval. `Appropriate for Review` begins review; `Desk Reject` requests separate EIC desk-rejection approval. |
| Automatic desk-rejection approval | The independent `automatic_desk_rejection_approval` setting is enabled by default. The AE still submits `Desk Reject` through Review Approval. After the native workflow creates the standard Desk Rejection Approval task, JMLR posts the standard EIC approval value automatically. When disabled, the EIC follows the genuine Pending Tasks link and approves or declines through the rendered form. |
| Post-review decisions | Once the review threshold is met, EIC and handling AE use the normal Decision form with all configured editorial outcomes. |
| Review threshold | The Decision action opens after 2 submitted reviews for a first submission in any track, or after 1 submitted review for a linked resubmission. Reviewer assignment still targets 3 reviewers. |
| Author notification | Released decisions become visible to authors and trigger the configured decision communication. |
| EIC approval | JMLR's `automatic_decision_approval` configuration is enabled by default. When enabled, a submitted AE decision completes normally, then posts the standard checked EIC approval value through Decision Approval. When disabled, the ordinary EIC approval task remains available. An EIC-authored Decision always uses that ordinary task and may be approved by the same EIC as a bounded authorized branch. |
| Follow-up actions | The decision controls whether resubmission, camera-ready revision, or publication preparation can proceed. |

## Decision Rules

- Decisions should be submitted only by the handling Action Editor or an
  allowed Editor-in-Chief role while the paper state permits a decision.
- Pre-AE `Desk Rejection` and post-review `Decision` are different
  actions and records. A direct EIC Desk Rejection is terminal, not a Decision,
  and creates no Decision Approval or resubmission path.
- Review Approval is the assigned-AE suitability gate. `Appropriate for Review`
  starts the normal reviewer-assignment workflow. An AE's `Desk Reject` always
  starts the standard EIC desk-rejection approval path. It never uses the
  direct pre-AE EIC Desk Rejection action.
- `automatic_desk_rejection_approval` is independent from
  `automatic_decision_approval`. When enabled, the Review Approval adapter must
  first let the native workflow successfully create the paper's standard
  `Desk_Rejection_Approval` invitation. It then uses the shared idempotent EIC
  approval helper to post exactly `I approve the AE's decision.` with the
  standard Editors-in-Chief signature and waits for the native approval
  process. It must not create the invitation, Desk Rejected state, or author
  notification itself. Exact readback includes invitation, forum, reply,
  signature, value, released AE recommendation, terminal state, and the single
  author notification.
- When automatic desk-rejection approval is disabled, the genuine EIC Pending
  Tasks link remains. `I approve the AE's decision.` makes the paper Desk
  Rejected and notifies authors. `I don't approve the AE's decision. Submission
  should be appropriate for review.` returns the paper to the normal
  Appropriate for Review path. An exact pre-existing manual approve or decline
  remains authoritative and is never overwritten. On retry, note existence is
  insufficient: the adapter requires the corresponding settled native outcome.
  Existing manual comments remain operator-authored; they are not required to
  match the automation comment. If an approved native attempt stopped before
  its non-idempotent notification, the adapter safely reruns that standard
  process; if the one notification already exists, it performs only idempotent
  invitation expiry. For decline, the standard Appropriate-for-Review note must
  itself settle the root to Under Review and create the reviewer-assignment
  invitation; an existing continuation with an unsettled root resumes that
  native continuation process rather than creating another response. Duplicate
  notifications, continuations, or malformed approval notes fail closed.
- After the review threshold is met, both EIC and handling AE Decision access
  should use the normal outcome set: `Accept as is`, `Accept with minor
  revision`, terminal `Reject`, and `Reject with encouragement to resubmit`.
  The last outcome uses `Reject` together with the visible
  resubmission checkbox; it alone creates the linked resubmission action.
- A first submission in any track requires 2 submitted reviews before the
  Decision action opens. A linked resubmission requires 1 submitted review.
  These thresholds do not reduce the automatic reviewer-assignment target of
  3 reviewers.
- A submitted decision is the durable editorial outcome for that round. Later
  workflow actions should follow the decision result rather than creating a
  second competing outcome.
- JMLR enables `automatic_decision_approval` by default. The automatic path
  must complete the Decision action before it posts anything. It
  then uses the checked `I approve the AE's decision.` value and normal
  Decision Approval invitation, EIC signature, validation, and process. It must
  not rewrite a per-paper Decision Approval invitation or duplicate the
  decision, release, rejection, camera-ready, task-expiry, notification, or
  acceptance transitions. Setting the configuration to `false` preserves the
  ordinary EIC approval task for controlled/manual approval.
- Automatic approval is a transition policy, not a second editorial decision.
  A retry must not create another approval for the same decision. If the native
  Decision process fails, the adapter must not post approval; if Decision
  Approval fails, the workflow reports that failure rather than synthesizing
  camera-ready state.
- A direct post-review EIC Decision does not enter AE-only automatic approval.
  The EIC follows the genuine `Review decision` Pending Tasks link and submits
  the native Decision Approval form. The same EIC may approve the Decision;
  this rare branch is intentionally covered by one acceptance-to-final smoke,
  not a separate outcome matrix.
- After any native manual approval of `Accept as is` or `Accept with minor
  revision`, the paper-scoped Decision Approval postprocess applies the same
  idempotent JMLR camera-ready guidance used by automatic approval. It removes
  `track_id`, preserves one guidance block, and fails if the exact invitation
  readback disagrees. A declined approval or rejection never changes the
  camera-ready form.
- Decision release controls the author-visible outcome, any allowed
  resubmission path, camera-ready eligibility, and whether reviewer rating or
  follow-up editorial tasks become available.
- After an accepted Decision Approval, the paper remains labeled
  `Decision pending for JMLR` until Camera Ready Verification posts the
  accepted record.
  During that intermediate state, authors must still see the active
  Camera Ready Revision action on the paper page.
- `Accept as is` and `Accept with minor revision` both direct authors to Camera
  Ready Revision on the same paper and state the configured deadline. For a
  minor revision, the Action Editor's decision comments define the requested
  changes. The author posts a restricted Official Comment summarizing how those
  changes were addressed, the Action Editor verifies the changes and final
  format, and reviewers do not re-review the paper.
- `Reject with encouragement to resubmit` directs authors to the paper page's
  Start Resubmission action, which creates a linked Regular-track submission
  and supplies the previous paper automatically. Terminal `Reject` creates no
  Resubmission action.
- Reviewer ratings are optional editorial metadata after review work; they are
  not a separate author-facing or reviewer-facing decision.
