# JMLR OpenReview Lifecycle

This page summarizes the workflow states and role handoffs for JMLR submissions
in OpenReview.

## Main Stages

| Stage | Primary Roles | Expected Behavior |
| --- | --- | --- |
| Submission | Authors, Editors-in-Chief | Authors submit the paper PDF, metadata, author list, affiliations, OpenReview profile ids or emails, conflicts, cover-letter context, optional supplementary material, Open Source Software selection, and optional previous-submission information. Editors-in-Chief monitor new submissions and create assignment pages before assignment controls appear. |
| Action Editor assignment | Editors-in-Chief, Action Editors | Editors-in-Chief use the setup-ready assignment page to assign a handling Action Editor. Once assigned, the paper moves out of the new-submission task list and into active handling. |
| Review assignment | Action Editors, Reviewers | Action Editors invite or assign reviewers, manage reviewer availability, and monitor review completion. |
| Review and decision | Reviewers, Action Editors, Editors-in-Chief, Authors | Reviewers submit reviews. Action Editors prepare recommendations or decisions according to the visible paper stage and available forms. Authors see released decisions and allowed follow-up actions. |
| Resubmission | Authors, Editors-in-Chief, Action Editors, Reviewers | A rejected paper may have one direct resubmission path when the decision permits it. Previous-round context is shown only to roles that need it for the new round. |
| Camera ready | Authors, Action Editors, Production Editors | Accepted papers move through camera-ready revision, verification, and publication preparation. |
| Publication | Production Editors, Authors | Production Editors complete publication handling and authors see the final publication status. |

## Action Owners

| Visible Action Or State | Rule |
| --- | --- |
| Create assignment pages | Prepares paper-specific assignment surfaces before assignment controls are used. |
| Assign Action Editor | Assigns a handling Action Editor through checked paper-specific surfaces; changing an existing handling AE requires removing the current AE first. |
| Auto-assign previous AE/reviewers | Reuses eligible previous-round participants only for resubmissions where continuity is available. |
| Submit review | Collects review content from assigned reviewers and applies the configured visibility rules. |
| Decision | Releases the editorial outcome and follow-up actions allowed for the paper state. |
| Camera-ready revision | Collects final paper files and publication metadata after acceptance. |
| Mark as published | Records final publication handling after the camera-ready stage is complete. |

Detailed assignment-page behavior is described in [Assignment Pages And Buttons](assignment-pages.md).
Detailed action behavior is summarized in [Action Inventory](action-inventory.md)
and the pages under [Detailed Actions](../index.md#detailed-actions).

## Product And OpenReview Terms

Most lifecycle docs use product terms such as paper page, task, assignment,
record, role, and visibility. See [OpenReview Model](openreview-model.md) for
the platform terms that may appear in source review or troubleshooting.

## Submission And Resubmission Rules

- New submissions must include the required paper metadata, author list,
  conflict declarations, PDF, and configured optional files before downstream
  assignment and review state is created.
- JMLR review is single blind. Editors and reviewers can see author identities;
  authors must not see reviewer identities or hidden editorial assignment
  details.
- Resubmissions use the previous paper's eligible resubmission action. The
  previous author list and Open Source Software selection carry forward.
- Resubmissions may reorder authors, but must not add, remove, replace, rename,
  or otherwise change authors through the direct resubmission path.
- Paper communication and follow-up actions are visible only to the roles and
  paper stages that need them.

## Validation

Run `python3 scripts/check_tree.py` after changing this page.
