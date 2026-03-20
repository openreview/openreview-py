async function process(client, edit, invitation) {
  client.throwErrors = true

  const { note } = edit
  if (note.ddate) {
    return
  }

  const [res1, res2] = await Promise.all([
    client.getNotes({ id: note.forum }),
    client.getGroups({ id: invitation.domain }),
  ])
  const forum = res1.notes[0]
  const domain = res2.groups[0]
  const readers = note.readers || []
  const authorsName = domain.content?.authors_name?.value || "Authors"
  const authorGroupId = `${domain.id}/Submission${forum.number}/${authorsName}`
  const commentText = note.content?.comment?.value || ""
  const linkPattern =
    /\[[^\]]+\]\([^)]+\)|<?(?:https?:\/\/|www\.)\S+>?|\b[a-z0-9.-]+\.[a-z]{2,}\/\S*/i

  if ((readers.includes(authorGroupId) || readers.includes("everyone")) && linkPattern.test(commentText)) {
    return Promise.reject(
      new OpenReviewError({
        name: "Error",
        message: "Links are not allowed in official comments that are visible to authors.",
      })
    )
  }

  if (readers.includes("everyone")) {
    return
  }

  const commentMandatoryReaders =
    domain.content?.comment_mandatory_readers?.value || []
  for (const m of commentMandatoryReaders) {
    const reader = m.replace("{number}", forum.number)
    if (!readers.includes(reader)) {
      return Promise.reject(
        new OpenReviewError({
          name: "Error",
          message: reader + " must be readers of the comment",
        })
      )
    }
  }
}
