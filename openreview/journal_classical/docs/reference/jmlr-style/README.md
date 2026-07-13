# JMLR Style References

This directory stores reference LaTeX style files used while designing the OpenReview camera-ready workflow.

`upstream/jmlr2e.sty` and `upstream/sample.tex` are downloaded from the public JMLR style-file repository and should be treated as upstream reference material.

`jmlr_or.sty` is the draft OpenReview-specific variant. It is based on upstream `jmlr2e.sty`, removes the rendered editor line, loads `lastpage` for page-range inference, and adds helpers for OpenReview-generated submitted/revised/accepted dates plus the final JMLR publication id. `\jmlropenreviewdates{...}` installs the JMLR title-page heading automatically, deriving year, volume, pages, dates, and the rendered `YY-XXXXX` paper id from the generated metadata block. That id is derived from the accepted year and the last five digits of the OpenReview paper number. Author names and publication order remain normal JMLR manuscript metadata controlled by the authors; the heading author string comes from the existing `\ShortHeadings{...}{...}` author argument.

`sample_or.tex` is the draft OpenReview-specific sample. It uses `jmlr_or.sty`, the generated `\jmlropenreviewdates{...}` block, normal `\title` and `\author` metadata, and no manual `\jmlrheading{...}` or `\editor{...}` call.
