# Paper Page Role/Stage Matrix

Paper page actions depend on the viewer role and paper stage. The table below
summarizes the behavior expected by reviewers and maintainers.

| Role | Stage | Expected Visible Actions | Must Hide |
| --- | --- | --- | --- |
| Author | Submitted before AE assignment | Submission status and allowed author communication. | EIC assignment controls, reviewer identities, reviewer-only content. |
| EIC | Submitted with no AE and no setup readiness | Assignment setup belongs in EIC Pending Tasks; the paper page should not yet expose `Assign Action Editor`. | Paper-page assignment launcher before setup readiness. |
| EIC | Setup-ready submitted paper | `Assign Action Editor` paper-specific launcher and allowed decision/intervention actions. | Assignment controls for authored or conflicted papers. |
| Action Editor | Assigned paper under review | Review monitoring, contact/comment, reviewer-specific rating actions for submitted reviews, and decision actions when available. Reviewer assignment and removal happen on the paper-specific assignment page. | Paper-level reviewer-rating launcher before decision approval, EIC-only setup, reviewer-assignment launchers, and role-management controls. |
| Reviewer | Assigned paper under review | Submit or read/edit own review when allowed, contact AE, and paper material needed for review. | Other reviewer identities, AE/EIC operational controls, author-only actions. |
| Production Editor | Camera-ready approved or publication stage | Download publication files, publication handling, and published-state controls when available. | Earlier editorial assignment/review controls. |
| Unrelated signed-in or signed-out user | Any pre-publication OpenReview paper-page stage | No OpenReview paper-page actions or restricted paper content. When OpenReview publication is enabled, a paper becomes publicly readable only after Mark as Published. | Paper content before OpenReview publication, released decisions/reviews, unreleased reviews, reviewer identities, assignment controls, and restricted paper records. |

Role-specific behavior should stay consistent across direct paper links, console
links, and paper-page action buttons.

## Assignment And Reviewer-Management Visibility

- Assignment setup is not a paper-page action before readiness. The only
  visible setup entry is the EIC Pending Tasks `Create assignment pages` row for
  a non-conflicted EIC.
- After setup readiness, the paper page may expose the paper-specific AE
  assignment launcher when allowed. Reviewer assignment launchers should not be
  shown on the paper forum; handling AEs and non-conflicted EICs use the
  reviewer assignment page from their role console or assignment-page link.
- Authors, ordinary reviewers, Production Editors, unrelated signed-in users,
  signed-out users, and authored or hard-conflicted operational roles must not
  see assignment candidate lists, selected-candidate state, reviewer-management
  submit controls, or hidden setup notes.
- Direct paper links must enforce the same visibility as console links. A user
  who cannot reach an assignment page from the console must not gain assignment
  controls by opening the paper page or assignment page URL directly.

## Public And Non-Participant Visibility

- Before Mark as Published, JMLR does not use the OpenReview paper page as the
  public publication surface.
- Public users and unrelated signed-in users should not see OpenReview
  restricted paper content, released review records, released decision records,
  paper files, assignment state, or workflow actions.
- When OpenReview publication is enabled, Mark as Published makes the
  OpenReview paper record and public files readable by everyone.
- Journal website/export handling remains a separate workflow.

See [OpenReview Model](openreview-model.md) for the platform terms behind paper
pages, records, roles, and visibility.
