# Reviewer Rating

Reviewer Rating is the standard editorial action for evaluating a submitted
review. The action records one required field when it is available to a
permitted editorial role.

| Field | Behavior |
| --- | --- |
| Rating | Required enum: `Exceeds expectations`, `Meets expectations`, or `Falls below expectations`. |

Reviewer ratings support Top Reviewer recognition and internal editorial
quality tracking. The standard Rating action defines its schema, availability,
and workflow transition. JMLR adds no fork or additional rating fields.

## Visibility And Side Effects

- Reviewer ratings are editorial-only metadata for Action Editors and
  Editors-in-Chief.
- Authors, reviewers, Production Editors, and the public must not read reviewer
  rating records or rating details.
- Rating controls should appear only for allowed editorial roles while the
  rating workflow is active for the target review/reviewer.
- Rating controls should appear only for reviews that are eligible to be rated.
- Reviewer rating is not a reviewer pending task and should not create a
  separate reviewer-report workflow.
- Reviewer rating prompts should not duplicate when paper status is refreshed.
- Reviewer identity shown in rating views follows the paper editorial identity
  policy.
