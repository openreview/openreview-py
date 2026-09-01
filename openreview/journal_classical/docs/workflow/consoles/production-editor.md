# Production Editor Console

The compact Production Editor console is a private worklist derived from
accepted public final records.

| Tab | Contents |
| --- | --- |
| Pending | Ready items plus the visible remaining count. |

Every row shows the paper number and title, worklist state, public OpenReview
record, private PE/EIC publication bundle, one editable JMLR publication URL,
and one **Mark published** action. The URL must use `/papers/v<volume>/`, not
`/papers/volume<volume>/`. After the Published write succeeds, the console
removes the paper from the pending worklist and updates the remaining count.
The downloadable `publication.json` contains only the predicted HTML URL in
`public_urls.abstract`; it does not predict an external final-PDF URL. The
Production Editor publishes the separately downloaded private final PDF.

Production Editors and Editors-in-Chief may use the worklist. It has no review,
assignment, decision, camera-ready verification, recruitment, role-management,
or OpenReview publication/retraction controls. An approved accepted-paper
retraction removes the root from this worklist and sends one manual external
follow-up notice; it does not rewrite the retained private handoff ledger.
