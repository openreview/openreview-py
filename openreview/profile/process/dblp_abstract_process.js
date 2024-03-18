async function process(client, edit, invitation) {
  client.throwErrors = true

  const result = await client.getNotes({ id: edit.note.id })
  const html = result.notes?.[0]?.content?.html?.value
  const extractAbstractFnUrl = null;
  let abstract = null
  if (html && extractAbstractFnUrl) {
    const extractionResult = await fetch(`${extractAbstractFnUrl}?url=${html}`.then(response => response.json()));
    abstract = extractionResult.abstract
    console.log('abstract: ' + abstract);
    console.log('pdf: ' + extractionResult.pdf);
    console.log('error: ' + extractionResult.error);
  }

  if (!abstract) return

  await client.postNoteEdit({
    invitation: "DBLP.org/-/Abstract",
    signatures: ["DBLP.org/Uploader"],
    readers: ["everyone"],
    writers: ["DBLP.org", "DBLP.org/Uploader"],
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
