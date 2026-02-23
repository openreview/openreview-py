def process(client, edit, invitation):
    """
    Preprocess function for Submission/Form_Fields invitations.
    Validates that venue and venueid fields cannot be deleted.
    """
    
    # Get the content that is being edited
    content = edit.content.get('content', {}).get('value', {})
    
    # Check if venue or venueid are being deleted
    protected_fields = ['venue', 'venueid']
    
    for field in protected_fields:
        if field in content:
            field_value = content[field]
            # Check if the field is being deleted
            if isinstance(field_value, dict) and field_value.get('delete') is True:
                raise openreview.OpenReviewException(f'The field "{field}" cannot be deleted as it is a required system field.')
