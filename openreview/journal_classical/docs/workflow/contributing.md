# Contributing

Use ordinary pull requests for JMLR OpenReview configuration and documentation
changes.

## Before Opening A Pull Request

1. Update the relevant role or workflow documentation when user-facing behavior changes.
2. Keep source changes focused on the `site_config/` area that owns the behavior.
3. Run the checks from the repository root:

   ```bash
   python3 -m pip install -e ".[test]"
   python3 scripts/build/site_config.py
   python3 scripts/check_source_assembly.py
   python3 scripts/check_tree.py
   python3 -m pytest
   ```

## Review Expectations

- A reviewer should be able to connect each behavior change to a role or workflow document.
- UI labels, form fields, status text, and permission-sensitive actions should be named explicitly in the pull request.
- Generated files, local caches, and temporary run output should not be committed.
