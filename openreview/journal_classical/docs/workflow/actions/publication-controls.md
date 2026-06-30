# Publication Download And Retraction Controls

Production Editor controls are permission-sensitive and stage-specific.

| Control | Role | Effect |
| --- | --- | --- |
| Download publication files | Production Editor | Downloads accepted publication material for production handling when publication export is enabled. |
| Retract publication | Production Editor | Opens the retraction confirmation path for a published paper when that action is available. |

Retraction is a destructive publication-state action and should require a clear
confirmation surface. These docs describe visible behavior; operator approval
and environment procedures are outside the source review surface.

## Download Behavior

- The download action belongs to the Production Editor publication workflow.
- The download action is available only when `publication_export_enabled` is true.
- Downloading files is read-only for the paper workflow: it should not change
  assignment, review, decision, camera-ready, publication, or retraction state.
- The downloaded set should contain the final publication material and metadata
  needed for production handling.

## Visibility And Files

- Download publication files should be available only for allowed
  non-conflicted Production Editors or Editors-in-Chief at the designed
  camera-ready-approved or publication stages when publication export is enabled.
- The download should include final paper material and publication metadata.
  When supplementary material exists, it should be available through the
  rendered publication/download path; when it does not exist, download should
  not fail because a supplement is missing.
- Published-row links should lead to the correct paper page or publication
  target without reopening review-stage workflow actions.
- Retraction confirmation should be visible only to allowed non-conflicted
  roles. Submitting retraction should move the paper into the designed
  retracted or terminal publication state without silently deleting publication
  output.
- A retracted paper should remain visible in the appropriate published or
  publication-status view so the retained history and final state can be
  inspected by allowed roles.
