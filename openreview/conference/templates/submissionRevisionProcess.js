function() {
  var or3client = lib.or3client;

  var SHORT_PHRASE = '';

  var forumNote = or3client.or3request(or3client.notesUrl+'?id='+note.forum, {}, 'GET', token);

  forumNote.then(function(result) {
    var forum = result.notes[0];
    var title = note.content.title || forum.content.title;

    var authorMail = {
      groups: note.content.authorids,
      subject: SHORT_PHRASE + ' has received a new revision of your submission titled ' + title,
      message: 'Your new revision of the submission to ' + SHORT_PHRASE + ' has been posted.\n\nTitle: ' + title + '\n\nAbstract: ' + note.content.abstract + '\n\nTo view your submission, click here: ' + baseUrl + '/forum?id=' + note.forum
    };

    return or3client.or3request(or3client.mailUrl, authorMail, 'POST', token);
  })
  .then(result => done())
  .catch(error => done(error));

  return true;
}
