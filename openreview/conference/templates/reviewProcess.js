function(){
    var or3client = lib.or3client;

    var CONFERENCE_ID = '';
    var SHORT_PHRASE = '';
    var AUTHORS_NAME = '';
    var REVIEWERS_NAME = '';
    var AREA_CHAIRS_NAME = '';
    var PROGRAM_CHAIRS_ID = '';
    var USE_AREA_CHAIRS = false;

    var forumNote = or3client.or3request(or3client.notesUrl+'?id='+note.forum, {}, 'GET', token);

    forumNote.then(function(result) {
      var forum = result.notes[0];
      var promises = [];

      var AUTHORS_ID = CONFERENCE_ID + '/Paper' + forum.number + '/' + AUTHORS_NAME;
      //TODO: use the variable instead, when we have anonymous groups integrated
      var REVIEWERS_ID = CONFERENCE_ID + '/Paper' + forum.number + '/Reviewers';
      var AREA_CHAIRS_ID = CONFERENCE_ID + '/Paper' + forum.number + '/Area_Chairs';
      var AREA_CHAIR_1_ID = CONFERENCE_ID + '/Paper' + forum.number + '/Area_Chair1';
      var ignoreGroups = note.nonreaders || [];
      ignoreGroups.push(note.tauthor);

      if (PROGRAM_CHAIRS_ID) {
        var program_chair_mail = {
          groups: [PROGRAM_CHAIRS_ID],
          ignoreGroups: ignoreGroups,
          subject: '[' + SHORT_PHRASE + '] A review has been received on Paper number: ' + forum.number + ', Paper title: "' + forum.content.title + '"',
          message: 'We have received a review on a submission to ' + SHORT_PHRASE + '.\n\nPaper number: ' + forum.number + ', \n\nPaper title: ' + forum.content.title + '\n\nReview title: ' + note.content.title + '\n\nReview comment: ' + note.content.review + '\n\nTo view the review, click here: ' + baseUrl + '/forum?id=' + note.forum + '&noteId=' + note.id
        };
        promises.push(or3client.or3request( or3client.mailUrl, program_chair_mail, 'POST', token ));
      }

      var review_writer_mail = {
        groups: note.signatures,
        subject: '[' + SHORT_PHRASE + '] Your review has been received on your assigned Paper number: ' + forum.number + ', Paper title: "' + forum.content.title + '"',
        message: 'We have received your review on a submission to ' + SHORT_PHRASE + '.\n\nPaper number: ' + forum.number + '\n\nPaper title: ' + forum.content.title + '\n\n Review title: ' + note.content.title + '\n\nReview comment: ' + note.content.review + '\n\nTo view the review, click here: ' + baseUrl + '/forum?id=' + note.forum + '&noteId=' + note.id
      };
      promises.push(or3client.or3request( or3client.mailUrl, review_writer_mail, 'POST', token ));

      if (USE_AREA_CHAIRS && (note.readers.includes('everyone') || note.readers.includes(AREA_CHAIRS_ID))) {
        var areachair_mail = {
          groups: [AREA_CHAIR_1_ID],
          ignoreGroups: ignoreGroups,
          subject : '[' + SHORT_PHRASE + '] Review posted to your assigned Paper number: ' + forum.number + ', Paper title: "' + forum.content.title + '"',
          message: 'A submission to ' + SHORT_PHRASE + ', for which you are an official area chair, has received a review. \n\nPaper number: ' + forum.number + '\n\nPaper title: ' + forum.content.title + '\n\nReview title: ' + note.content.title + '\n\nReview comment: ' + note.content.review + '\n\nTo view the review, click here: ' + baseUrl + '/forum?id=' + note.forum + '&noteId=' + note.id
        };
        promises.push(or3client.or3request( or3client.mailUrl, areachair_mail, 'POST', token ));
      }

      var reviewers_submitted = REVIEWERS_ID + '/Submitted';
      if (note.readers.includes('everyone') || note.readers.includes(REVIEWERS_ID)) {
        var reviewer_mail = {
          groups: [REVIEWERS_ID],
          ignoreGroups: ignoreGroups,
          subject: '[' + SHORT_PHRASE + '] Review posted to your assigned Paper number: ' + forum.number + ', Paper title: "' + forum.content.title + '"',
          message: 'A submission to ' + SHORT_PHRASE + ', for which you are a reviewer, has received a review. \n\nPaper number: ' + forum.number + '\n\nPaper title: ' + forum.content.title + '\n\nReview title: ' + note.content.title + '\n\nReview comment: ' + note.content.review + '\n\nTo view the review, click here: ' + baseUrl + '/forum?id=' + note.forum + '&noteId=' + note.id
        };
        promises.push(or3client.or3request( or3client.mailUrl, reviewer_mail, 'POST', token ));
      } else if (note.readers.includes(reviewers_submitted)) {
        var reviewer_mail = {
          groups: [reviewers_submitted],
          ignoreGroups: ignoreGroups,
          subject: '[' + SHORT_PHRASE + '] Review posted to your assigned Paper number: ' + forum.number + ', Paper title: "' + forum.content.title + '"',
          message: 'A submission to ' + SHORT_PHRASE + ', for which you are a reviewer, has received a review. \n\nPaper number: ' + forum.number + '\n\nPaper title: ' + forum.content.title + '\n\nReview title: ' + note.content.title + '\n\nReview comment: ' + note.content.review + '\n\nTo view the review, click here: ' + baseUrl + '/forum?id=' + note.forum + '&noteId=' + note.id
        };
        promises.push(or3client.or3request( or3client.mailUrl, reviewer_mail, 'POST', token ));
      }

      if (note.readers.includes('everyone') || note.readers.includes(AUTHORS_ID)) {
        var author_mail = {
          groups: [AUTHORS_ID],
          ignoreGroups: ignoreGroups,
          subject: '[' + SHORT_PHRASE + '] Review posted to your submission - Paper number: ' + forum.number + ', Paper title: "' + forum.content.title + '"',
          message: 'Your submission to ' + SHORT_PHRASE + ' has received a review. \n\nTitle: ' + note.content.title + '\n\nComment: ' + note.content.review + '\n\nTo view the review, click here: ' + baseUrl + '/forum?id=' + note.forum + '&noteId=' + note.id
        };
        promises.push(or3client.or3request( or3client.mailUrl, author_mail, 'POST', token ));
      }

      return Promise.all(promises)
      .then(function(result) {
        return or3client.addGroupMember(reviewers_submitted, note.signatures[0], token);
      })
    })
    .then(result => done())
    .catch(error => done(error));
    return true;
  };
