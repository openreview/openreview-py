function(){
    var or3client = lib.or3client;
    var baseUrl = 'https://openreview.net'

    var adminMessage = 'A request for service has been submitted. Check it here: ' + baseUrl + '/forum?id=' + note.forum + '\n'

    for (key in note.content) {
      adminMessage = adminMessage.concat('\n' + key + ': ' + note.content[key])
    }

    var openreviewMailPayload = {
      groups: ['OpenReview.net/Support'],
      subject: 'A request for service has been submitted',
      message: adminMessage
    };

    var programchairMailPayload = {
      groups: note.content['program_chair_emails'],
      subject: 'Your request for OpenReview service has been received.',
      message: 'You recently requested conference management services from OpenReview. A member of our support team will contact you shortly. You can view the request here: ' + baseUrl + '/forum?id=' + note.forum
    };

    var commentInvitation = {
      id: 'OpenReview.net/Support/-/Request' + note.number + '/Comment',
      super: 'OpenReview.net/Support/-/Comment',
      reply: {
        forum: note.forum,
        replyto: null,
        readers: {
            values: note.content['program_chair_emails'].concat(['OpenReview.net/Support'])
        }
      },
      writers: ['OpenReview.net/Support'],
      signatures: ['OpenReview.net/Support']
    }

    var deployInvitation = {
      id: 'OpenReview.net/Support/-/Request' + note.number + '/Deploy',
      super: 'OpenReview.net/Support/-/Deploy',
      reply: {
        referent: note.forum,
        forum: note.forum
      },
      writers: ['OpenReview.net/Support'],
      signatures: ['OpenReview.net']
    }

    or3client.or3request(or3client.mailUrl, openreviewMailPayload, 'POST', token)
    .then(result => or3client.or3request(or3client.mailUrl, programchairMailPayload, 'POST', token))
    .then(result => or3client.or3request(or3client.inviteUrl, commentInvitation, 'POST', token))
    .then(result => or3client.or3request(or3client.inviteUrl, deployInvitation, 'POST', token))
    .then(result => done())
    .catch(error => done(error));

    return true;
};
