# Camera-Ready Revision

Accepted papers move through author preparation and Action Editor verification
before the final public OpenReview record is created.

## Author Preparation

| Material | Requirement |
| --- | --- |
| Final PDF | Required for every track. Upload the final JMLR manuscript. |
| Supplementary material | Optional for every track. Upload at most one PDF or ZIP file. |

The camera-ready form contains only the two material fields above. Revision
summaries and correction requests use Official Comment rather than another form
field. OSS uses this same form: it has no separate code upload, required source
archive, video field, or OSS-specific material field. An author may use the
optional ZIP supplement for software, but the workflow does not require it.

The optional structured `code` project or repository URL is submission
metadata, not a third camera-ready material field. It is available to every
track and need not appear in the final PDF or supplement. The exact website
export contract is owned by [Publication](publication.md).

Authors prepare the final PDF with the OpenReview-specific JMLR style file
`docs/reference/jmlr-style/jmlr_or.sty`. The paper's Camera Ready Revision form
provides the generated `\jmlropenreviewdates{...}` block. Authors use that block
exactly as provided and do not write a manual `\jmlrheading{...}` or
`\editor{...}` call.

The official [JMLR Author Guidelines](https://www.jmlr.org/format/authors-guide.html)
are the common reference for authors and Action Editors. The configured
`website_urls.camera_ready_author_guidelines` value owns this URL and defaults
to that page in every environment. Decision and camera-ready messages provide
general JMLR formatting guidance, include the configured Author Guidelines link, and direct the author
or Action Editor to the paper form for the exact dates, publication identifier,
footer URL, and generated block. The Camera Ready Revision and Verification
forms display the paper-specific values. Where the general page differs from
those paper-specific OpenReview instructions, the OpenReview instructions
govern this workflow. In particular, the author uploads the final PDF and
optional supplement defined above, uses the generated metadata and `jmlr_or.sty`,
and does not add a manual heading or Editor line.

The generated block supplies the submitted, revised, and accepted dates, the
JMLR publication identifier, and the metadata needed for the JMLR first-page
heading, page range, and footer. Author names and affiliations remain ordinary
manuscript content.

The camera-ready lifecycle retains its standard revision, verification,
acceptance, release, and final public-record transitions. JMLR adds only the
two-field material form and the paper-specific instructions displayed by the
Camera Ready Revision and Verification actions.

## Decision-Specific Instructions

| Decision | Author action | Action Editor check |
| --- | --- | --- |
| Accept as is | Upload the formatted final PDF and optional supplement by the stated deadline. An Official Comment is optional. | Check the JMLR format and final material. |
| Accept with minor revision | Address the requested changes, upload the revised final PDF and optional supplement, and post a restricted Official Comment summarizing how the decision comments were addressed. | Check both the requested minor revisions and the JMLR format. Reviewers do not re-review the paper. |

For a minor revision, the author sends the summary through the paper's Official
Comment action. The author selects the paper Authors and Action Editors;
Editors-in-Chief also remain readers. The author does not select Reviewers
or public readers.

## Action Editor Verification

The Action Editor checks the latest uploaded PDF against the same JMLR format
instructions and configured Author Guidelines given to the author:

- uses `jmlr_or.sty`;
- contains the exact paper-specific `\jmlropenreviewdates{...}` block displayed
  in the verification form;
- renders the displayed volume, year, submitted date, revised date, published
  date, publication identifier, `1–last page` range, and paper-specific JMLR
  URL;
- renders the JMLR copyright and CC-BY 4.0 footer;
- does not render an Editor line.

The paper-specific JMLR URL is the publication attribution URL, not the
optional project or repository URL. The verification check derives its expected
`/papers/v<volume>/<paper_id>.html` path from the same generated volume and
publication identifier used in the PDF. It permits only the established
HTTP/HTTPS and `www` redirect variants and does not rely on a visual comparison
for URL identity.

Regular, OSS, and Award papers use this same PDF format and verification
contract. OSS does not add an MLOSS label to the PDF. Requirements on the
external MLOSS website for a repository or source archive are legacy website
instructions and do not make either the structured `code` URL or supplement
mandatory in OpenReview.

The verification form displays these values rather than asking the Action
Editor to infer them. It also displays the accepted OpenReview title and asks
the Action Editor to confirm that the PDF matches the accepted paper except for
camera-ready formatting and any explicitly approved minor revisions. It does
not ask the Action Editor to compare or approve a separate author list.

For an `Accept with minor revision` decision, the Action Editor also reads the
author's revision-summary Official Comment and verifies the requested changes.

Camera Ready Verification approves the latest camera-ready material. If a
correction is needed, the Action Editor does not approve it. The Action Editor
posts a restricted Official Comment to the paper Authors explaining the needed
correction. The author uploads a corrected PDF, and the Action Editor then
checks the latest upload.

Approval creates the final public OpenReview record and hands the final PDF and
optional supplement to the JMLR production workflow. It does not alter earlier
reviews or the editorial decision.
