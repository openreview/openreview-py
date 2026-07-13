# Reviewer Rating

Reviewer rating is optional editorial metadata submitted by AEs or EICs after
review work is complete.

| Field | Behavior |
| --- | --- |
| Quality/problem rating | Uses configured choices such as `No rating`, `Exceeds expectations`, `Meets expectations`, `Falls below expectations`, and `Report problem`. |
| Timeliness | Records whether the review was on time, past due, or not expected. Submitted reviews default to `On time` through a seven-day grace period after the applicable review due date. |
| Resubmission reviewer selection | Optional checkbox. Checked means the reviewer should be selected for automatic assignment if the paper is resubmitted. It is unchecked by default and does not assign the reviewer immediately. |
| Comment | Optional editorial record for rating context. |

Reviewer ratings support Top Reviewer recognition and internal editorial
quality tracking. They do not create a separate reviewer workflow or replace the
review form.

## Visibility And Side Effects

- Reviewer ratings are editorial-only metadata for Action Editors and
  Editors-in-Chief.
- Authors, reviewers, Production Editors, and the public must not read reviewer
  rating records, rating comments, hidden reviewer identity fields, or rating
  details.
- Rating controls should appear only for allowed editorial roles while the
  rating workflow is active for the target review/reviewer.
- Rating controls should appear only for reviews that are eligible to be rated.
- Reviewer rating is not a reviewer pending task and should not create a
  separate reviewer-report workflow.
- `Report problem` is a rating choice, not a separate public or reviewer-facing
  report action.
- Reviewer rating prompts should not duplicate when paper status is refreshed.
- Reviewer identity shown in rating views follows the paper editorial identity
  policy.
