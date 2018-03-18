#!/usr/bin/python
# -*- coding: utf-8 -*-
import openreview
import tools

def get_conflicts(author_profiles, user_profile):

    authors_domain_conflicts = set()
    authors_relation_conflicts = set()
    conflicts = set()

    for p in author_profiles.values():
        author_domain_conflicts, author_relation_conflicts = get_profile_conflicts(p)

        authors_domain_conflicts.update(author_domain_conflicts)
        authors_relation_conflicts.update(author_relation_conflicts)


	user_domain_conflicts, user_relation_conflicts = get_profile_conflicts(user_profile)

	conflicts.update(authors_domain_conflicts.intersection(user_domain_conflicts))
	conflicts.update(authors_relation_conflicts.intersection(user_relation_conflicts))

	return list(conflicts)

def get_profile_conflicts(profile):
    domain_conflicts = set()
    relation_conflicts = set()

    profile_domains = []
    for e in profile.content['emails']:
        profile_domains += tools.subdomains(e)

    domain_conflicts.update(profile_domains)

    institution_domains = [h['institution']['domain'] for h in profile.content['history']]
    domain_conflicts.update(institution_domains)

    if 'relations' in profile.content:
        relation_conflicts.update([r['email'] for r in profile.content['relations']])

    if 'gmail.com' in domain_conflicts:
        domain_conflicts.remove('gmail.com')

    return (domain_conflicts, relation_conflicts)
