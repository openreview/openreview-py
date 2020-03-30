function() {
    var or3client = lib.or3client;
    var SHORT_PHRASE = '';
    var REVIEWER_NAME = '';
    var REVIEWERS_ACCEPTED_ID = '';
    var REVIEWERS_DECLINED_ID = '';
    var HASH_SEED = '';

    var hashKey = or3client.createHash(note.content.user, HASH_SEED);

    if (hashKey === note.content.key) {
        if (note.content.response === 'Yes') {
            console.log('Invitation replied Yes');
            var text = 'Thank you for accepting the invitation to be a ' + REVIEWER_NAME + ' for ' + SHORT_PHRASE + '.\n';
            text += 'We have noted your request to review a maximum of ' + note.content.reviewer_load + ' submissions.\n';
            text += 'The ' + SHORT_PHRASE + ' program chairs will be contacting you with more information regarding next steps soon. ';
            text += 'In the meantime, please add noreply@openreview.net to your email contacts to ensure that you receive all communications.\n\n';
            text += 'If you would like to change your decision, please click the Decline link in the previous invitation email.';

            var email = {
                groups: [note.content.user],
                subject: '[' + SHORT_PHRASE + '] ' + REVIEWER_NAME + ' Invitation accepted',
                message: text
            };
            //if a user is in the declined group, remove them from that group and add them to the reviewers group
            or3client.removeGroupMember(REVIEWERS_DECLINED_ID, note.content.user, token)
            .then(result => or3client.addGroupMember(REVIEWERS_ACCEPTED_ID, note.content.user, token))
            .then(result => or3client.or3request(or3client.mailUrl, email, 'POST', token))
            .then(result => done())
            .catch(error => done(error));
            return true;
        }
    } else {
        done('Invalid key', note.content.key);
        return false;
    }
}