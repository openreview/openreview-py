# JMLR OpenReview Lifecycle

This page summarizes the workflow states and role handoffs for JMLR submissions
in OpenReview.

## Main Stages

| Stage | Primary Roles | Expected Behavior |
| --- | --- | --- |
| Submission | Authors, Editors-in-Chief | Authors use OpenReview's multi-profile author picker, choose Regular or a currently open managed track, upload the PDF and optional supplement, and provide the required submission metadata. Every track may also provide one optional structured project or repository `code` URL. New Regular papers recommend three Action Editors; managed-track papers and resubmissions do not. |
| Action Editor assignment | Action Editors | Ordinary papers enter the periodic track-aware batch. Editors-in-Chief use the standard Edge Browser only for exceptional immediate reassignment or a case missed by batching. |
| Review assignment | Action Editors, Reviewers | Action Editors invite or assign reviewers, manage reviewer availability, and monitor review completion. |
| Review and decision | Reviewers, Action Editors, Editors-in-Chief, Authors | Reviewers submit reviews. Action Editors prepare recommendations or decisions according to the visible paper stage and available forms. Authors see released decisions and allowed follow-up actions. |
| Resubmission | Authors, Action Editors | A rejected Regular paper may have a direct resubmission path when the decision permits it. The workflow immediately attempts previous-AE continuity, then falls back to the normal Regular batch; previous reviewers are not reassigned. |
| Camera ready | Authors, Action Editors | Accepted papers move through the shared camera-ready revision and verification path: final PDF required and one PDF-or-ZIP supplement optional for every track. Verification creates the final public OpenReview record. |
| JMLR website handoff | Production Editors | Production Editors receive a direct worklist link, use the private final-file bundle and `publication.json`, publish on the JMLR website manually, and privately record completion. |

## Action Owners

| Visible Action Or State | Rule |
| --- | --- |
| Periodic AE batch | Routes each unassigned paper through its track eligibility, global availability, and authoritative conflict checks. |
| Exceptional AE reassignment | Uses the standard Edge Browser after the current assignment is removed. |
| Immediate previous-AE continuity | Reuses the previous Action Editor when current base membership and conflict checks pass; it does not reuse reviewers. |
| Submit review | Collects review content from assigned reviewers and applies the configured visibility rules. |
| Decision | Releases the editorial outcome and follow-up actions allowed for the paper state. |
| Camera-ready revision | Collects the shared final PDF and optional PDF-or-ZIP supplement after acceptance. See [Camera-Ready Revision](actions/camera-ready-revision.md). |
| Production handoff | Creates a private Ready work item and emails Production Editors after the final record is public and its bundle is ready. Canonical track and website metadata are defined by [Publication](actions/publication.md). |

Detailed assignment-page behavior is described in [Assignment Pages And Buttons](assignment-pages.md).
Detailed action behavior is summarized in [Action Inventory](action-inventory.md)
and the pages under [Detailed Actions](../index.md#detailed-actions).

## Product And OpenReview Terms

Most lifecycle docs use product terms such as paper page, task, assignment,
record, role, and visibility. See [OpenReview Model](openreview-model.md) for
the platform terms that may appear in source review or troubleshooting.

## Submission And Resubmission Rules

- New submissions must include the required paper metadata, all authors through
  OpenReview's profile picker, a track, and a PDF. The optional
  supplement is limited to 10 MB. The structured `code` URL, cover letter, and
  supplement are optional for every track.
- `track_id` is the immutable OpenReview classification. The optional
  structured `code` URL is preserved through ordinary revisions, but does not
  classify a paper and is not a track-level website URL.
- JMLR review is single blind. Editors and reviewers can see author identities;
  authors must not see reviewer identities or hidden editorial assignment
  details.
- Resubmissions use the normal submission editor to create a new paper
  and forum. The editor identifies the action as a linked resubmission, shows
  the previous paper as a clickable read-only link, and shows the inherited
  Regular track as read-only context.
- A linked resubmission paper displays one server-derived `Previous JMLR
  submission` link to its immediate predecessor. New papers omit the field,
  and the display does not expand the earlier-paper chain.
- Camera-ready guidance must use the OpenReview-specific style reference `docs/reference/jmlr-style/jmlr_or.sty`, based on `docs/reference/jmlr-style/upstream/jmlr2e.sty`.
- OSS, Regular, and Award use the same final-PDF and optional-supplement
  contract. External legacy MLOSS repository and source-archive requirements
  do not add OpenReview fields or make those optional values mandatory.
- Paper communication and follow-up actions are visible only to the roles and
  paper stages that need them.

## Validation

Run `python3 scripts/check_source_assembly.py` and the focused lifecycle pytest
checks after changing this page.
