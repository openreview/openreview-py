# Accepted-Paper Retraction

This page owns the JMLR OpenReview behavior for an author request to retract an
accepted paper. Retraction of an external jmlr.org page remains a separate
manual Production Editor action.

## Browser Workflow

| Step | Role and rendered control | Visible and persisted effect |
| --- | --- | --- |
| Request | A paper author opens the accepted paper, clicks `Retraction`, confirms the venue policy, optionally comments, and submits. | The request is visible to Authors, the handling Action Editors, and Editors-in-Chief. A standard paper-scoped `Retraction_Approval` task appears for EICs. |
| Review | An EIC follows `Review retraction` from Pending Tasks, clicks `Retraction Approval`, selects `Yes` or `No`, optionally comments, and submits. | The task disappears. The author request is released to `everyone`; the EIC response remains readable by Editors-in-Chief, the paper Action Editors, and the paper Authors. |
| Approve (`Yes`) | EIC approval of the author request. | The public retraction record is released, the root becomes `JMLR/Retracted_Acceptance`, and Authors receive the standard decision message. Production Editors receive exactly one JMLR follow-up notice. |
| Decline (`No`) | EIC declines the author request. | The accepted root remains accepted. Authors receive the standard decision message. No JMLR Production Editor retraction notice is sent. |

Only an author of an accepted paper may create the request. Only an EIC may
approve or decline it. A Production Editor may see publication controls but
cannot see or invoke either editorial retraction control.

After completion, the released author request is public. The approval remains
visible only to the paper Authors, its assigned Action Editors, and the EIC
group; Production Editors, unrelated signed-in users, and guests cannot read
it. The completed paper exposes neither `Retraction` nor `Retraction Approval`.
These visibility and task-removal outcomes must persist after refresh.

## Publication Handoff

The private `Publication_Status` note is immutable historical handoff state. A
retraction does not rewrite a retained `Ready` or `Published` value and does not
invent a `Retracted` publication status.

Once a root is retracted:

- it disappears from the pending Production Editor worklist because it is no
  longer an accepted record;
- a stale rendered `Mark published` submission fails the server-side accepted
  record check and cannot change the private status or saved external URL; and
- the one Production Editor notification asks the human operator to reconcile
  the external jmlr.org publication manually.

A declined request leaves the accepted paper eligible for its ordinary private
publication handoff.

OpenReview does not edit or retract the already published external jmlr.org
HTML or PDF. Production Editors perform that external follow-up manually.

## Retry Contract

The JMLR postprocess sends a Production Editor group notice only after a `Yes`
outcome has produced the retracted root. It includes a stable callback-edit
marker and reads back that exact event before and after delivery. Group fan-out
may store one recipient row per PE, but all rows from the one logical delivery
share one `requestId`. A retry after a timeout that occurred after persistence
therefore leaves exactly one logical delivery, while a later post-acceptance EIC
revision of the same paper remains a distinct event. Multiple request IDs for
one event, missing event identity, or an approval whose native root never
settles as retracted fails closed.

Static checks live in
`tests/source/test_production_change_notification.py`; browser/live coverage
must use the rendered author and EIC forms and secondary read-only state and
message checks.
