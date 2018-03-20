#!/usr/bin/python
# -*- coding: utf-8 -*-
import openreview

def get_conflicts(author_profiles, user_profile):

    author_domains = set()
    author_emails = set()
    author_relations = set()

    for author_email, profile in author_profiles.iteritems():

        author_info = get_author_info(profile, author_email)

        author_domains.update(author_info['domains'])
        author_emails.update(author_info['emails'])
        author_relations.update(author_info['relations'])

    user_info = get_profile_info(user_profile)

    conflicts = set()
    conflicts.update(author_domains.intersection(user_info['domains']))
    conflicts.update(author_relations.intersection(user_info['emails']))
    conflicts.update(author_emails.intersection(user_info['relations']))

    return list(conflicts)

def get_author_info(profile, email):
    if profile:
        return get_profile_info(profile)
    else:
        return {
            'domains': get_domains(email, subdomains = True),
            'emails': [email],
            'relations': []
        }


def get_profile_info(profile):

    domains = set()
    emails = set()
    relations = set()

    ## Emails section
    for e in profile.content['emails']:
        domains.update(get_domains(e, subdomains = True))
        emails.add(e)

    ## Institution section
    for h in profile.content.get('history', []):
        domain = h.get('institution', {}).get('domain', '')
        domains.update(get_domains(domain, subdomains = True))


    ## Relations section
    relations.update([r['email'] for r in profile.content.get('relations', [])])

    ## Filter common domains
    if 'gmail.com' in domains:
        domains.remove('gmail.com')

    return {
        'domains': domains,
        'emails': emails,
        'relations': relations
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
