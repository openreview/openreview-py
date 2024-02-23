async function process(client, edit, invitation) {
  client.throwErrors = true

  const result = await client.getNotes({ id: edit.note.id })
  const html = result.notes?.[0]?.content?.html?.value
  let abstract = null
  if (html) {
    const extractionResult = await extractAbstract(html)
    abstract = extractionResult.abstract
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
