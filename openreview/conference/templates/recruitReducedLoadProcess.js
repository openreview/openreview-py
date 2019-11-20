function() {
    var or3client = lib.or3client;
    var SHORT_PHRASE = '';
    var INVITEE_ROLE = '';
    var REVIEWERS_ACCEPTED_ID = '';
    var REVIEWERS_DECLINED_ID = '';
    var HASH_SEED = '';

    var hashKey = or3client.createHash(note.content.user, HASH_SEED);

    if (hashKey === note.content.key) {
        if (note.content.response === 'Yes') {
            console.log('Invitation replied Yes');
            //if a user is in the declined group, remove them from that group and add them to the reviewers group
            or3client.removeGroupMember(REVIEWERS_DECLINED_ID, note.content.user, token)
            .then(result => or3client.addGroupMember(REVIEWERS_ACCEPTED_ID, note.content.user, token))
            .then(result => done())
            .catch(error => done(error));

            var userMail = {
                groups: [note.content.user],
                subject: 'You have accepted to serve on the ' + INVITEE_ROLE + ' committee for ' + SHORT_PHRASE,
                message: 'This is to confirm that we have received your acceptance to serve on the ' + INVITEE_ROLE + ' committee. We have noted your reduced load to be ' + note.content.reduced_load + '.'
            };
            or3client.or3request(or3client.mailUrl, userMail, 'POST', token)
            .then(result => done())
            .catch(error => done(error));
            return true;
        }
    } else {
        done('Invalid key', note.content.key);
        return false;
    }
}