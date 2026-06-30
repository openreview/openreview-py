# Role Recruitment And Volunteer Responses

Role recruitment manages invitations to serve as an Action Editor or reviewer,
plus reviewer volunteer responses.

## Behavior

- Recruitment responses should map to the intended invitee identity.
- Accepting a role invitation may require OpenReview login when the response
  needs a profile identity.
- Declining an invitation may use the invitation response path without adding
  role membership.
- Volunteer and recruitment responses should avoid duplicate role membership.
- Reviewer volunteering records willingness to join the reviewer pool. It does
  not assign the volunteer to any paper.

## Must Hide

- Recruitment management tools from non-EIC users.
- Invitee identity details from users who are not allowed to manage
  recruitment.
- Role membership changes that are not backed by an accepted invitation or
  approved volunteer path.

## Related Roles

- Authors may volunteer for the reviewer pool from the venue or author-facing
  entry point when that action is available.
- Reviewers may manage assignment availability and review-load preferences
  after joining the reviewer pool.
- Editors-in-Chief manage recruitment, role membership, and bulk invitations
  from EIC-only surfaces.

## Validation

Run `python3 scripts/check_tree.py` after changing this page.
