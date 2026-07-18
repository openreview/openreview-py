async function process(client, edit, invitation) {
  client.throwErrors = true;
  
  const authorIndex = edit.content.author_index.value;
  const authorId = edit.content.author_id.value;
  const authorName = edit.content.author_name.value;

  if (Tools.prettyId(authorId) !== authorName) {
    return Promise.reject(new OpenReviewError({ name: 'Error', message: `The author id ${authorId} doesn't match with the author name ${authorName}` }));
  }
  
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

  const usernames = userProfile.content.names.map(name => name.username).filter(username => !!username);
  const names = userProfile.content.names.map(name => name.fullname);

  const usernameIndex = usernames.indexOf(authorId);

  if (usernameIndex === -1) {
    return Promise.reject(new OpenReviewError({ name: 'Error', message: `The author id ${authorId} doesn't match with the names listed in your profile` }));
  }

  const publicationAuthorName = publication.content.authors.value[authorIndex]?.fullname;
  const nameIndex = names.indexOf(publicationAuthorName);
  if (nameIndex === -1) {
    return Promise.reject(new OpenReviewError({ name: 'Error', message: `The author name ${publicationAuthorName} from index ${authorIndex} doesn't match with the names listed in your profile` }));
  }
}