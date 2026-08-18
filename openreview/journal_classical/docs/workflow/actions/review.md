# Review

Reviewers submit reviews from the reviewer paper page or Reviewer Console task.

| Item | Behavior |
| --- | --- |
| Main form | Reviewers complete `Summary Of Contributions`, `Strengths And Weaknesses`, `Requested Changes`, `Broader Impact Concerns`, `Claims And Evidence`, and `Audience`. |
| Recommendation and files | The current review form has no recommendation field and no review-file upload. Editorial outcomes belong to the later Decision action. |
| Visibility before peer release | Authors and the handling Action Editor can read each submitted review; other reviewers cannot. |
| Visibility after peer release | After the configured threshold, peer reviewers can also read released reviews. Review content remains anonymous to authors and peer reviewers. |
| Corrections | After a review is submitted, corrections or clarifications should use the available contact/editorial communication path unless the paper state allows edit/read review. |
| Rating-start notification | OpenReview notifies the Action Editor when review rating and decision work begins. JMLR supplies the message wording; the trigger, recipients, due dates, rating state, and decision transition remain unchanged. |

## Replacement Callback Contract

JMLR replaces the platform Review content callback only to expose `Decision`
after exactly two active reviews on an initial submission or one active review
on a linked resubmission. The replacement retains these native effects:

- a first review sends the standard `Review posted` reader notifications;
- the callback reconciles the reviewer's pending-load edge to the exact number
  of active assignments without an active review; create, edit, deletion,
  restore, and replay therefore converge instead of incrementing twice;
- the paper/reviewer assignment acknowledgement expires after the first review;
- reaching the configured reviewer target releases the active reviews; and
- editing an existing review may send a distinct `Review edited` notification,
  but does not repeat acknowledgement expiry, release, load decrement, or
  Decision invitation creation.

The browser gate submits and edits rendered Review forms. It also uses the
review note's rendered `Delete or restore note` control for a
delete/restore/delete sequence and refreshes after every transition. Read-only
checks then corroborate messages, the exact pending-load sequence,
acknowledgement expiry, review release, and the single Decision invitation.

The release gate submits the configured three reviews in Chrome and then opens
the paper as its author. The author must see exactly three anonymous Review
records; readback must find `everyone` readers and the paper-specific
`Review_Release` invitation on each active Review. Static preservation checks
live in `tests/source/test_decision_review_threshold.py`.
