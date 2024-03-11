def process(client, edit, invitation):
  # Get paper number
  note = edit.note
  forum = client.get_note(note.forum)

  violation_fields = ['appropriateness', 'formatting', 'length', 'anonymity', 'responsible_checklist', 'limitations']
  format_field = {
    'appropriateness': 'Appropriateness',
    'formatting': 'Formatting',
    'length': 'Length',
    'anonymity': 'Anonymity',
    'responsible_checklist': 'Responsible Checklist',
    'limitations': 'Limitations'
  }
  if False in [note.content.get(field, {}).get('value', 'Yes') == 'Yes' for field in violation_fields]:
    violated_fields = [format_field[field] for field in violation_fields if note.content.get(field, {}).get('value', 'Yes') == 'No']
    if 'no violations' in note.content.get('potential_violation_justification', {}).get('value', 'no violations') or len(note.content.get('potential_violation_justification', {}).get('value', 'no violations')) <= 0:
      exception_string = f"You have indicated a potential violation with the following fields: {', '.join(violated_fields)}. Please enter a brief explanation under \"Potential Violation Justification\""
      raise openreview.OpenReviewException(exception_string)
    
  needs_ethics_review = edit.note.content.get('need_ethics_review', {}).get('value', 'No') == 'Yes'
  if needs_ethics_review and 'N/A' in edit.note.content.get('ethics_review_justification', {}).get('value', 'N/A'):
    raise openreview.OpenReviewException("You have indicated that this submission needs an ethics review. Please enter a brief justification for your flagging.")