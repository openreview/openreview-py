function(){
  var or3client = lib.or3client;

  var GROUP_PREFIX = '';
  var SUPPORT_GROUP = GROUP_PREFIX + '/Support';

  or3client.or3request(or3client.notesUrl + '?id=' + note.forum, {}, 'GET', token)
  .then(function(result) {

    var forumNote = result.notes[0];
    var prettySignature = note.signatures[0].startsWith('~') ? note.signatures[0].replace(/~|\d+/g, '').replace(/_/g, ' ') : 'Support';
    var commentTitle = note.content.title ? note.content.title : 'Comment by ' + prettySignature;

    var message = {
      groups: note.readers,
      ignoreGroups: [SUPPORT_GROUP],
      subject: 'Comment posted to your request for service: ' + forumNote.content.title,
      message: 'A comment was posted to your service request. \n\nComment title: ' + commentTitle + '\n\nComment: ' + note.content.comment + '\n\nTo view the comment, click here: ' + baseUrl + '/forum?id=' + note.forum + '&noteId=' + note.id + '\n\nPlease note that with the exception of urgent issues, requests made on weekends or US holidays can expect to receive a response on the following business day. Thank you for your patience!'
    };

    if (commentTitle.includes('Process Completed')) {
      return or3client.or3request(or3client.mailUrl, message, 'POST', token)
    }

    var support_message = {
      groups: [SUPPORT_GROUP],
      subject: 'Comment posted to a service request: ' + forumNote.content.title,
      message: 'A comment was posted to a service request. \n\nComment title: ' + commentTitle + '\n\nComment: ' + note.content.comment + '\n\nTo view the comment, click here: ' + baseUrl + '/forum?id=' + note.forum + '&noteId=' + note.id
    };

    return or3client.or3request(or3client.mailUrl, message, 'POST', token)
    .then(result => or3client.or3request(or3client.mailUrl, support_message, 'POST', token));
  })
  .then(result => done())
  .catch(error => done(error));

  return true;
};
