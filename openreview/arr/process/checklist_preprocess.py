def process(client, edit, invitation):
  # Get paper number
  note = edit.note
  forum = client.get_note(note.forum)

  needs_ethics_review = edit.note.content.get('need_ethics_review', {}).get('value', 'No') == 'Yes'
  if needs_ethics_review and 'N/A' in edit.note.content.get('ethics_review_justification', {}).get('value', 'N/A'):
    raise openreview.OpenReviewException("You have indicated that this submission needs an ethics review. Please enter a brief justification for your flagging.")
