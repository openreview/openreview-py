async function process(client, edit, invitation) {
  client.throwErrors = true;
  
  const authorIndex = edit.content.author_index.value;
  const authorId = edit.content.author_id.value;

  const { notes } = await client.getNotes({ id: edit.note.id });
  const publication = notes[0];

  if (authorIndex >= publication.content.authorids.value.length || authorIndex < 0) {
    return Promise.reject(new OpenReviewError({ name: 'Error', message: `Invalid author index` }));
  }

  const { profiles } = await client.getProfiles({ id: edit.signatures[0] });
  const userProfile = profiles[0];
  
  const usernames = userProfile.content.names.map(name => name.username);
  const names = userProfile.content.names.map(name => name.fullname);

  if (authorId === '') {
    const authorName = publication.content.authorids.value[authorIndex];
    if (!usernames.some(username => username === authorName)) {
      return Promise.reject(new OpenReviewError({ name: 'Error', message: `The author name ${authorName} from index ${authorIndex} doesn't match with the names listed in your profile` }));
    }
    return;
  }

  const usernameIndex = usernames.indexOf(authorId);

  if (usernameIndex === -1) {
    return Promise.reject(new OpenReviewError({ name: 'Error', message: `The author id ${authorId} doesn't match with the names listed in your profile` }));
  }
  
  const authorName = publication.content.authors.value[authorIndex];
  const nameIndex = names.indexOf(authorName);
  if (nameIndex === -1) {
    return Promise.reject(new OpenReviewError({ name: 'Error', message: `The author name ${authorName} from index ${authorIndex} doesn't match with the names listed in your profile` }));
  }
}