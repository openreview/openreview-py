async function process(client, edit, invitation) {
  client.throwErrors = true;

  const note = Tools.convertArxivXmlToNote(edit.content?.xml?.value);

  note.id = edit.note.id;

  // Handle legacy convert format (string arrays) by converting to author{} objects
  const authors = note.content.authors?.value || [];
  if (authors.length > 0 && typeof authors[0] === 'string') {
    const authorids = note.content.authorids?.value || [];
    note.content.authors = {
      value: authors.map((name, i) => ({ fullname: name, username: authorids[i] || '' }))
    };
    delete note.content.authorids;
  }

  const existingAuthors = edit.note.content.authors?.value;
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
    signatures: [`${edit.domain}/arXiv.org/Uploader`],
    readers: ['everyone'],
    writers: [`${edit.domain}/arXiv.org`],
    note: note
  });

}