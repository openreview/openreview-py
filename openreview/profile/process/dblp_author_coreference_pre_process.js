async function process(client, edit, invitation) {
  client.throwErrors = true;
  
  const value = edit.note.content.authorids?.value;

  if (!value?.replace) {
    return Promise.reject(new OpenReviewError({ name: 'Error', message: `Only author replacement is allowed` }))
  }
  
  const index = value.replace.index;
  const authorId = value.replace.value;

  const { profiles } = await client.getProfiles({ id: edit.signatures[0] });
  const userProfile = profiles[0];
  
  const { notes } = await client.getNotes({ id: edit.note.id });
  const publication = notes[0];
  
  const usernames = userProfile.content.names.map(name => name.username);
  const names = userProfile.content.names.map(name => name.fullname);
  const nameIndex = usernames.indexOf(authorId);

  if (nameIndex === -1) {
    return Promise.reject(new OpenReviewError({ name: 'Error', message: `The author name to replace doesn't match with the names listed in your profile` }))
  }
  
  if (names[nameIndex] !== publication.content.authors.value[index]) {
    return Promise.reject(new OpenReviewError({ name: 'Error', message: `Your name doesn't match with the author name in the paper` }))
  }
}