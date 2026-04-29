def process(client, edit, invitation):
  note = edit.note

  needs_ethics_review = note.content.get('needs_ethics_review', {}).get('value', 'No') == 'Yes'
  if needs_ethics_review and 'no concerns' in note.content.get('ethical_concerns', {}).get('value', 'There are no concerns with this submission'):
    raise openreview.OpenReviewException("You have indicated that this submission needs an ethics review. Please enter a brief justification for your flagging.")

  is_deletion = note.ddate is not None
  current_note_id = note.id
  active_metareviews = client.get_notes(
    forum=note.forum,
    invitation=invitation.id
  )

  domain = client.get_group(invitation.domain)
  anon_area_chairs_name = domain.content.get('area_chairs_anon_name', {}).get('value', 'Area_Chair_')
  note_signature = note.signatures[0]

  if active_metareviews and not is_deletion and current_note_id not in [metareview.id for metareview in active_metareviews]:
    raise openreview.OpenReviewException('Only one Meta_Review can be submitted for this submission.')

  for metareview in active_metareviews:
    if metareview.id == current_note_id:
      if note_signature != metareview.signatures[0] and f'/{anon_area_chairs_name}' in note_signature:
        raise openreview.OpenReviewException('Only the Area Chair who submitted this Meta_Review can edit it.')
