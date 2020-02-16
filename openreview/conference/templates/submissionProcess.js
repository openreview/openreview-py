function() {
  var or3client = lib.or3client;

  var SHORT_PHRASE = '';

  var authorMessage = 'Your submission to ' + SHORT_PHRASE + ' has been posted.\n\nSubmission Number: ' + note.number + '\n\nTitle: ' + note.content.title;
  if (note.content.abstract) {
    authorMessage += '\n\nAbstract: ' + note.content.abstract;
  }
  authorMessage += '\n\nTo view your submission, click here: ' + baseUrl + '/forum?id=' + note.forum + '\n\nIf you are not an author of this submission and would like to be removed, please contact the author who added you at ' + note.tauthor;

  var authorMail = {
    groups: note.content.authorids,
    subject: SHORT_PHRASE + ' has received your submission titled ' + note.content.title,
    message: authorMessage
  };

  or3client.or3request(or3client.mailUrl, authorMail, 'POST', token)
  .then(result => done())
  .catch(error => done(error));

  return true;
}
