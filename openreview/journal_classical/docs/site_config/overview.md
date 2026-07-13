# Configuration Source Guide

The `site_config/` tree is the editable OpenReview venue configuration source.
It should be complete enough for reviewers to run the local build and inspect
the rendered OpenReview objects without private environment files.

## Source Areas

| Path | Purpose |
| --- | --- |
| `site_config/openreview.json` | Venue-level settings, request fields, and global configuration values. |
| `site_config/global_settings/` | Role consoles, assignment pages, venue landing behavior, and shared role pages. |
| `site_config/invitations/` | Submission, assignment, review, decision, camera-ready, publication, and recruitment invitation definitions. |
| `site_config/email_templates/` | Email bodies used by workflow actions. |
| `site_config/message_templates/` | Reusable visible text inserted by workflow scripts. |
| `site_config/python_scripts/` | Source-owned process helpers included into OpenReview invitation scripts. |
| `site_config/ui_helpers/` | Shared browser-side permission and UI helpers. |

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
| `site_config/invitations/venue/camera_ready_verification/` | `JMLR/-/Camera_Ready_Verification` |
| `site_config/invitations/reviewers/assignment/` | `JMLR/Reviewers/-/Assignment` |
| `site_config/invitations/action_editors/assignment/` | `JMLR/Paper<number>/Action_Editors/-/Assignment` |

Common section files:

| Source file | OpenReview section |
| --- | --- |
| `edit/reply.json` | Form schema, readers, writers, signatures, and instructions. |
| `edge/edge.json` | Edge invitation definition. |
| `process_functions/preprocess.py` | Validation before an edit is accepted. |
| `process_functions/process.py` | Actions after an edit is accepted. |
| `content_process_functions/process.py` | Meta-invitation content process script. |

## Global Settings And Templates

`site_config/global_settings/` owns group webfields, console webfields, group shells, and request-form snapshots. Important files include:

- `jmlr_meta.js`: venue homepage and role router.
- `author_console_webfield.js`: author console.
- `reviewer_console_webfield.js`: reviewer console.
- `action_editor_console_webfield.js`: Action Editor console.
- `eic_console_webfield.js`: Editors-in-Chief console.
- `production_editor_console_webfield.js`: Production Editor console.
- `groups/*.json`: role group shells.

`site_config/email_templates/` stores configurable workflow email bodies, grouped by recipient role:

- `author/*.txt`
- `reviewer/*.txt`
- `ae/*.txt`
- `eic/*.txt`
- `production_editor/*.txt`
- `recruitment/*.txt`

`site_config/message_templates/` stores reusable non-email text inserted into workflow scripts.

## Venue Settings

`site_config/openreview.json` owns non-secret venue settings. The build helper
reads them with OpenReview journal-style accessors before rendering environment
builds, then passes the resolved values into generated request-form snapshots,
webfields, and process scripts.

| Setting | Current value |
| --- | --- |
| `official_venue_name` | `Journal of Machine Learning Research` |
| `abbreviated_venue_name` | `JMLR` |
| `request_form.AE_anonymity` | `true` |
| `request_form.oss_action_editors_enabled` | `true` |
| `request_form.publication_mode` | `camera_ready_mark_published` |
| `request_form.publication_export_enabled` | `true` |
| `request_form.openreview_publication_enabled` | `true` |

The source test `tests/source/test_site_config_public_settings.py` validates
these defaults, fallback behavior, and JSON/Python render replacements.

## Build-Time Includes

Invitation templates can include placeholders rendered by `scripts/build/site_config.py`.

Common placeholders:

- `{{DEV_JOURNAL_ID}}` and `{{PROD_JOURNAL_ID}}`
- `{{ACTION_EDITORS_MAX_PAPERS}}`
- `{{REVIEWERS_MAX_PAPERS}}`
- `{{OSS_ACTION_EDITOR_GROUP_ID}}`
- `{{OSS_ACTION_EDITORS_MAX_PAPERS}}`
- `{{SITE_FORUM_REGEX}}`
- `{{SUPPLEMENTARY_MATERIAL_MAX_SIZE_MB}}`
- `{{MESSAGE_TEMPLATE_JSON:path/to/template.txt}}`
- `{{PYTHON_SCRIPT_JSON:path/to/script.py}}`
- `{{PYTHON_SCRIPT_FILE:path/to/script.py}}`

Build-time include targets must stay inside their corresponding `site_config/` source areas. Uploaded OpenReview process code uses the generated script text and must not read repository files at runtime.

## Source Review Rules

- Keep user-facing labels, form fields, and side effects aligned with the workflow and role docs.
- Prefer focused source files for focused UI surfaces or process helpers.
- Keep policy-sensitive text in auditable template or config locations when practical.
- Do not edit generated output as source; update the editable files in `site_config/`.
- Keep build-time include targets in the tree when adding template, Python, or JavaScript placeholders.
- Keep `scripts/build/site_config.py` available when source comments refer to the build path.
- Public source must not contain credentials, private journal request IDs, or local operator secrets.

## Validation

Run these checks after documentation or source changes:

```bash
python3 -m pip install -e ".[test]"
python3 scripts/build/site_config.py
python3 scripts/check_source_assembly.py
python3 scripts/check_tree.py
python3 -m pytest
```

`scripts/check_source_assembly.py` verifies required source areas, placeholder
targets, and build entrypoints. `scripts/check_tree.py` also checks Markdown
links, JSON/Python/JavaScript syntax where practical, and the local build.
`python3 -m pytest` runs source-only tests under `tests/source/`.
