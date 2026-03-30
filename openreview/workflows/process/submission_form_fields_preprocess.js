function process(client, edit, invitation) {
  // Preprocess function for Submission/Form_Fields invitations.
  // Validates that venue and venueid fields cannot be deleted.
  
  // Get the content that is being edited
  const content = edit.content?.content?.value || {};
  
  // Check if venue or venueid are being deleted
  const protectedFields = ['venue', 'venueid'];
  
  for (const field of protectedFields) {
    if (content[field]) {
      const fieldValue = content[field];
      // Check if the field is being deleted
      if (fieldValue.delete === true) {
        return Promise.reject(
          new OpenReviewError({ 
            name: 'Error', 
            message: `The field "${field}" cannot be deleted as it is a required system field.` 
          })
        );
      }
    }
  }
  
  return Promise.resolve();
}
