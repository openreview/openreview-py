# Configuration Source Guide

The `site_config/` tree is the editable public JMLR delta over
This directory contains the editable JMLR venue policy and compatibility
behavior. The private integration repository owns
environment rendering and apply plans.

See [Site-Config Architecture And Ownership](architecture.md) for the exclusive
executable-source map, implementation boundary, and duplicate-risk inventory.

## Source Areas

| Path | Purpose |
| --- | --- |
| `site_config/openreview.json` | Venue-level settings, request fields, and global configuration values. |
| `site_config/global_settings/` | JMLR venue landing, EIC compatibility landing, Production Editor worklist, and JMLR-owned group data. |
| `site_config/invitations/` | Partial invitation definitions and callbacks for documented JMLR policy gaps. |
| `site_config/email_templates/` | Reachable JMLR policy messages and recruitment defaults. |
| `site_config/message_templates/` | Reusable non-email text and HTML inserted into workflow scripts or webfields. |
| `site_config/web_fragments/` | Executable JMLR browser fragments assembled into configured webfields. |
| `site_config/python_scripts/` | Source-owned process helpers included into OpenReview invitation scripts. |

## Invitation Paths

Invitation source paths use this shape:

```text
site_config/invitations/<group>/<invitation_name>/<section>/<file>
```

Common examples:

| Source prefix | OpenReview invitation |
| --- | --- |
| `site_config/invitations/venue/submission/` | `JMLR/-/Submission` |
| `site_config/invitations/venue/review/` | `JMLR/-/Review` |
| `site_config/invitations/venue/decision/` | `JMLR/-/Decision` |
| `site_config/invitations/reviewers/assignment/` | `JMLR/Reviewers/-/Assignment` |
| `site_config/invitations/action_editors/assignment/` | Checked JMLR Action Editor assignment behavior. |

Common section files:

| Source file | OpenReview section |
| --- | --- |
| `edit/reply.json` | Form schema, readers, writers, signatures, and instructions. |
| `edge/edge.json` | Edge invitation definition. |
| `process_functions/preprocess.py` | Validation before an edit is accepted. |
| `process_functions/process.py` | Actions after an edit is accepted. |
| `content_process_functions/process.py` | Meta-invitation content process script. |

## Global Settings And Templates

`site_config/global_settings/` owns only JMLR-specific data and compatibility
webfields. OpenReview provides the Author, Reviewer, Action Editor, and ordinary venue
role consoles. Important JMLR files are:

- `jmlr_meta.js`: venue-homepage compatibility plus linked-resubmission context.
- `jmlr_eic_compatibility_landing.js`: bounded five-tab EIC landing for the current API.
- `production_editor_console_webfield.js`: manual jmlr.org publication worklist.
- `groups/tracks.json`: ordered managed-track registry.
- `groups/production_editors.json`: private production-handoff role data.

`site_config/email_templates/` stores configurable workflow email bodies, grouped by recipient role:

- `author/*.txt`
- `ae/*.txt`
- `production_editor/*.txt`
- `journal_request/*.txt`

`site_config/message_templates/` stores reusable non-email text inserted into workflow scripts.

`site_config/web_fragments/` stores executable JavaScript fragments assembled
into a webfield but not independently applied. The previous-reviewer launcher
augments the reviewer Edge Browser without becoming a standalone
invitation or global setting.

## Venue Settings

`site_config/openreview.json` owns non-secret venue settings. The build helper
reads them with OpenReview content accessors before rendering environment
builds, then passes the resolved values into generated request-form snapshots,
webfields, and process scripts.

| Setting | Current value |
| --- | --- |
| `official_venue_name` | Configured full JMLR venue name. |
| `abbreviated_venue_name` | `JMLR` |
| `request_form.submission_public` | `false` |
| `request_form.author_anonymity` | `false` |
| `request_form.AE_anonymity` | `true` |
| `request_form.submission_license` | `CC BY-SA 4.0` |
| `request_form.number_of_reviewers` | `3` |
| `request_form.action_editors_max_papers` | `9` concurrent active papers |
| `request_form.reviewers_max_papers` | `2` (`3` on dev as a test fixture) |
| assignment / review / discussion / recommendation / decision periods | `1 / 8 / 2 / 2 / 1` weeks |
| camera-ready / verification periods | `4 / 1` weeks |
| archived Action Editors / reviewers | `true / true` |
| expert / external reviewers | `true / true` |
| expertise model | `specter+mfr` |

`tests/source/test_settings_contracts.py` validates these defaults and the
intentional dev-only reviewer fixture override.

## Build-Time Includes

Invitation templates can include placeholders rendered by the private
integration repository's `scripts/build/site_config.py`.

Common placeholders:

- `{{DEV_JOURNAL_ID}}` and `{{PROD_JOURNAL_ID}}`
- `{{SITE_URL}}`
- `{{REVIEWERS_MAX_PAPERS}}`
- `{{MESSAGE_TEMPLATE_JSON:path/to/template.txt}}`
- `{{PYTHON_SCRIPT_JSON:path/to/script.py}}`
- `{{PYTHON_SCRIPT_FILE:path/to/script.py}}`

Build-time include targets must stay inside their corresponding `site_config/` source areas. Uploaded OpenReview process code uses the generated script text and must not read repository files at runtime.

Deployment builds resolve the environment-specific support-request note id in
the private repository. Public-source validation must not require private ids or
an ignored local builder copy.

## Source Review Rules

- Keep user-facing labels, form fields, and side effects aligned with the workflow and role docs.
- Prefer focused source files for focused UI surfaces or process helpers.
- Keep policy-sensitive text in auditable template or config locations when practical.
- Do not edit generated output as source; update the editable files in `site_config/`.
- Keep build-time include targets in the tree when adding template, Python, or JavaScript placeholders.
- Public source must not contain credentials, private support-request IDs, or local operator secrets.

## Validation

Run these checks after documentation or source changes:

```bash
python3 scripts/check_source_assembly.py
python3 -m pytest -c source_pyproject.toml tests/source
```

`scripts/check_source_assembly.py` verifies required source areas, placeholder
targets, and source-ownership boundaries. The pytest command runs public source
contracts. The private repository separately validates rendered builds,
environment configuration, apply plans, and private documentation links.
