function processUpdate() {
  var or3client = lib.or3client;

  var CONFERENCE_ID = '';
  var SHORT_PHRASE = '';
  var PROGRAM_CHAIRS_ID = '';
  var AREA_CHAIRS_ID = '';
  var OFFICIAL_REVIEW_NAME = '';
  var CREATE_GROUPS = false;
  var ANON_IDS = false;
  var DEANONYMIZERS = [];
  var SUBMISSION_EMAIL = '';

  var authorSubject = SHORT_PHRASE + ' has received your submission titled ' + note.content.title;
  var noteAbstract = (note.content.abstract ? `\n\nAbstract: ${note.content.abstract}` : '');
  var action = note.ddate ? 'deleted' : (existingNote ? 'updated' : 'posted');
  var authorMessage = `Your submission to ${SHORT_PHRASE} has been ${action}.\n\nSubmission Number: ${note.number} \n\nTitle: ${note.content.title} ${noteAbstract} \n\nTo view your submission, click here: ${baseUrl}/forum?id=${note.forum}`;
  if (SUBMISSION_EMAIL) {
    authorMessage = SUBMISSION_EMAIL;
  }
  var messages = [];

  messages.push({
    groups: [note.tauthor],
    subject: authorSubject,
    message: authorMessage
  });

  if (note.content.authorids && note.content.authorids.length) {
    authorMessage += `\n\nIf you are not an author of this submission and would like to be removed, please contact the author who added you at ${note.tauthor}`;
    messages.push({
      groups: note.content.authorids,
      ignoreGroups: [note.tauthor],
      subject: authorSubject,
      message: authorMessage
    })
  }

  let createGroups = async function() {
    if (CREATE_GROUPS && action == 'posted') {
      let committee = [CONFERENCE_ID];
      if (AREA_CHAIRS_ID) {
        committee.push(AREA_CHAIRS_ID);
      }
      const paperGroup = {
        id: CONFERENCE_ID + '/Paper' + note.number,
        signatures: [CONFERENCE_ID],
        writers: committee,
        members: [],
        readers: committee,
        signatories: committee
      };

      await or3client.or3request(or3client.grpUrl, paperGroup, 'POST', token);

      const authorGroupId = paperGroup.id + '/Authors';
      const authorGroup = {
        id: authorGroupId,
        signatures: [CONFERENCE_ID],
        writers: [CONFERENCE_ID],
        members: note.content.authorids.concat(note.signatures),
        readers: [CONFERENCE_ID, authorGroupId],
        signatories: [CONFERENCE_ID, authorGroupId]
      };

      await or3client.or3request(or3client.grpUrl, authorGroup, 'POST', token);

      const reviewerGroupId = paperGroup.id + '/Reviewers';
      const reviewerGroup = {
        id: reviewerGroupId,
        signatures: [CONFERENCE_ID],
        writers: committee,
        members: [],
        readers: committee.concat(reviewerGroupId),
        signatories: committee,
        nonreaders: [authorGroupId],
        anonids: ANON_IDS,
        deanonymizers: DEANONYMIZERS.map(d => d.replace('{number}', note.number))
      };

      await or3client.or3request(or3client.grpUrl, reviewerGroup, 'POST', token);

      const reviewerSubmittedGroupId = reviewerGroupId + '/Submitted';
      const reviewerSubmittedGroup = {
        id: reviewerSubmittedGroupId,
        signatures: [CONFERENCE_ID],
        writers: committee,
        members: [],
        readers: committee.concat(reviewerSubmittedGroupId),
        signatories: committee,
        nonreaders: [authorGroupId]
      };

      await or3client.or3request(or3client.grpUrl, reviewerSubmittedGroup, 'POST', token);

      if (OFFICIAL_REVIEW_NAME) {
        const officialReviewInvitation = {
          id: paperGroup.id + '/-/' + OFFICIAL_REVIEW_NAME,
          super: CONFERENCE_ID + '/-/' + OFFICIAL_REVIEW_NAME,
          signatures: [CONFERENCE_ID],
          writers: [CONFERENCE_ID],
          invitees: [reviewerGroupId],
          reply: {
            forum: note.id,
            replyto: note.id,
            readers: {
              values: ['everyone'],
              description: "User groups that should be able to read this review."
            },
            writers: {
              'values-regex': paperGroup.id + ( ANON_IDS ? '/Reviewer_.*' : '/AnonReviewer.*' )
            },
            signatures: {
              'values-regex': paperGroup.id + ( ANON_IDS ? '/Reviewer_.*' : '/AnonReviewer.*' )
            }
          }
        };

        await or3client.or3request(or3client.inviteUrl, officialReviewInvitation, 'POST', token);
      }

    }

    return Promise.resolve();
  }

  let sendEmails = function() {
    var promises = messages.map(mailBody => or3client.or3request(or3client.mailUrl, mailBody, 'POST', token));

    if (PROGRAM_CHAIRS_ID && action == 'posted') {
      var pcsMail = {
        groups: [PROGRAM_CHAIRS_ID],
        subject: SHORT_PHRASE + ' has received a new submission titled ' + note.content.title,
        message: `A submission to ${SHORT_PHRASE} has been ${action}.

        Submission Number: ${note.number}
        Title: ${note.content.title} ${noteAbstract}

        To view the submission, click here: ${baseUrl}/forum?id=${note.forum}`
      };
      promises.push(or3client.or3request(or3client.mailUrl, pcsMail, 'POST', token));
    }
    return Promise.all(promises);
  }

  createGroups()
  .then(() => sendEmails())
  .then(() => done())
  .catch(error => done(error));

  return true;
}
