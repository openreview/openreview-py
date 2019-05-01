function(){
    var or3client = lib.or3client;

    var SHORT_PHRASE = '';
    var AUTHORS_ID = '';
    var REVIEWERS_ID = '';
    var AREA_CHAIRS_ID = '';
    var PROGRAM_CHAIRS_ID = '';

    or3client.or3request(or3client.notesUrl + '?id=' + note.forum, {}, 'GET', token)
    .then(function(result) {

      var forumNote = result.notes[0];

      var ac_mail = {
        groups: [AREA_CHAIRS_ID],
        ignoreGroups: [note.tauthor],
        subject: '[' + SHORT_PHRASE + '] Comment posted to a paper in your area. Paper Number: ' + forumNote.number + ', Paper Title: \"' + forumNote.content.title + '\"',
        message: 'A comment was posted to a paper for which you are serving as Area Chair.\n\nComment title: ' + note.content.title + '\n\nComment: ' + note.content.comment + '\n\nTo view the comment, click here: ' + baseUrl + '/forum?id=' + note.forum + '&noteId=' + note.id
      };

      var reviewer_mail = {
        groups: [REVIEWERS_ID],
        ignoreGroups: [note.tauthor],
        subject: '[' + SHORT_PHRASE + '] Comment posted to a paper you are reviewing. Paper Number: ' + forumNote.number + ', Paper Title: \"' + forumNote.content.title + '\"',
        message: 'A comment was posted to a paper for which you are serving as reviewer.\n\nComment title: ' + note.content.title + '\n\nComment: ' + note.content.comment + '\n\nTo view the comment, click here: ' + baseUrl + '/forum?id=' + note.forum + '&noteId=' + note.id
      };

      var author_mail = {
        groups: forumNote.content.authorids,
        ignoreGroups: [note.tauthor],
        subject: '[' + SHORT_PHRASE + '] Your submission has received a comment. Paper Title: \"' + forumNote.content.title + '\"',
        message: 'Your submission to ' + SHORT_PHRASE + ' has received a comment.\n\nComment title: ' + note.content.title + '\n\nComment: ' + note.content.comment + '\n\nTo view the comment, click here: ' + baseUrl + '/forum?id=' + note.forum + '&noteId=' + note.id
      };

      var promises = [];

      if(note.readers.includes(AUTHORS_ID) || note.readers.includes('everyone')){
        promises.push(or3client.or3request(or3client.mailUrl, author_mail, 'POST', token));
      }

      if(note.readers.includes(REVIEWERS_ID) || note.readers.includes('everyone')){
        promises.push(or3client.or3request(or3client.mailUrl, reviewer_mail, 'POST', token));
      }

      if(AREA_CHAIRS_ID && (note.readers.includes(AREA_CHAIRS_ID) || note.readers.includes('everyone'))){
        promises.push(or3client.or3request(or3client.mailUrl, ac_mail, 'POST', token));
      }

      if(PROGRAM_CHAIRS_ID && (note.readers.includes(PROGRAM_CHAIRS_ID) || note.readers.includes('everyone'))){

        var ignoreGroups = note.nonreaders || [];
        ignoreGroups.push(note.tauthor);
        var pc_mail = {
          groups: [PROGRAM_CHAIRS_ID],
          ignoreGroups: ignoreGroups,
          subject: '[' + SHORT_PHRASE + '] A comment was posted. Paper Number: ' + forumNote.number + ', Paper Title: \"' + forumNote.content.title + '\"',
          message: 'A comment was posted to a paper for which you are serving as Program Chair.\n\nComment title: ' + note.content.title + '\n\nComment: ' + note.content.comment + '\n\nTo view the comment, click here: ' + baseUrl + '/forum?id=' + note.forum + '&noteId=' + note.id
        };

        promises.push(or3client.or3request(or3client.mailUrl, pc_mail, 'POST', token));
      }

      return Promise.all(promises);
    })
    .then(result => done())
    .catch(error => done(error));

    return true;
};
