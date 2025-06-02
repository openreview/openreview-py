async function process(client, edit, invitation) {
  client.throwErrors = true;

  if (edit.note.id) {
    return
  }  

  const externalId = edit.note.externalId;

  const { notes } = await client.getNotes({ externalId: externalId });
  if (notes.length > 0) {
    throw new OpenReviewError({
      name: 'Error',
      message: `A document with the value ${externalId} in externalIds already exists.`
    });
  }

  const dblpId = externalId.replace('arxiv:', 'dblp:journals/corr/abs-').replace(/\./g, '-');
  const { notes: foundNotes } = await client.getNotes({ externalId: dblpId });
  if (foundNotes.length > 0) {
    throw new OpenReviewError({
      name: 'Error',
      message: `A public article from DBLP is already present.`
    });
  }      

}