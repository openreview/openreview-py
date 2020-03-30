function processUpdate() {
  var or3client = lib.or3client;

  var SHORT_PHRASE = '';

  var authorSubject = SHORT_PHRASE + ' has received your submission titled ' + note.content.title;
  var noteAbstract = (note.content.abstract ? `\n\nAbstract: ${note.content.abstract}` : '');
  var action = note.ddate ? 'deleted' : (existingNote ? 'updated' : 'posted');
  var authorMessage = `Your submission to ${SHORT_PHRASE} has been ${action}.\n\nSubmission Number: ${note.number} \n\nTitle: ${note.content.title} ${noteAbstract} \n\nTo view your submission, click here: ${baseUrl}/forum?id=${note.forum}`;

  var authorMail = {
    groups: [note.tauthor],
    subject: authorSubject,
    message: authorMessage
  };

  authorMessage += `\n\nIf you are not an author of this submission and would like to be removed, please contact the author who added you at ${note.tauthor}`;

  var otherAuthorsMail = {
    groups: note.content.authorids,
    ignoreGroups: [note.tauthor],
    subject: authorSubject,
    message: authorMessage
  };

  Promise.all([
    or3client.or3request(or3client.mailUrl, authorMail, 'POST', token),
    or3client.or3request(or3client.mailUrl, otherAuthorsMail, 'POST', token)
    ])
  .then(result => done())
  .catch(error => done(error));

  return true;
}
