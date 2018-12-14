function(){
    var or3client = lib.or3client;

    var CONFERENCE_ID = '';
    var SHORT_PHRASE = '';
    var AUTHORS_NAME = '';
    var REVIEWERS_NAME = '';
    var AREA_CHAIRS_NAME = '';
    var PROGRAM_CHAIRS_NAME = '';

    or3client.or3request(or3client.notesUrl + '?id=' + note.forum, {}, 'GET', token)
    .then(function(result) {

      var forumNote = result.notes[0];

      var PAPER_AUTHORS = CONFERENCE_ID + '/Paper' + forumNote.number + '/' + AUTHORS_NAME;
      var PAPER_REVIEWERS = CONFERENCE_ID + '/Paper' + forumNote.number + '/' + REVIEWERS_NAME;
      var PAPER_AREACHAIRS = CONFERENCE_ID + '/Paper' + forumNote.number + '/' + AREA_CHAIRS_NAME;
      var PROGRAM_CHAIRS = CONFERENCE_ID + '/' + PROGRAM_CHAIRS_NAME;

      var ac_mail = {
        groups: [PAPER_AREACHAIRS],
        ignoreGroups: [note.tauthor],
        subject: '[' + SHORT_PHRASE + '] Comment posted to a paper in your area. Paper Number: ' + forumNote.number + ', Paper Title: \"' + forumNote.content.title + '\"',
        message: 'A comment was posted to a paper for which you are serving as Area Chair.\n\nComment title: ' + note.content.title + '\n\nComment: ' + note.content.comment + '\n\nTo view the comment, click here: ' + baseUrl + '/forum?id=' + note.forum + '&noteId=' + note.id
      };

      var reviewer_mail = {
        groups: [PAPER_REVIEWERS],
        ignoreGroups: [note.tauthor],
        subject: '[' + SHORT_PHRASE + '] Comment posted to a paper you are reviewing. Paper Number: ' + forumNote.number + ', Paper Title: \"' + forumNote.content.title + '\"',
        message: 'A comment was posted to a paper for which you are serving as reviewer.\n\nComment title: ' + note.content.title + '\n\nComment: ' + note.content.comment + '\n\nTo view the comment, click here: ' + baseUrl + '/forum?id=' + note.forum + '&noteId=' + note.id
      };

      var pc_mail = {
        groups: [PROGRAM_CHAIRS],
        ignoreGroups: [note.tauthor],
        subject: '[' + SHORT_PHRASE + '] A comment was posted. Paper Number: ' + forumNote.number + ', Paper Title: \"' + forumNote.content.title + '\"',
        message: 'A comment was posted to a paper with readership restricted to the Program Chairs.\n\nComment title: ' + note.content.title + '\n\nComment: ' + note.content.comment + '\n\nTo view the comment, click here: ' + baseUrl + '/forum?id=' + note.forum + '&noteId=' + note.id
      };

      var author_mail = {
        groups: forumNote.content.authorids,
        ignoreGroups: [note.tauthor],
        subject: '[' + SHORT_PHRASE + '] Your submission has received a comment. Paper Title: \"' + forumNote.content.title + '\"',
        message: 'Your submission to ' + SHORT_PHRASE + ' has received a comment.\n\nComment title: ' + note.content.title + '\n\nComment: ' + note.content.comment + '\n\nTo view the comment, click here: ' + baseUrl + '/forum?id=' + note.forum + '&noteId=' + note.id
      };

      var promises = [];

      if(note.readers.includes(PAPER_AUTHORS) || note.readers.includes('everyone')){
        promises.push(or3client.or3request(or3client.mailUrl, author_mail, 'POST', token));
      }

      if(note.readers.includes(PAPER_REVIEWERS) || note.readers.includes('everyone')){
        promises.push(or3client.or3request(or3client.mailUrl, reviewer_mail, 'POST', token));
      }

      if(note.readers.includes(PAPER_AREACHAIRS) || note.readers.includes('everyone')){
        promises.push(or3client.or3request(or3client.mailUrl, ac_mail, 'POST', token));
      }

      if(note.readers.includes(PROGRAM_CHAIRS) || note.readers.includes('everyone')){
        promises.push(or3client.or3request(or3client.mailUrl, pc_mail, 'POST', token));
      }


      return Promise.all(promises);
    })
    .then(result => done())
    .catch(error => done(error));

    return true;
};
