import openreview
import argparse

def replace_members_with_ids(client, group):
    '''
    Given a Group object, iterates through the Group's members and, for any member
    represented by an email address, attempts to find a profile associated with
    that email address. If a profile is found, replaces the email with the profile ID.

    Returns None.
    '''
    ids = []
    emails = []
    for member in group.members:
        if '~' not in member:
            try:
                profile = client.get_profile(member.lower())
                ids.append(profile.id)
            except openreview.OpenReviewException as e:
                if 'Profile not found' in e.args[0][0]:
                    emails.append(member.lower())
                else:
                    raise e
        else:
            ids.append(member)

    group.members = ids + emails
    return client.post_group(group)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('group_id', help='group ID whose members should be written to the name file')
    parser.add_argument('--baseurl', help="base url")
    parser.add_argument('--username')
    parser.add_argument('--password')
    args = parser.parse_args()

    client = openreview.Client(baseurl=args.baseurl, username=args.username, password=args.password)

    target_group = client.get_group(args.group_id)
    posted_group = replace_members_with_ids(client, target_group)

    print(posted_group)

