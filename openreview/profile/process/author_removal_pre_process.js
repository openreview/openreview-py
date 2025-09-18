async function process(client, edit, invitation) {
  client.throwErrors = true;
  
  const authorIndex = edit.content.author_index.value;
  
  const { notes } = await client.getNotes({ id: edit.note.id });
  const publication = notes[0];

  if (authorIndex >= publication.content.authors.value.length || authorIndex < 0) {
    return Promise.reject(new OpenReviewError({ name: 'Error', message: `Invalid author index` }));
  }

  if (!edit.signatures[0].startsWith('~') || edit.signatures[0] == '~Super_User1') {
    return;
  }

  const { profiles } = await client.getProfiles({ id: edit.signatures[0] });
  const userProfile = profiles[0];
  
  const usernames = userProfile.content.names.map(name => name.username);

  const authorName = publication.content.authorids?.value[authorIndex];
  if (!usernames.some(username => username === authorName)) {
    return Promise.reject(new OpenReviewError({ name: 'Error', message: `The author name ${authorName} from index ${authorIndex} doesn't match with the names listed in your profile` }));
  }

}