function(){
    var or3client = lib.or3client;

    var CONFERENCE_ID = '';
    var SHORT_PHRASE = '';
    var AUTHORS_NAME = '';
    var PROGRAM_CHAIRS_ID = '';
    var USE_AREA_CHAIRS = false;

    var forumNote = or3client.or3request(or3client.notesUrl+'?id='+note.forum, {}, 'GET', token);
    var reviewNote = or3client.or3request(or3client.notesUrl+'?id='+note.replyto, {}, 'GET', token);

    Promise.all([forumNote, reviewNote]).then(function([result1, result2]) {
      var forum = result1.notes[0];
      var review = result2.notes[0];
      var promises = [];

      var AUTHORS_ID = CONFERENCE_ID + '/Paper' + forum.number + '/' + AUTHORS_NAME;
      //TODO: use the variable instead, when we have anonymous groups integrated
      var REVIEWERS_ID = CONFERENCE_ID + '/Paper' + forum.number + '/Reviewers';
      var AREA_CHAIRS_ID = CONFERENCE_ID + '/Paper' + forum.number + '/Area_Chairs';
      var ignoreGroups = note.nonreaders || [];
      ignoreGroups.push(note.tauthor);

      var content = 'To view the rebuttal, click here: ' + baseUrl + '/forum?id=' + note.forum + '&noteId=' + note.id;

      if (PROGRAM_CHAIRS_ID) {
        var program_chair_mail = {
          groups: [PROGRAM_CHAIRS_ID],
          ignoreGroups: ignoreGroups,
          subject: '[' + SHORT_PHRASE + '] A rebuttal has been received on Paper number: ' + forum.number + ', Paper title: "' + forum.content.title + '"',
          message: 'We have received a review rebuttal on a submission to ' + SHORT_PHRASE + '.\n\n' + content
        };
        promises.push(or3client.or3request( or3client.mailUrl, program_chair_mail, 'POST', token ));
      }

      var authors_writer_mail = {
        groups: note.signatures,
        subject: '[' + SHORT_PHRASE + '] Your rebuttal has been received on your submission - Paper number: ' + forum.number + ', Paper title: "' + forum.content.title + '"',
        message: 'We have received your rebuttal on your submission to ' + SHORT_PHRASE + '.\n\nPaper number: ' + forum.number + '\n\nPaper title: ' + forum.content.title + '\n\n' + content
      };
      promises.push(or3client.or3request( or3client.mailUrl, authors_writer_mail, 'POST', token ));

      if (USE_AREA_CHAIRS && (note.readers.includes('everyone') || note.readers.includes(AREA_CHAIRS_ID))) {
        var areachair_mail = {
          groups: [AREA_CHAIRS_ID],
          ignoreGroups: ignoreGroups,
          subject : '[' + SHORT_PHRASE + '] Rebuttal posted to your assigned Paper number: ' + forum.number + ', Paper title: "' + forum.content.title + '"',
          message: 'A submission to ' + SHORT_PHRASE + ', for which you are an official area chair, has received a rebuttal. \n\nPaper number: ' + forum.number + '\n\nPaper title: ' + forum.content.title + '\n\n' + content
        };
        promises.push(or3client.or3request( or3client.mailUrl, areachair_mail, 'POST', token ));
      }

      var reviewers_submitted = REVIEWERS_ID + '/Submitted';
      if (note.readers.includes('everyone') || note.readers.includes(REVIEWERS_ID)) {
        var reviewer_mail = {
          groups: [REVIEWERS_ID],
          ignoreGroups: review.signatures,
          subject: '[' + SHORT_PHRASE + '] Rebuttal posted to your assigned Paper number: ' + forum.number + ', Paper title: "' + forum.content.title + '"',
          message: 'A submission to ' + SHORT_PHRASE + ', for which you are a reviewer, has received a rebuttal. \n\nPaper number: ' + forum.number + '\n\nPaper title: ' + forum.content.title + '\n\n' + content
        };
        promises.push(or3client.or3request( or3client.mailUrl, reviewer_mail, 'POST', token ));
      } else if (note.readers.includes(reviewers_submitted)) {
        var reviewer_mail = {
          groups: [reviewers_submitted],
          ignoreGroups: review.signatures,
          subject: '[' + SHORT_PHRASE + '] Rebuttal posted to your assigned Paper number: ' + forum.number + ', Paper title: "' + forum.content.title + '"',
          message: 'A submission to ' + SHORT_PHRASE + ', for which you are a reviewer, has received a rebuttal. \n\nPaper number: ' + forum.number + '\n\nPaper title: ' + forum.content.title + '\n\n' + content
        };
        promises.push(or3client.or3request( or3client.mailUrl, reviewer_mail, 'POST', token ));
      }

      var review_signature_mail = {
        groups: review.signatures,
        subject : '[' + SHORT_PHRASE + '] Rebuttal posted to your review submitted - Paper number: ' + forum.number + ', Paper title: "' + forum.content.title + '"',
        message: 'A submission to ' + SHORT_PHRASE + ', for which you are a reviewer, has received a rebuttal. \n\nPaper number: ' + forum.number + '\n\nPaper title: ' + forum.content.title + '\n\n' + content
      };
      promises.push(or3client.or3request( or3client.mailUrl, review_signature_mail, 'POST', token ));

      return Promise.all(promises);
    })
    .then(result => done())
    .catch(error => done(error));
    return true;
  };
