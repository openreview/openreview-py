# Checks

These checks are meant for ordinary source and documentation review. They do
not require venue credentials or environment-specific state.

## Commands

Install the test dependency once in your local environment:

```bash
python3 -m pip install -e ".[test]"
```

| Command | Checks |
| --- | --- |
| `python3 scripts/check_source_assembly.py` | Required `site_config/` source areas and build-time template references. |
| `python3 -m pytest -c source_pyproject.toml` | Source-only pytest checks under `tests/source/`; these do not require venue credentials or DEV OpenReview state. |

## Source Assembly Scope

The source tree uses build-time placeholders such as:

| Placeholder | Expected Target |
| --- | --- |
| `{{MESSAGE_TEMPLATE_JSON:path}}` | `site_config/message_templates/path` |
| `{{WEB_FRAGMENT_JSON:path}}` | `site_config/web_fragments/path` |
| `{{EMAIL_TEMPLATE_JSON:path}}` | `site_config/email_templates/path` |
| `{{PYTHON_SCRIPT_JSON:path}}` | `site_config/python_scripts/path` |
| `{{PYTHON_SCRIPT_FILE:path}}` | `site_config/python_scripts/path` |
| `{{PYTHON_SCRIPT_CHUNK_FILE:path:start:end}}` | `site_config/python_scripts/path` |
| `{{GLOBAL_SETTING_JS_JSON:path}}` | `site_config/global_settings/path` |
| `{{GLOBAL_SETTING_JS_FILE:path}}` | `site_config/global_settings/path` |

The source assembly check verifies that these referenced files exist and that
their referenced targets are present. It does not apply configuration to an
OpenReview venue.

## Notification Content Ownership

JMLR-authored notification subjects and bodies belong in
`site_config/email_templates/`. Executable callbacks retain scheduling,
recipient selection, state handling, and API calls, and embed the content with
`EMAIL_TEMPLATE_JSON` during assembly. Standalone UI copy may use
`site_config/message_templates/` when extraction does not add runtime behavior.
Executable browser behavior belongs in `site_config/web_fragments/` and uses
`WEB_FRAGMENT_JSON`; it is not classified or counted as message text.

`tests/source/test_message_content_extraction.py` inventories public
`client.post_message` owners, checks exact template rendering, and compiles the
assembled callbacks. Mixed UI launchers keep intertwined labels and state
feedback in their owning JavaScript when separating them would add behavior.

## Review Rule

Before review, run the source assembly check and pytest. The private integration
repository separately owns environment rendering and apply-plan validation.
Update docs when a source change affects visible role behavior, form fields,
buttons, status text, or permissions.
