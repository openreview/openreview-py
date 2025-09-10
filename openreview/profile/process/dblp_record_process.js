async function process(client, edit, invitation) {
  client.throwErrors = true;

  const note = Tools.convertDblpXmlToNote(edit.content?.xml?.value);

  note.id = edit.note.id;
  const { notes } = await client.getNotes({ id: note.id });
  if (notes[0].content.authorids && notes[0].content.authorids.value) {
    delete note.content.authorids;
  } 

  note.content.venueid = {
    value: edit.domain
  }

  await client.postNoteEdit({
    invitation: `${edit.domain}/-/Edit`,
    signatures: [`${edit.domain}/DBLP.org/Uploader`],
    readers: ['everyone'],
    writers: [`${edit.domain}/DBLP.org`],
    note: note
  });

}