async function process(client, edit, invitation) {
  client.throwErrors = true

  const result = await client.getNotes({ id: edit.note.id })
  const html = result.notes?.[0]?.content?.html?.value

  let abstract = null
  if (html) {
    const extractionResult = await Tools.extractAbstract(html);
    abstract = extractionResult.abstract
    console.log('abstract: ' + abstract);
    console.log('pdf: ' + extractionResult.pdf);
    console.log('error: ' + extractionResult.error);
  } else {
    console.log('html field is empty');
  }

  if (!abstract) return

  await client.postNoteEdit({
    invitation: "DBLP.org/-/Abstract",
    signatures: ["DBLP.org/Uploader"],
    id: edit.id,
    note: {
      id: edit.note.id,
      content: {
        abstract: {
          value: abstract,
        },
      },
    },
  })
}
