async function process(client, edit, invitation) {
  client.throwErrors = true;
  
  const index = edit.content.author_index.value;
  const authorId = edit.content.author_id.value;

  const { notes } = await client.getNotes({ id: edit.note.id });
  const publication = notes[0];

  if (index >= publication.content.authorids.value.length || index < 0) {
    return Promise.reject(new OpenReviewError({ name: 'Error', message: `Invalid author index` }));
  }

  const { profiles } = await client.getProfiles({ id: edit.signatures[0] });
  const userProfile = profiles[0];
  
  const usernames = userProfile.content.names.map(name => name.username);
  const names = userProfile.content.names.map(name => name.fullname);

  if (authorId === '') {
    if (!usernames.some(username => username === publication.content.authorids.value[index])) {
      return Promise.reject(new OpenReviewError({ name: 'Error', message: `The author name to remove doesn't match with the names listed in your profile` }));
    }
    return;
  }

  const nameIndex = usernames.indexOf(authorId);

  if (nameIndex === -1) {
    return Promise.reject(new OpenReviewError({ name: 'Error', message: `The author name to replace doesn't match with the names listed in your profile` }));
  }
  
  if (names[nameIndex] !== publication.content.authors.value[index]) {
    return Promise.reject(new OpenReviewError({ name: 'Error', message: `Your name doesn't match with the author name in the paper` }));
  }
}