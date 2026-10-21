# Email Notifications

Email is the one output of this library that cannot be un-read. Every `client.post_message()` in a process function sends as the venue, to whoever is in `recipients`, with whatever text was formatted. The server resolves group ids to members and emails, so a wrong group is a wrong audience of hundreds.

## Required shape

Every process sends through `openreview.api.OpenReviewClient`:

```python
client.post_message(
    invitation=meta_invitation_id,     # the venue's meta invitation, from domain.content
    signature=venue_id,                # the venue, never a user
    sender=sender,                     # domain.get_content_value('message_sender')
    recipients=[...],                  # group ids or profile ids
    ignoreRecipients=[...],            # groups or ids to exclude even if in recipients
    replyTo=contact,                   # domain.get_content_value('contact') where replies make sense
    subject=f'[{short_name}] ...',
    message=...
)
```

- `invitation=` and `signature=` are what let the API authorize the message and attribute it; a call without them fails for the venue token or is attributed wrongly. Journals pass `journal.get_meta_invitation_id()` and `journal.get_message_sender()`.
- `parentGroup=` scopes recipients to members of that group; it is used when `recipients` is a broad group and only the intersection should be mailed.
- Guard the empty case: `if recipients:` before posting, or the call fails on an empty list.

## Audience rules

**Content follows readers.** A review, meta-review, decision, rebuttal or comment is quoted in an email only to recipients who are readers of that note. The pattern in `review_process.py` is: PCs get the full content, the reviewer who posted gets a confirmation, the assigned area chairs get the content if they are readers, the other reviewers get the content only when `release_to_reviewers` makes them readers, and authors get it only when `release_to_authors` is set. A new notification path needs the same branching, driven by the stage settings in the parent invitation (`users_to_notify`, `email_program_chairs`, `email_area_chairs`, `email_reviewers`, `email_authors`).

**Anonymity survives email.** The signature of an anonymous note is an anonymous group id. The email may say "a reviewer" or quote the anonymous id; it may not resolve it to a name or profile id for anyone outside the group's `deanonymizers`. Journals deanonymize action editors in emails to authors only when `is_action_editor_anonymous()` is false. Recruitment and assignment emails to the reviewer themselves may use their name.

**Exclude the actor and the silent groups.** `ignoreRecipients` carries the user who triggered the edit (they do not need "a comment was posted" for their own comment), the venue and support groups, and groups the stage settings say not to notify. Several tests assert that the super user and the PCs did *not* receive a notification for their own action; a diff that drops an `ignoreRecipients` entry will fail those tests in the file-level run and would spam real PCs.

**Authors and submissions.** New-submission notifications go to `authors_id` for that paper and list the authors only because the authors can already see their own submission. A notification that includes the author list and goes to a committee group on an anonymous venue is a leak.

**Recruitment.** `tools.recruit_reviewer()`, `tools.recruit_user()` and the `*recruitment_process.py` files send invitations containing a link whose `key` is derived from the venue's `hash_seed` (`get_user_hash_key`). The link is the credential: the API validates the key against `hash_seed` when it issues the guest token for the response, so no process function checks it. The library's responsibilities are to keep `hash_seed` at `readers: [venue]` and to sign exactly the user string the link carries. Storing `hash_seed` with wider readers, or signing a different string than the one in the URL, lets anyone accept on another person's behalf or locks every invitee out.

**Message content from users.** Subjects and bodies embed submission titles, comment text and reviewer-written messages via f-strings. That is plain-text email, so there is no injection concern. `submission.content['title']['value']` raises `KeyError` on a form without that field, which aborts the process; a `.get()` chain avoids the crash but formats a missing value as the literal text `None`, which is a wording defect, not a crash. Flag the first as a failure and the second only as text quality.

## Tests

Tests read sent mail with `openreview_client.get_messages(to=..., subject=...)` and assert counts and body fragments. Select by recipient and subject, never by position in the full list — the order of messages across recipients is not stable. A PR that changes who receives a notification should include a test that the intended recipient received it and a test that an excluded recipient (the actor, the authors, the PCs) did not; the second one is what catches an accidentally widened audience.
