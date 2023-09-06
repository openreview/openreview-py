function(){
    // V1 invitation

    const fieldTokens = {
        "invitation_email_subject": ['invitee_role'],
        "invitation_email_content": ['fullname', 'invitee_role', 'invitation_url', 'contact_info'],
        "accepted_email_template": ['fullname', 'reviewer_name']
    };

    for (const [field, tokens] of Object.entries(fieldTokens)) {
        if (field in note.content) {
            // Find all words wrapped in double curly braces. If it's not a token, raise an error.
            let regex = /{{([^{}]+)}}/g;
            let parenthesizedToken = '';
            let match;
            while ((match = regex.exec(note.content[field])) !== null) {
                parenthesizedToken = match[1];
                if (!tokens.includes(parenthesizedToken)) {
                    done(`Invalid token: {{${parenthesizedToken}}} in ${field} is not supported. Please use the following tokens in this field: ${tokens.toString()}.`);
                }
            }

            // Check for tokens that don't have double curly braces, raise an error.
            for (const token of tokens) {
                regex = new RegExp(`(?<!{)[{]?${token}[}]+|[{]+${token}[}]?(?!})`, 'g');
                while ((match = regex.exec(note.content[field])) !== null) {
                    parenthesizedToken = match[0];
                    done(`Invalid token: ${parenthesizedToken} in ${field}. Tokens must be wrapped in double curly braces.`);
                }
            }
        }
    }
    done()
}
