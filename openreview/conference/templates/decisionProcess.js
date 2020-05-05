function (){
    var or3client = lib.or3client;

    var CONFERENCE_ID = '';
    var SHORT_PHRASE = '';
    var AUTHORS_NAME = '';

    var forumNote = or3client.or3request(or3client.notesUrl + '?id=' + note.forum, {}, 'GET', token);

    forumNote.then(function(result) {
      var forum = result.notes[0];
      var promises = [];

      var AUTHORS_ID = CONFERENCE_ID + '/Paper' + forum.number + '/' + AUTHORS_NAME;

      if (note.readers.includes('everyone') || note.readers.includes(AUTHORS_ID)) {
        var author_mail = {
          groups: [AUTHORS_ID],
          subject: '[' + SHORT_PHRASE + '] Decision posted to your submission - Paper number: ' + forum.number + ', Paper title: "' + forum.content.title + '"',
          message: 'To view the decision, click here: ' + baseUrl + '/forum?id=' + note.forum + '&noteId=' + note.id
        };
        promises.push(or3client.or3request( or3client.mailUrl, author_mail, 'POST', token ));
      }

      return Promise.all(promises)
    })
    .then(result => done())
    .catch(error => done(error));
    return true;
  };
