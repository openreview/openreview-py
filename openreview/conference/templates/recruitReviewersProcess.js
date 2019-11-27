function() {
  var or3client = lib.or3client;

  var SHORT_PHRASE = '';
  var CONFERENCE_NAME = '';
  var REVIEWER_NAME = '';
  var REVIEWERS_ACCEPTED_ID = '';
  var REVIEWERS_DECLINED_ID = '';
  var HASH_SEED = '';
  var REDUCED_LOAD_INVITATION_NAME = '';

  var hashKey = or3client.createHash(note.content.user, HASH_SEED);

  if (hashKey === note.content.key) {
    if (note.content.response === 'Yes') {
      console.log('Invitation replied Yes');
      //if a user is in the declined group, remove them from that group and add them to the reviewers group
      var text = 'Thank you for accepting the invitation to be a ' + REVIEWER_NAME + ' for ' + SHORT_PHRASE + '.\n';
      text += 'The ' + SHORT_PHRASE + ' program chairs will be contacting you with more information regarding next steps soon. ';
      text += 'In the meantime, please add noreply@openreview.net to your email contacts to ensure that you receive all communications.\n\n';
      text += 'If you would like to change your decision, please click the Decline link in the previous invitation email.';

      var email = {
        groups: [note.content.user],
        subject: '[' + SHORT_PHRASE + '] ' + REVIEWER_NAME + ' Invitation accepted',
        message: text
      };

      or3client.removeGroupMember(REVIEWERS_DECLINED_ID, note.content.user, token)
      .then(result => or3client.addGroupMember(REVIEWERS_ACCEPTED_ID, note.content.user, token))
      .then(result => or3client.or3request(or3client.mailUrl, email, 'POST', token))
      .then(result => done())
      .catch(error => done(error));

    } else if (note.content.response === 'No') {
      console.log('Invitation replied No');

      var text = 'You have declined the invitation to become a ' + REVIEWER_NAME + ' for ' + SHORT_PHRASE + '.\n\n';
      text += 'If you would like to change your decision, please click the Accept link in the previous invitation email.\n\n';

      if (REDUCED_LOAD_INVITATION_NAME){
        text += 'In case you only declined because you think you cannot handle the maximum load of papers, you can reduce your load slightly. Be aware that this will decrease your overall score for an outstanding reviewer award, since all good reviews will accumulate a positive score. You can request a reduced reviewer load by clicking here: https://openreview.net/invitation?id=' + CONFERENCE_NAME + '/-/' + REDUCED_LOAD_INVITATION_NAME + '&user=' + note.content.user + '&key=' + note.content.key + ' .\n\n'
      }

      var email = {
        groups: [note.content.user],
        subject: '[' + SHORT_PHRASE + '] ' + REVIEWER_NAME + ' Invitation declined',
        message: text
      };
      //if a user is in the reviewers group, remove them from that group and add them to the reviewers-declined group
      or3client.removeGroupMember(REVIEWERS_ACCEPTED_ID, note.content.user, token)
      .then(result => or3client.addGroupMember(REVIEWERS_DECLINED_ID, note.content.user, token))
      .then(result => or3client.or3request(or3client.mailUrl, email, 'POST', token))
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
