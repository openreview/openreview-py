async function process(client, edit, invitation) {
  client.throwErrors = true;

  const noteId = edit.note.id;
  const { notes } = await client.getNotes({ id: noteId });
  const note = notes[0];

  const html = note.content.html?.value;

  if (!html) {
    console.log('html field is empty, no edit will be posted');
    return;
  }
  
  let updatedFields = {};

  const { abstract, pdf } = await Tools.extractAbstract(html);
  console.log('abstract: ' + abstract);
  console.log('pdf: ' + pdf);
  if (abstract) {
    updatedFields.abstract = { value: abstract };
  }
  if (pdf) {
    updatedFields.pdf = { value: pdf };
  }

  await client.postNoteEdit({
    invitation: `${edit.domain}/-/Edit`,
    signatures: [`${edit.domain}/DBLP.org/Uploader`],
    readers: ['everyone'],
    writers: [`${edit.domain}/DBLP.org`],
    note: {
      id: noteId,
      content: updatedFields
    }
  });

}