function() {
  var or3client = lib.or3client;

  var SHORT_PHRASE = '';
  var isNewNote = note.tcdate < note.tmdate;

  var subject = SHORT_PHRASE + ' has received your submission titled ' + note.content.title;
  var message = 'Your submission to ' + SHORT_PHRASE + ' has been posted.\n\nTitle: ' + note.content.title + '\n\nAbstract: ' + note.content.abstract + '\n\nTo view your submission, click here: ' + baseUrl + '/forum?id=' + note.forum;
  
  if (!isNewNote) {
    subject = SHORT_PHRASE + ' has received an update on your submission titled ' + note.content.title;
    message = 'Your submission to ' + SHORT_PHRASE + ' has received an update.\n\nTitle: ' + note.content.title + '\n\nAbstract: ' + note.content.abstract + '\n\nTo view your submission, click here: ' + baseUrl + '/forum?id=' + note.forum;
  }
  var primaryAuthorMail = {
    groups: note.tauthor,
    subject: subject,
    message: message
  };

  var promises = [];
  promises.push(or3client.or3request(or3client.mailUrl, primaryAuthorMail, 'POST', token));

  message += '\n\nPlease contact ' + note.tauthor + ' if you feel you have been added in error.'
  var allAuthorMail = {
    groups: note.content.authorids,
    ignoreGroups: [note.tauthor],
    subject: subject,
    message: message
  }
  promises.push(or3client.or3request(or3client.mailUrl, allAuthorMail, 'POST', token));

  Promise.all(promises)
  .then(result => done())
  .catch(error => done(error));

  return true;
}
