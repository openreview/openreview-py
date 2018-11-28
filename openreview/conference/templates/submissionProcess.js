function() {
  var or3client = lib.or3client;

  var SHORT_PHRASE = '';

  var authorMail = {
    groups: note.content.authorids,
    subject: SHORT_PHRASE + ' has received your submission titled ' + note.content.title,
    message: 'Your submission to ' + SHORT_PHRASE + ' has been posted.\n\nTitle: ' + note.content.title + '\n\nAbstract: ' + note.content.abstract + '\n\nTo view your submission, click here: ' + baseUrl + '/forum?id=' + note.forum
  };

  or3client.or3request(or3client.mailUrl, authorMail, 'POST', token)
  .then(result => done())
  .catch(error => done(error));

  return true;
}
