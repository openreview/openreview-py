async function process(client, edit, invitation) {
  client.throwErrors = true;

  const note = Tools.convertORCIDJsonToNote(edit.content?.json?.value);

  note.id = edit.note.id;

  // Handle legacy convert format (string arrays) by converting to author{} objects
  const convertedAuthors = note.content.authors?.value || [];
  if (convertedAuthors.length > 0 && typeof convertedAuthors[0] === 'string') {
    const authorids = note.content.authorids?.value || [];
    note.content.authors = {
      value: convertedAuthors.map((name, i) => ({ fullname: name, username: authorids[i] || '' }))
    };
    delete note.content.authorids;
  }

  const { notes } = await client.getNotes({ id: edit.note.id });
  const existingAuthors = notes[0].content.authors?.value;

  if (existingAuthors) {
    note.content.authors.value = note.content.authors.value.map((author, index) => {
      const existing = existingAuthors[index];
      if (existing?.username) {
        return { ...author, username: existing.username };
      }
      return author;
    });
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