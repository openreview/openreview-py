#!/usr/bin/python
# -*- coding: utf-8 -*-
import openreview

def get_conflicts(author_profiles, user_profile):

    authors_domain_conflicts = set()
    authors_email_conflicts = set()
    authors_relation_conflicts = set()

    for author_email, profile in author_profiles.iteritems():

        author_conflicts = get_author_conflicts(profile, author_email)

        authors_domain_conflicts.update(author_conflicts['domains'])
        authors_email_conflicts.update(author_conflicts['emails'])
        authors_relation_conflicts.update(author_conflicts['relations'])

    user_conflicts = get_profile_conflicts(user_profile)

    conflicts = set()
    conflicts.update(authors_domain_conflicts.intersection(user_conflicts['domains']))
    conflicts.update(authors_relation_conflicts.intersection(user_conflicts['emails']))
    conflicts.update(authors_email_conflicts.intersection(user_conflicts['relations']))

    return list(conflicts)

def get_author_conflicts(profile, email):
    if profile:
        return get_profile_conflicts(profile)
    else:
        return {
            'domains': get_domains(email, subdomains = True),
            'emails': [email],
            'relations': [email] ## Should I keep adding profile emails?
        }


def get_profile_conflicts(profile):

    domain_conflicts = set()
    email_conflicts = set()
    relation_conflicts = set()

    ## Emails section
    for e in profile.content['emails']:
        domain_conflicts.update(get_domains(e, subdomains = True))
        email_conflicts.add(e)

    ## Institution section
    for h in profile.content.get('history', []):
        domain = h.get('institution', {}).get('domain', '')
        domain_conflicts.update(get_domains(domain, subdomains = True))


    ## Relations section
    relation_conflicts.update([r['email'] for r in profile.content.get('relations', [])])
    relation_conflicts.update(profile.content['emails']) ## Should I keep adding profile emails?

    ## Filter common domains
    if 'gmail.com' in domain_conflicts:
        domain_conflicts.remove('gmail.com')

    return {
        'domains': domain_conflicts,
        'emails': email_conflicts,
        'relations': relation_conflicts
    }

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
