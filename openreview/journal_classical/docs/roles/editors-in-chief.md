# Editors In Chief

## Your Work

- Oversee journal-wide OpenReview operations.
- Move submitted papers into the checked assignment workflow.
- Assign or change handling Action Editors and inspect paper status.
- Manage reviewer, Action Editor, OSS AE, EIC, and production-editor roles.
- Intervene in paper workflows when needed.
- Review recruitment and operational changes before they affect the venue.

## Where To Go

Use the Editors-in-Chief Console for pending assignment setup, AE assignment, status views, role management, bulk invitations, and paper oversight.

The venue page also has an EIC-only People Management route for role membership
updates, role assignment-availability administration, and reviewer or Action
Editor recruitment. People Management must not be used as a paper assignment
path.
Recruitment and volunteer response behavior is described in
[Role Recruitment And Volunteer Responses](../workflow/role-recruitment.md).

Pending Tasks is the main queue for submitted papers with no handling AE. A new paper first shows `Create assignment pages`; after setup is ready, ordinary submissions show `Assign Action Editor`, while resubmissions may show `Auto-assign previous AE/reviewers` until previous-AE continuity is assigned.

## Main Actions

| Action | When to use it |
|---|---|
| Create assignment pages | Prepare the paper-specific AE and reviewer assignment pages for a submitted paper before assignment controls appear. |
| Assign Action Editor | Assign a handling AE, or use `Remove current Action Editor` before assigning a different one, through the checked paper-specific assignment page. |
| Auto-assign previous AE/reviewers | For eligible resubmissions, retry or accelerate the shared previous-continuity action. AE assignment is the success criterion; selected previous-reviewer carry-forward is best-effort. |
| Status views | Inspect papers, AEs, reviewers, and Top Reviewer recognition status. |
| Assign Roles | Update role membership and assignment availability. |
| Bulk Invite | Recruit reviewers or AEs after reviewing recipients and copy. |
| Paper actions | Intervene with assignment, reviewer management, decision, or camera-ready actions when appropriate. |

## Notes

Assignment setup is not an assignment. `Create assignment pages` prepares the paper-specific assignment surfaces and setup status.

While assignment setup is running, assignment controls stay hidden. If setup
fails or becomes stale, use `Retry setup` before assigning an AE.

For ordinary new submissions, use `Assign Action Editor` after assignment pages are ready. For resubmissions, the system also runs a two-hour previous-AE continuity check after submission once assignment pages are ready. Use `Auto-assign previous AE/reviewers` when it is offered to retry or accelerate the same backend continuity action; otherwise use the paper-specific assignment launcher.

Normal paper changes should use checked workflow actions. Broad paper-correction controls should not appear in normal production UI.

If you are an author or otherwise conflicted on a paper, you should not see operational controls or reviewer identities for that paper.

If you also hold another role, enter papers and assignment pages from the
Editors-in-Chief Console when acting as EIC. EIC assignment actions require the
editor-in-chief role context.

Production updates and repair require maintainer help and explicit production approval. Detailed assignment behavior is owned by the workflow docs.
