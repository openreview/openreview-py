function(){
    var or3client = lib.or3client;

    var CONFERENCE_ID = '';
    var SHORT_PHRASE = '';
    var AUTHORS_NAME = '';
    var REVIEWERS_NAME = '';
    var AREA_CHAIRS_NAME = '';

    var forumNote = or3client.or3request(or3client.notesUrl+'?id='+note.forum, {}, 'GET', token);

    forumNote.then(function(result) {
      var forum = result.notes[0];
      var note_number = forum.number;

      PAPER_REVIEWERS = CONFERENCE_ID + '/Paper' + note_number + '/' + REVIEWERS_NAME;
      PAPER_AREACHAIRS = CONFERENCE_ID + '/Paper' + note_number + '/' + AREA_CHAIRS_NAME;
      PAPER_AUTHORS = CONFERENCE_ID + '/Paper' + note_number + '/' + AUTHORS_NAME;

      var areachair_mail = {
        "groups": [PAPER_AREACHAIRS],
        "subject": "[" + SHORT_PHRASE + "] Review posted to your assigned paper: \"" + forum.content.title + "\"",
        "message": "A submission to " + SHORT_PHRASE + ", for which you are an official area chair, has received an official review. \n\nTitle: " + note.content.title + "\n\nComment: " + note.content.review + "\n\nTo view the review, click here: " + baseUrl + "/forum?id=" + note.forum
      };
      var author_mail = {
        "groups": [PAPER_AUTHORS],
        "subject": "[" + SHORT_PHRASE + "] Review posted to your submission: \"" + forum.content.title + "\"",
        "message": "Your submission to " + SHORT_PHRASE + " has received an official review. \n\nTitle: " + note.content.title + "\n\nComment: " + note.content.review + "\n\nTo view the review, click here: " + baseUrl + "/forum?id=" + note.forum
      };
      var areachairMailP = or3client.or3request( or3client.mailUrl, areachair_mail, 'POST', token );
      var authorMailP = or3client.or3request( or3client.mailUrl, author_mail, 'POST', token );

      return Promise.all([areachairMailP, authorMailP]);
    })
    .then(result => done())
    .catch(error => done(error));
    return true;
  };
