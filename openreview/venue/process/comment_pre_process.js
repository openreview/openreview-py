async function process(client, edit, invitation) {
  client.throwErrors = true

  const { note } = edit

  if (note.ddate || note.readers.includes("everyone")) {
    return
  }

  const [res1, res2] = await Promise.all([
    client.getNotes({ id: note.forum }),
    client.getGroups({ id: invitation.domain }),
  ])
  const forum = res1.notes[0]
  const domain = res2.groups[0]

  const commentMandatoryReaders =
    domain.content?.comment_mandatory_readers?.value || []
  for (const m of commentMandatoryReaders) {
    const mandatoryReader = m.replace("{number}", forum.number)
    if (!note.readers.includes(mandatoryReader)) {
      return Promise.reject(
        new OpenReviewError({
          name: "Error",
          message: `${mandatoryReader}must be readers of the comment`,
        })
      )
    }
  }
}
