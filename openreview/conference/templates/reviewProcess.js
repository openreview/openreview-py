function(){
    var or3client = lib.or3client;

    var CONFERENCE_ID = '';
    var SHORT_PHRASE = '';
    var AUTHORS_NAME = '';
    var PROGRAM_CHAIRS_NAME = '';

    var forumNote = or3client.or3request(or3client.notesUrl+'?id='+note.forum, {}, 'GET', token);

    forumNote.then(function(result) {
      var forum = result.notes[0];
      var note_number = forum.number;
      var promises = [];

      PAPER_REVIEWERS = CONFERENCE_ID + '/Paper' + note_number + '/Reviewers';
      PAPER_AREACHAIRS = CONFERENCE_ID + '/Paper' + note_number + '/Area_Chairs';
      PAPER_AUTHORS = CONFERENCE_ID + '/Paper' + note_number + '/' + AUTHORS_NAME;
      REVIEWERS_SUBMITTED = PAPER_REVIEWERS + '/Submitted';

      if (PROGRAM_CHAIRS_NAME){
        console.log('sending email to pc boss!');
        console.log(CONFERENCE_ID + '/' + PROGRAM_CHAIRS_NAME);
        var program_chair_mail = {
          groups: [CONFERENCE_ID + '/' + PROGRAM_CHAIRS_NAME],
          subject: '[' + SHORT_PHRASE + '] A review has been received on paper: "' + forum.content.title + '"',
          message: 'We have received a review on a submission to ' + SHORT_PHRASE + '.\n\nPaper title: ' + forum.content.title + '\n\nReview title: ' + note.content.title + '\n\nReview comment: ' + note.content.review + '\n\nTo view the review, click here: ' + baseUrl + '/forum?id=' + note.forum + '&noteId=' + note.id
        };
        promises.push(or3client.or3request( or3client.mailUrl, program_chair_mail, 'POST', token ));
      }

      var review_writer_mail = {
        groups: note.signatures,
        subject: '[' + SHORT_PHRASE + '] Your review has been received on your assigned paper: "' + forum.content.title + '"',
        message: 'We have received your review on a submission to ' + SHORT_PHRASE + '.\n\nPaper title: ' + forum.content.title + '\n\n Review title: ' + note.content.title + '\n\nReview comment: ' + note.content.review + '\n\nTo view the review, click here: ' + baseUrl + '/forum?id=' + note.forum + '&noteId=' + note.id
      };
      promises.push(or3client.or3request( or3client.mailUrl, review_writer_mail, 'POST', token ));

      if (note.readers.includes('everyone') || note.readers.includes(PAPER_AREACHAIRS)) {
        var areachair_mail = {
          groups: [PAPER_AREACHAIRS],
          subject : '[' + SHORT_PHRASE + '] Review posted to your assigned paper: "' + forum.content.title + '"',
          message: 'A submission to ' + SHORT_PHRASE + ', for which you are an official area chair, has received a review. \n\nTitle: ' + note.content.title + '\n\nComment: ' + note.content.review + '\n\nTo view the review, click here: ' + baseUrl + '/forum?id=' + note.forum + '&noteId=' + note.id
        };
        promises.push(or3client.or3request( or3client.mailUrl, areachair_mail, 'POST', token ));
      }

      if (note.readers.includes('everyone') || note.readers.includes(PAPER_REVIEWERS)) {
        var reviewer_mail = {
          groups: [PAPER_REVIEWERS],
          ignoreGroups: [note.tauthor],
          subject: '[' + SHORT_PHRASE + '] Review posted to your assigned paper: "' + forum.content.title + '"',
          message: 'A submission to ' + SHORT_PHRASE + ', for which you are a reviewer, has received a review. \n\nTitle: ' + note.content.title + '\n\nComment: ' + note.content.review + '\n\nTo view the review, click here: ' + baseUrl + '/forum?id=' + note.forum + '&noteId=' + note.id
        };
        promises.push(or3client.or3request( or3client.mailUrl, reviewer_mail, 'POST', token ));
      }

      if (note.readers.includes('everyone') || note.readers.includes(PAPER_AUTHORS)) {
        var author_mail = {
          groups: [PAPER_AUTHORS],
          subject: '[' + SHORT_PHRASE + '] Review posted to your submission: "' + forum.content.title + '"',
          message: 'Your submission to ' + SHORT_PHRASE + ' has received a review. \n\nTitle: ' + note.content.title + '\n\nComment: ' + note.content.review + '\n\nTo view the review, click here: ' + baseUrl + '/forum?id=' + note.forum + '&noteId=' + note.id
        };
        promises.push(or3client.or3request( or3client.mailUrl, author_mail, 'POST', token ));
      }

      return Promise.all(promises)
      .then(function(result){
        return or3client.addGroupMember(REVIEWERS_SUBMITTED, note.signatures[0], token);
      })
    })
    .then(result => done())
    .catch(error => done(error));
    return true;
  };
