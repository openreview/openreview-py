function(){
    var or3client = lib.or3client;

    var CONFERENCE_ID = '';
    var SHORT_PHRASE = '';
    var AUTHORS_NAME = '';
    var REVIEWERS_NAME = '';
    var AREA_CHAIRS_NAME = '';
    var SENIOR_AREA_CHAIRS_NAME = '';
    var PROGRAM_CHAIRS_ID = '';
    var USE_AREA_CHAIRS = false;
    var EMAIL_PCs = false;

    or3client.or3request(or3client.notesUrl + '?id=' + note.forum, {}, 'GET', token)
    .then(function(result) {

      var forumNote = result.notes[0];
      var AUTHORS_ID = CONFERENCE_ID + '/Paper' + forumNote.number + '/' + AUTHORS_NAME;
      //TODO: use the variable instead, when we have anonymous groups integrated
      var REVIEWERS_ID = CONFERENCE_ID + '/Paper' + forumNote.number + '/Reviewers';
      var AREA_CHAIRS_ID = CONFERENCE_ID + '/Paper' + forumNote.number + '/Area_Chairs';
      var SENIOR_AREA_CHAIRS_ID = CONFERENCE_ID + '/Paper' + forumNote.number + '/Senior_Area_Chairs';
      var ignoreGroups = note.nonreaders || [];
      var signature = note.signatures[0].split('/').slice(-1)[0];
      var prettySignature = signature.startsWith('~') ? signature.replace(/~|\d+/g, '').replace(/_/g, ' ') : signature.replace(/_/g, ' ')
      prettySignature = prettySignature == 'Authors' ? 'An author' : prettySignature;
      ignoreGroups.push(note.tauthor);
      var content = `

Paper Number: ${forumNote.number}

Paper Title: "${forumNote.content.title}"

Comment title: ${note.content.title}

Comment: ${note.content.comment}

To view the comment, click here: ${baseUrl}/forum?id=${note.forum}&noteId=${note.id}`

      var ac_mail = {
        groups: [AREA_CHAIRS_ID],
        ignoreGroups: ignoreGroups,
        subject: `[${SHORT_PHRASE}] ${prettySignature} commented on a paper in your area. Paper Number: ${forumNote.number}, Paper Title: "${forumNote.content.title}"`,
        message: `${prettySignature} commented on a paper for which you are serving as Area Chair.${content}`
      };

      var comment_author_mail = {
        groups: [note.tauthor],
        subject: '[' + SHORT_PHRASE + '] Your comment was received on Paper Number: ' + forumNote.number + ', Paper Title: "' + forumNote.content.title + '"',
        message: `Your comment was received on a submission to ${SHORT_PHRASE}.${content}`
      };

      var paper_author_mail = {
        groups: forumNote.content.authorids,
        ignoreGroups: ignoreGroups,
        subject: `[${SHORT_PHRASE}] ${prettySignature} commented on your submission. Paper Number: ${forumNote.number}, Paper Title: "${forumNote.content.title}"`,
        message: `${prettySignature} commented on your submission.${content}`
      };

      var promises = [];

      promises.push(or3client.or3request(or3client.mailUrl, comment_author_mail, 'POST', token));

      if(note.readers.includes(AUTHORS_ID) || note.readers.includes('everyone')){
        promises.push(or3client.or3request(or3client.mailUrl, paper_author_mail, 'POST', token));
      }

      var reviewers_submitted = REVIEWERS_ID + '/Submitted';
      if (note.readers.includes('everyone') || note.readers.includes(REVIEWERS_ID)){
        var reviewer_mail = {
          groups: [REVIEWERS_ID],
          ignoreGroups: ignoreGroups,
          subject: `[${SHORT_PHRASE}] ${prettySignature} commented on a paper you are reviewing. Paper Number: ${forumNote.number}, Paper Title: "${forumNote.content.title}"`,
          message: `${prettySignature} commented on a paper for which you are serving as reviewer.${content}`
        };
        promises.push(or3client.or3request( or3client.mailUrl, reviewer_mail, 'POST', token ));
      } else if (note.readers.includes(reviewers_submitted)) {
        var reviewer_mail = {
          groups: [reviewers_submitted],
          ignoreGroups: ignoreGroups,
          subject: `[${SHORT_PHRASE}] ${prettySignature} commented on a paper you are reviewing. Paper Number: ${forumNote.number}, Paper Title: "${forumNote.content.title}"`,
          message: `${prettySignature} commented on a paper for which you are serving as reviewer.${content}`
        };
        promises.push(or3client.or3request( or3client.mailUrl, reviewer_mail, 'POST', token ));
      } else {
        var anonReviewers = note.readers.filter(reader => reader.indexOf('AnonReviewer') >= 0 || reader.indexOf('Reviewer_') >= 0);
        if (anonReviewers.length) {
          var reviewer_mail = {
            groups: anonReviewers,
            ignoreGroups: ignoreGroups,
            subject: `[${SHORT_PHRASE}] ${prettySignature} commented on a paper you are reviewing. Paper Number: ${forumNote.number}, Paper Title: "${forumNote.content.title}"`,
            message: `${prettySignature} commented on a paper for which you are serving as reviewer.${content}`
          };
          promises.push(or3client.or3request( or3client.mailUrl, reviewer_mail, 'POST', token ));
        }
      }

      if(USE_AREA_CHAIRS && (note.readers.includes(AREA_CHAIRS_ID) || note.readers.includes('everyone'))){
        promises.push(or3client.or3request(or3client.mailUrl, ac_mail, 'POST', token));
      }

      var email_SAC = note.readers.length==3 && note.readers.includes(SENIOR_AREA_CHAIRS_ID) && note.readers.includes(PROGRAM_CHAIRS_ID)
      if(SENIOR_AREA_CHAIRS_NAME && email_SAC){
        var SAC_mail = {
          groups: [SENIOR_AREA_CHAIRS_ID],
          ignoreGroups: ignoreGroups,
          subject: `[${SHORT_PHRASE}] ${prettySignature} commented on a paper in your area. Paper Number: ${forumNote.number}, Paper Title: "${forumNote.content.title}"`,
          message: `${prettySignature} commented on a paper for which you are serving as Senior Area Chair.${content}`
        };
        promises.push(or3client.or3request( or3client.mailUrl, SAC_mail, 'POST', token ));
      }

      if(EMAIL_PCs && (note.readers.includes(PROGRAM_CHAIRS_ID) || note.readers.includes('everyone'))){

        var pc_mail = {
          groups: [PROGRAM_CHAIRS_ID],
          ignoreGroups: ignoreGroups,
          subject: `[${SHORT_PHRASE}] ${prettySignature} commented on a paper. Paper Number: ${forumNote.number}, Paper Title: "${forumNote.content.title}"`,
          message: `${prettySignature} commented on a paper for which you are serving as Program Chair.${content}`
        };

        promises.push(or3client.or3request(or3client.mailUrl, pc_mail, 'POST', token));
      }

      return Promise.all(promises);
    })
    .then(result => done())
    .catch(error => done(error));

    return true;
};
