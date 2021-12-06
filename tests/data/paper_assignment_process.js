function processUpdate(){
  const or3client = lib.or3client;
  const REVIEWERS_ID = '';

  if (note.ddate) {
    return or3client.removeGroupMember(REVIEWERS_ID, note.tail, token)
    .then(result => done())
    .catch(error => done(error));
  } else {
    return or3client.addGroupMember(REVIEWERS_ID, note.tail, token)
    .then(result => done())
    .catch(error => done(error));
  }

};
