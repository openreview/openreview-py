#!/usr/bin/python
# -*- coding: utf-8 -*-
import openreview

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
        profile_domains += get_domains(e, subdomains = True)
    domain_conflicts.update(profile_domains)

    institution_domains = []
    for h in profile.content.get('history', []):
        domain = h.get('institution', {}).get('domain', None)
        if domain:
            institution_domains += get_domains(domain, subdomains = True)
    domain_conflicts.update(institution_domains)

    domain_conflicts.update(institution_domains)

    relation_conflicts.update([get_domains(r['email'], subdomains = False) for r in profile.content.get('relations', [])])

    if 'gmail.com' in domain_conflicts:
        domain_conflicts.remove('gmail.com')

    return (domain_conflicts, relation_conflicts)

def get_domains(entity, subdomains = False):

    if '@' in entity:
        full_domain = entity.split('@')[1]
    else:
        full_domain = entity

    if subdomains:
        domain_components = full_domain.split('.')
        domains = ['.'.join(domain_components[index:len(domain_components)]) for index, path in enumerate(domain_components)]
        valid_domains = [d for d in domains if '.' in d]
        return valid_domains
    else:
        return full_domain
