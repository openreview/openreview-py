async function process(client, edit, invitation) {
    client.throwErrors = true

    const { note } = edit

    const { groups : domainGroups } = await client.getAllGroups({id: note.content.venue_id.value})

    const requestFormId = domainGroups[0]?.content?.request_form_id?.value

    if (requestFormId && note.id !== requestFormId) {
        return Promise.reject(
            new OpenReviewError({
                name: "Error",
                message: "The venue id " + note.content.venue_id.value + " has already been used for request " + requestFormId,
            })
        )
    }
}