def process(client, edit, invitation):
  # Get paper number
  note = edit.note
  forum = client.get_note(note.forum)

  needs_ethics_review = edit.note.content.get('needs_ethics_review', {}).get('value', 'No') == 'Yes'
  if needs_ethics_review and 'no concerns' in edit.note.content.get('ethical_concerns', {}).get('value', 'There are no concerns with this submission'):
    raise openreview.OpenReviewException("You have indicated that this submission needs an ethics review. Please enter a brief justification for your flagging.")