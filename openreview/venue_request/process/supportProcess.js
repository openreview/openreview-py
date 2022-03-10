function(){
    var or3client = lib.or3client;
    var GROUP_PREFIX = '';
    var SUPPORT_GROUP = GROUP_PREFIX + '/Support';
    var baseUrl = 'https://openreview.net'
    var SUPER_USER = '~Super_User1'

    var adminMessage = 'A request for service has been submitted by ' + note.content['Abbreviated Venue Name'] + '. Check it here: ' + baseUrl + '/forum?id=' + note.forum + '\n'

    for (key in note.content) {
      adminMessage = adminMessage.concat('\n' + key + ': ' + note.content[key])
    }

    var openreviewMailPayload = {
      groups: [SUPPORT_GROUP],
      subject: 'A request for service has been submitted by ' + note.content['Abbreviated Venue Name'],
      message: adminMessage
    };

    var programchairMailPayload = {
      groups: note.content['program_chair_emails'],
      subject: 'Your request for OpenReview service has been received.',
      message: 'Thank you for choosing OpenReview to host your upcoming venue. We are reviewing your request and will post a comment on the request forum when the venue is deployed. You can access the request forum here: ' + baseUrl + '/forum?id=' + note.forum
    };

    var commentInvitation = {
      id: SUPPORT_GROUP + '/-/Request' + note.number + '/Comment',
      super: SUPPORT_GROUP + '/-/Comment',
      reply: {
        forum: note.forum,
        replyto: null,
        readers: {
            values: note.content['program_chair_emails'].concat([SUPPORT_GROUP])
        }
      },
      writers: [SUPPORT_GROUP],
      signatures: [SUPER_USER]
    }

    var deployInvitation = {
      id: SUPPORT_GROUP + '/-/Request' + note.number + '/Deploy',
      super: SUPPORT_GROUP + '/-/Deploy',
      reply: {
        referent: note.forum,
        forum: note.forum
      },
      writers: [SUPPORT_GROUP],
      signatures: [GROUP_PREFIX]
    }

    or3client.or3request(or3client.mailUrl, openreviewMailPayload, 'POST', token)
    .then(result => or3client.or3request(or3client.mailUrl, programchairMailPayload, 'POST', token))
    .then(result => or3client.or3request(or3client.inviteUrl, commentInvitation, 'POST', token))
    .then(result => or3client.or3request(or3client.inviteUrl, deployInvitation, 'POST', token))
    .then(result => done())
    .catch(error => done(error));

    return true;
};
