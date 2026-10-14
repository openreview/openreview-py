# Publication

Camera-ready verification creates the final public OpenReview record. The final
paper, its allowed files, and the review record use the normal public
release behavior; JMLR adds no separate OpenReview publication gate or
lifecycle transition.

OpenReview does not show a canonical `jmlr.org` link. The JMLR website remains a
separate publication surface managed manually by Production Editors.

## Production Worklist

After the final OpenReview record is public and its download bundle is ready,
Production Editors receive an email linking directly to the private Production
Editor worklist. Each accepted final record begins in **Ready**. The worklist
shows only pending Ready items. Its private status record becomes **Published**
when the Production Editor completes the task.

The restricted bundle and this private completion ledger are both required
handoff records. Only papers with an explicit private status record appear on
the worklist; accepted historical records with no handoff record are never
silently labeled Ready. A bundle notification without the private status
history is not an equivalent replacement.

Each row links to the public OpenReview record and the private PE/EIC bundle.
The bundle contains:

- the final PDF;
- optional supplementary material, when present; and
- `publication.json` with the publication metadata already captured by the
  workflow.

The private status record carries the OpenReview final-PDF and optional
supplement references for PE/EIC readers. This lets the signed-in bundle page
create ordinary browser downloads without exposing those references publicly.

The final PDF and optional supplement use the shared material contract for
every track. The PDF uses the ordinary JMLR format, including for OSS papers;
it does not display an OSS or MLOSS track label. See
[Camera-Ready Revision](camera-ready-revision.md) for the material and PDF
verification rules.

## Publication Metadata

`publication.json` preserves OpenReview's canonical paper classification and
projects only the fields understood by the JMLR website.

| Field | Presence | Source and meaning |
| --- | --- | --- |
| `track_id` | Always | Exact immutable `track_id` from the final root submission. This rule applies to Regular, OSS, Award, and future managed tracks. |
| `special_issue` | OSS only | The literal value `MLOSS`, selected by the declared OSS publication policy. Regular and Award omit this field. |
| `extra_links` | When the optional structured `code` URL is present | The canonical JMLR website shape `[["code", URL]]`. Any track may provide this link. |

The structured `code` value is optional for every track and may identify a
public project page or source repository. The workflow exports that value
directly. It does not infer a link from the abstract, cover letter, manuscript,
or supplementary material, and it does not require the same URL to appear in
the PDF.

No display-name or track-level URL projection is part of the contract.
Configuration, the track registry, Track Management, and `publication.json`
must not export a duplicate track display name, `track_url`, or a generic track
`url`. The JMLR website derives its MLOSS collection from `special_issue`, not
from a display name, code link, or track website.

## Publication And Project URLs

Three link surfaces remain independent:

- `public_urls.abstract` is the generated, paper-specific JMLR publication
  page. Every final PDF renders this attribution URL in its footer.
- optional `code` is the paper-specific project or repository link exported as
  `extra_links`.
- links inside the manuscript are author-maintained manuscript content.

The Action Editor checks the footer URL deterministically against the paper's
generated publication identity. Its normalized path must be
`/papers/v<volume>/<paper_id>.html`, using the same volume and paper identifier
displayed for that PDF. Only the existing harmless HTTP/HTTPS and `www`
redirect variants are acceptable; the check does not compare the footer with
the optional `code` URL.

The current external MLOSS website text that requires a repository or a
source-code archive is legacy website policy, not an OpenReview requirement.
OpenReview permits an optional structured code link and an optional PDF-or-ZIP
supplement for every track. It requires neither for OSS.

Production Editors enter one JMLR publication URL after the manual website
publication, then select **Mark published**. The URL uses
`/papers/v<volume>/<paper>.html`; `/papers/volume<volume>/` is not accepted by
the worklist. After the Published write succeeds, the page removes the paper
from the pending worklist and updates the remaining count.

`publication.json` contains only the predicted public HTML page as
`public_urls.abstract`, using `/papers/v<volume>/<paper>.html`. It does not
predict or emit an external `public_urls.pdf` URL. The Production Editor
downloads the private final PDF from OpenReview and publishes that file
manually on the JMLR website.

These private worklist states do not publish, hide, retract, or otherwise edit
the already-public OpenReview final record or its files. The separate
[accepted-paper retraction](retraction.md) can retract that OpenReview record,
but OpenReview cannot publish, edit, or retract the external jmlr.org page.
