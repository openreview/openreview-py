#!/usr/bin/python
from openreview import *

super_user_id = 'OpenReview.net'

def create_profile(client, email, first, last, middle = None):

	response = client.get_tildeusername(first, last, middle)
	tilde_id = response['username']

	tilde_group = Group(id = tilde_id, signatures = [super_user_id], signatories = [tilde_id], readers = [tilde_id], writers = [super_user_id], members = [email])
	email_group = Group(id = email, signatures = [super_user_id], signatories = [email], readers = [email], writers = [super_user_id], members = [tilde_id])
	profile_content = {
        'emails': [email],
        'preferred_email': email,
        'names': [
            {
                'first': first,
                'middle': middle,
                'last': last,
                'username': tilde_id
            }
        ]
    }
	client.post_group(tilde_group)
	client.post_group(email_group)
	profile = client.post_profile(tilde_id, profile_content)

	return profile


