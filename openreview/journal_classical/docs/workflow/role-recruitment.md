# Role Recruitment

Role recruitment manages invitations to serve as an Action Editor or reviewer.

## Behavior

- Recruitment responses should map to the intended invitee identity.
- Accepting a role invitation may require OpenReview login when the response
  needs a profile identity.
- Declining an invitation may use the invitation response path without adding
  role membership.
- Recruitment responses should avoid duplicate role membership.
- Role acceptance uses an additive membership update so concurrent accepted
  invitations cannot overwrite one another.
- A newly accepted Action Editor receives the normal Regular-only eligibility
  default without requiring an additional initialization action.
- Each emailed recruitment response is bound to its exact active invite record.
  An accepted or declined response is terminal; an older response link must not
  reverse completed role membership.
- Accept requires an active logged-in OpenReview profile. When an email invite
  is accepted by a profile that does not list that email, the response records
  an identity-linkage warning while the invite edge retains the emailed
  identity. An unresolved Accept remains pending and creates neither a receipt
  nor role membership. Decline may be recorded without login.
- Unanswered role invitations expire after the configured interval without a
  reminder email. A terminal label is authoritative until the invite edge's
  original retention/expiration date.

## Must Hide

- Recruitment management tools from non-EIC users.
- Invitee identity details from users who are not allowed to manage
  recruitment.
- Role membership changes that are not backed by an accepted invitation.

## Related Roles

- Reviewers may manage assignment availability and review-load preferences
  after joining the reviewer pool.
- Editors-in-Chief open Action Editor and reviewer recruitment from Role
  Management, but compose and send the invitations on the OpenReview recruitment
  forum.

## Default Wording

The recruitment forms keep their standard editable `email_subject` and
`email_content` fields for every batch. JMLR provisions venue-specific default
bodies for both roles:

- Action Editor invitations describe JMLR, the editorial duties, and how
  OpenReview reduces administrative work.
- Reviewer invitations identify the inviter as the JMLR Editors-in-Chief.
- Both bodies include login, signup, Accept, Decline, expiry, and closing
  guidance without conference or program-chair terminology.

The Action Editor invitation does not promise a numerical load or assignment
pacing rule. Assignment load is managed separately through the standard
concurrent active-paper mechanism.

## Validation

Run `python3 scripts/check_source_assembly.py` and the focused recruitment
pytest checks after changing this page.
