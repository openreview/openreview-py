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

  function containsLink(text) {
    const tokenChecks = [
      ["includes", ["http://", "https://", "www."]]
    ]
    const popularDomainSuffixes = [
      ".com",
      ".net",
      ".org",
      ".io",
      ".co",
      ".tv",
      ".cn",
      ".de",
      ".uk",
      ".ru",
      ".nl",
      ".br"
    ]
    const boundaryChars = "<>()[]{}.,;:!?\"'"
    let lowerText = String(text || "").toLowerCase()

    for (const whitespace of ["\n", "\r", "\t"]) {
      lowerText = lowerText.split(whitespace).join(" ")
    }

    function trimToken(token) {
      let start = 0
      let end = token.length
      while (start < end && boundaryChars.includes(token[start])) {
        start += 1
      }
      while (end > start && boundaryChars.includes(token[end - 1])) {
        end -= 1
      }
      return token.slice(start, end)
    }

    function matches(value, checks) {
      for (const [operation, parts] of checks) {
        for (const part of parts) {
          if (value[operation](part)) {
            return true
          }
        }
      }
      return false
    }

    for (const rawToken of lowerText.split(" ")) {
      const token = trimToken(rawToken)
      // Skip empty tokens, emails, and tokens that cannot be hostnames.
      if (!token || token.includes("@") || !token.includes(".")) {
        continue
      }
      // Return early for explicit URL schemes and common www-style hosts.
      if (matches(token, tokenChecks)) {
        return true
      }

      // Trim the token to a host-like prefix before matching common web suffixes.
      let host = token
      for (const separator of ["/", "?", "#", ":"]) {
        const index = host.indexOf(separator)
        if (index !== -1) {
          host = host.slice(0, index)
        }
      }
      host = trimToken(host)

      // Match hosts that end in one of the common web suffixes.
      const firstDot = host.indexOf(".")
      if (firstDot > 0 && firstDot < host.length - 1) {
        for (const suffix of popularDomainSuffixes) {
          if (host.endsWith(suffix)) {
            return true
          }
        }
      }
    }

    return false
  }

  if ((readers.includes(authorGroupId) || readers.includes("everyone")) && containsLink(commentText)) {
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
