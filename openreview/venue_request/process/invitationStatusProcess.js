function(){
  var or3client = lib.or3client;

  var GROUP_PREFIX = '';
  var SUPPORT_GROUP = GROUP_PREFIX + '/Support';

  or3client.or3request(or3client.notesUrl + '?id=' + note.forum, {}, 'GET', token)
  .then(function(result) {

    var forumNote = result.notes[0];

    var message = {
      groups: note.readers,
      ignoreGroups: [note.tauthor, SUPPORT_GROUP],
      subject: 'Comment posted to your request for service: ' + forumNote.content.title,
      message: 'A comment was posted to your service request. \n\nComment title: ' + note.content.title + '\n\nComment: ' + note.content.comment + '\n\nTo view the comment, click here: ' + baseUrl + '/forum?id=' + note.forum + '&noteId=' + note.id
    };

    return or3client.or3request(or3client.mailUrl, message, 'POST', token);
  })
  .then(result => done())
  .catch(error => done(error));

  return true;
};
