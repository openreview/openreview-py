# Email Notifications

Email is the one output of this library that cannot be un-read. Every `client.post_message()` in a process function sends as the venue, to whoever is in `recipients`, with whatever text was formatted. The server resolves group ids to members and emails, so a wrong group is a wrong audience of hundreds.

## Required shape

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

**Recruitment.** `tools.recruit_reviewer()`, `tools.recruit_user()` and the `*recruitment_process.py` files send invitations containing an HMAC-signed link (`get_user_hash_key(user, hash_seed)`, SHA-256 over the venue's `hash_seed`, which has `readers: [venue]`). The link is the credential: the pre-process recomputes the HMAC and checks membership in the invited group before accepting a response. A change that stores `hash_seed` with wider readers, uses a different user string for signing than for verification, or skips the invited-group check lets anyone accept on another person's behalf.

**Message content from users.** Subjects and bodies embed submission titles, comment text and reviewer-written messages via f-strings. That is plain-text email, so there is no injection concern, but a title that is `None` raises inside the f-string; use `.get()` chains for optional fields.

## Tests

Tests read sent mail with `openreview_client.get_messages(to=..., subject=...)` and assert counts and body fragments. Select by recipient and subject, never by position in the full list — the order of messages across recipients is not stable (#3225, #3226). A notification change ships with an assertion that the right address got it and an assertion that the excluded address did not.
