async function process(client, edit, invitation) {
  client.throwErrors = true;

  const note = Tools.convertORCIDJsonToNote(edit.content?.json?.value);

  note.id = edit.note.id;
  const { notes } = await client.getNotes({ id: edit.note.id });
  const authorids =  notes[0].content.authorids?.value;

  if (authorids) {
    note.content.authorids.value = note.content.authorids.value.map((authorid, index) => authorids[index] || authorid);
  }

  note.content.venueid = {
    value: edit.domain
  }

  await client.postNoteEdit({
    invitation: `${edit.domain}/-/Edit`,
    signatures: [`${edit.domain}/ORCID.org/Uploader`],
    readers: ['everyone'],
    writers: [`${edit.domain}/ORCID.org`],
    note: note
  });

}