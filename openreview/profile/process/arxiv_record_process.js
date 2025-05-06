async function process(client, edit, invitation) {
  client.throwErrors = true;


  const { notes } = await client.getNotes({ id: edit.note.id });
  const note = notes[0];
  if (!note.content.authorids) {
    await client.postNoteEdit({
      invitation: `${edit.domain}/-/Edit`,
      signatures: [`${edit.domain}/arXiv.org/Uploader`],
      readers: ['everyone'],
      writers: [`${edit.domain}/arXiv.org`],
      note: {
        id: note.id,
        content: {
          authorids: {
            value: note.content.authors.value.map((author, index) => {
              return `https://arxiv.org/search/?query=${author}&searchtype=all`;
            })
          }
        }
      }
    });
  }

  await client.postNoteEdit({
    invitation: `${edit.domain}/-/Discussion_Allowed`,
    signatures: [`${edit.domain}/arXiv.org`],
    note: {
      id: note.id,
    }
  });  

}