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
  
  const { notes: savedNotes } = await client.getNotes({ id: edit.note.id });
  const savedNote = savedNotes[0];
  signature = edit.signatures[0];
  if (signature.startsWith('~')) {
    const { profiles } = await client.getProfiles({ id: signature });
    if (profiles.length > 0) {
      const profile = profiles[0];
      const profileNames = profile.content.names.map(name => name.fullname);
      savedNote.content.authors.value.forEach((author, index) => {
        if (profileNames.includes(author)) {
          savedNote.content.authorids.value[index] = signature;
          client.postNoteEdit({
            invitation: `${edit.domain}/-/Authorship_Claim`,
            signatures: [`${edit.domain}/arXiv.org`],
            content: {
                'author_index': { 'value': index },
                'author_id': { 'value': signature },
            },                 
            note: {
              id: savedNote.id
            }
          });
          return;          
        }
      });
    }
  }  

}