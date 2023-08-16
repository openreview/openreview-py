function(){
    // V1 invitation

    const tokens = ['fullname', 'invitee_role', 'invitation_url', 'contact_info', 'reviewer_name', 'accept_url', 'decline_url'];
    const fields = ['invitation_email_subject', 'invitation_email_content', 'accepted_email_template'];

    
    for (const field of fields) {
        if (field in note.content) {
            // Find all words wrapped in double curly braces. If it's not a token, raise an error.
            let regex = /{{([^{}]+)}}/g;
            let parenthesizedToken = '';
            let match;
            while ((match = regex.exec(note.content[field])) !== null) {
                parenthesizedToken = match[1];
                if (!tokens.includes(parenthesizedToken)) {
                    done(`Invalid token: {{${parenthesizedToken}}} does not exist.`);
                }
            }

            // Check for tokens that don't have double curly braces, raise an error.
            for (const token of tokens) {
                regex = new RegExp(`(?<!{)[{]?${token}[}]+|[{]+${token}[}]?(?!})`, 'g');
                while ((match = regex.exec(note.content[field])) !== null) {
                    parenthesizedToken = match[0];
                    done(`Invalid token: ${parenthesizedToken}. Tokens must be wrapped in double curly braces.`);
                }
            }
        }
    }
    done()
}
