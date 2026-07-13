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
| `python3 scripts/build/site_config.py` | Renders local `build/local/dev` and `build/local/prod` output from checked-in source only. |
| `python3 scripts/check_source_assembly.py` | Required `site_config/` source areas, build entrypoints, and build-time template references. |
| `python3 scripts/check_tree.py` | Markdown links, concrete JSON files, complete Python files, complete JavaScript files, source assembly references, and the local build. |
| `python3 -m pytest` | Source-only pytest checks under `tests/source/`; these do not require venue credentials or dev OpenReview state. |

## Source Assembly Scope

The source tree uses build-time placeholders such as:

| Placeholder | Expected Target |
| --- | --- |
| `{{MESSAGE_TEMPLATE_JSON:path}}` | `site_config/message_templates/path` |
| `{{EMAIL_TEMPLATE_JSON:path}}` | `site_config/email_templates/path` |
| `{{PYTHON_SCRIPT_JSON:path}}` | `site_config/python_scripts/path` |
| `{{PYTHON_SCRIPT_FILE:path}}` | `site_config/python_scripts/path` |
| `{{PYTHON_SCRIPT_CHUNK_FILE:path:start:end}}` | `site_config/python_scripts/path` |
| `{{GLOBAL_SETTING_JS_JSON:path}}` | `site_config/global_settings/path` |
| `{{GLOBAL_SETTING_JS_FILE:path}}` | `site_config/global_settings/path` |

The source assembly check verifies that these referenced files exist and that
the build entrypoints referenced by source comments are present. It does not
apply configuration to an OpenReview venue.

## Review Rule

Before opening a pull request, run the build, tree/source checks, and pytest.
Update docs when a source change affects visible role behavior, form fields,
buttons, status text, or permissions.
