async function process(client, edit, invitation) {
  client.throwErrors = true;

  const note = Tools.convertDblpXmlToNote(edit.content?.xml?.value);

  if (edit.note.id) {
    return
  }

  const externalId = note.externalId;

  const { notes } = await client.getNotes({ externalId: externalId });
  if (notes.length > 0) {
    throw new OpenReviewError({
      name: 'Error',
      message: `A document with the value ${externalId} in externalIds already exists.`
    });
  }

  if (externalId && externalId.startsWith('dblp:journals/corr/abs-')) {
    const arxivId = externalId.replace('dblp:journals/corr/abs-', 'arxiv:').replace(/-/g, '.');
    const { notes } = await client.getNotes({ externalId: arxivId });
    if (notes.length > 0) {
      throw new OpenReviewError({
        name: 'Error',
        message: `A public article from Arxiv is already present.`
      });
    }      
  }

}