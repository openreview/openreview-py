async function process(client, edit, invitation) {
  client.throwErrors = true;

  // const note = Tools.convertDblpXmlToNote(edit.content?.xml?.value);

  // note.id = edit.note.id;
  // const { notes } = await client.getNotes({ id: note.id });
  // if (notes[0].content.authorids && notes[0].content.authorids.value) {
  //   delete note.content.authorids;
  // } 

  // note.content.venueid = {
  //   value: edit.domain
  // }

  note = {
    id: edit.note.id,
    content: {
      authorids: {
        value: edit.note.content.authors?.value.map((author) => {
          return `https://orcid.org/orcid-search/search?searchQuery=${author}`;
        })
      },
    }
  };

  await client.postNoteEdit({
    invitation: `${edit.domain}/-/Edit`,
    signatures: [`${edit.domain}/ORCID.org/Uploader`],
    readers: ['everyone'],
    writers: [`${edit.domain}/ORCID.org`],
    note: note
  });

}