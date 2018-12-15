import openreview
import argparse
from .tools import replace_members_with_ids

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

