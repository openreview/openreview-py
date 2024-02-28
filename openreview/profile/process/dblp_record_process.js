async function process(client, edit, invitation) {
  client.throwErrors = true;
  
  const note = Tools.convertDblpXmlToNote(edit.content?.xml?.value);

  note.id = edit.note.id;
  const authorids = edit.note.content.authorids?.value;
  if (authorids) {
    note.content.authorids.value = note.content.authorids.value.map((authorid, index) => authorids[index] || authorid);
  }
  
  console.log('note: ' + JSON.stringify(note));
  
  await client.postNoteEdit({
    invitation: 'DBLP.org/-/Edit',
    signatures: ['DBLP.org/Uploader'],
    readers: ['everyone'],
    writers: ['DBLP.org'],
    note: note
  });
}