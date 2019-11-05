function() {
    var or3client = lib.or3client;
    var SHORT_PHRASE = '';
    var userMail = {
        groups: note.content.user,
        subject: SHORT_PHRASE + ' has received your request for reduced load',
        message: 'Your request to ' + SHORT_PHRASE + ' for reduced load has been received.'
    };
    or3client.or3request(or3client.mailUrl, authorMail, 'POST', token)
    .then(result => done())
    .catch(error => done(error));
    return true;
}