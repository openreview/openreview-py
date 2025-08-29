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

  const { notes: savedNotes } = await client.getNotes({ id: note.id });
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
            signatures: [`${edit.domain}/DBLP.org`],
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