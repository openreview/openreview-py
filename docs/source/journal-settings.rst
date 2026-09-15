Journal settings
================

Action Editor paper visibility
------------------------------

``action_editor_paper_visibility`` controls which Action Editors may read a
private paper and its private lifecycle records.

``all``
  Every member of the journal's Action Editors group may read private papers.
  This is the default and preserves existing Journal behavior.

``assigned_only``
  Only members of the paper's Action Editors group receive Action Editor
  access. Editors in Chief, authors, assigned reviewers, and other explicitly
  authorized roles keep their existing access. Public records remain public.

The value must be ``all`` or ``assigned_only``. Invalid values stop journal
setup before it writes venue configuration. Changing this setting does not
rewrite records that already exist; an existing venue must separately qualify
or migrate historical records before relying on the stricter mode.
