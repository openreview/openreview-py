function() {
  var or3client = lib.or3client;

  var REVIEWERS_ACCEPTED_ID = '';
  var REVIEWERS_DECLINED_ID = '';
  var HASH_SEED = '';

  var hashKey = or3client.createHash(note.content.user, HASH_SEED);

  if (hashKey === note.content.key) {
    if (note.content.response === 'Yes') {
      console.log('Invitation replied Yes');
      //if a user is in the declined group, remove them from that group and add them to the reviewers group
      or3client.removeGroupMember(REVIEWERS_DECLINED_ID, note.content.user, token)
      .then(result => or3client.addGroupMember(REVIEWERS_ACCEPTED_ID, note.content.user, token))
      .then(result => done())
      .catch(error => done(error));

    } else if (note.content.response === 'No') {
      console.log('Invitation replied No');
      //if a user is in the reviewers group, remove them from that group and add them to the reviewers-declined group
      or3client.removeGroupMember(REVIEWERS_ACCEPTED_ID, note.content.user, token)
      .then(result => or3client.addGroupMember(REVIEWERS_DECLINED_ID, note.content.user, token))
      .then(result => done())
      .catch(error => done(error));

    } else {
      done('Invalid response', note.content.response);
    }

    return true;
  } else {
    done('Invalid key', note.content.key);
    return false;
  }
}
