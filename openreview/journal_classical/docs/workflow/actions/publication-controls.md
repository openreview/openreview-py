# Publication Download Bundle

The publication download is a read-only file handoff for Production Editors
after camera-ready verification has made the final OpenReview record public.
The private worklist tracks the later manual JMLR website publication without
changing that OpenReview record.

## Download Behavior

- The handoff email links directly to the Production Editor worklist, which
  provides the allowed download entry point.
- Downloading is read-only and does not change assignment, review, decision,
  camera-ready, or public-record state.
- The bundle contains the final PDF, optional supplementary material when
  present, and `publication.json`.
- The page fetches private files with the signed-in PE/EIC session and exposes
  ordinary browser downloads. The downloaded files use `<publication-id>.pdf`,
  `<publication-id>-supplement`, and `publication.json`.
- **Open public OpenReview record** navigates to the exact paper forum and does
  not change publication state.

## Visibility And Files

- Only current Production Editors receive the production handoff.
- A missing supplement does not make the download fail.
- The private Ready/Published record stores the OpenReview file references for
  PE/EIC readers. The public submission is not made private or rewritten.
- The private status records external work as Ready or Published; it is not an
  OpenReview publication or retraction control.

## Validation

The Row 16 managed-browser case clicks every rendered link, verifies the final
PDF starts with the PDF signature, parses `publication.json`, downloads the
supplement when present, and follows the public-record link. Row 17 then clicks
**Mark published**, checks that the pending row disappears, and confirms the
public OpenReview record did not change.
