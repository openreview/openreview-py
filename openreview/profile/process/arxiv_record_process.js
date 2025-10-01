async function process(client, edit, invitation) {
  client.throwErrors = true;

  const note = Tools.convertArxivXmlToNote(edit.content?.xml?.value);

  note.id = edit.note.id;
  const authorids = edit.note.content.authorids?.value;
  if (authorids) {
    note.content.authorids.value = note.content.authorids.value.map((authorid, index) => authorids[index] || authorid);
  }

  note.content.venueid = {
    value: edit.domain
  }

  await client.postNoteEdit({
    invitation: `${edit.domain}/-/Edit`,
    signatures: [`${edit.domain}/arXiv.org/Uploader`],
    readers: ['everyone'],
    writers: [`${edit.domain}/arXiv.org`],
    note: note
  });

}