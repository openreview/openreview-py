Getting Data
==============

The OpenReview API can be used to retrieve conference data (e.g. papers, comments, decisions, reviews, etc.) for research or other purposes.

Notes
-------------------------------------------

Most data in OpenReview are represented as `Notes`. All `Notes` respond to an `Invitation`, which specifies the possible content and permissions that the `Note` is required to contain.

Users can query for notes using the ID of the Invitation that it responds to.

Consider the following example which gets the public `Notes` that represent the 11th through 20th submissions to ICLR 2019::

	blind_submissions = client.get_notes(
		invitation='ICLR.cc/2019/Conference/-/Blind_Submission',
		limit=10,
		offset=10)

By default, `get_notes` will return up to the first 1000 corresponding `Notes` (`limit=1000`). To retrieve `Notes` beyond the first 1000, you can adjust the `offset` parameter, or use the function `tools.iterget_notes` which returns an iterator over all corresponding `Notes`::


	blind_submissions_iterator = openreview.tools.iterget_notes(
		client, invitation='ICLR.cc/2019/Conference/-/Blind_Submission')

It's also possible to query for `Notes` by `Invitation` ID using a regex pattern. Consider the following example that gets all `Public_Comments` for the ICLR 2019 conference::


	iclr19_public_comments = client.get_notes(
		invitation='ICLR.cc/2019/Conference/-/Paper.*/Public_Comment')

This code returns public comments made during the conference `ICLR.cc/2019/Conference` with invitation such as `ICLR.cc/2019/Conference/-/Paper1234/Public_Comment`.

Invitation IDs follow a loose convention that resembles the one in the example above: the ID of the conference (e.g. `ICLR.cc/2019/Conference`) and an identifying string (e.g. `Blind_Submission`), joined by a dash (`-`). It's important to note, however, that this convention is not strictly enforced, and individual conferences may choose to format their Invitation IDs differently.

Invitations can be queried with the `get_invitations` function to find the Invitation IDs for a particular conference. The following example retrieves the first 10 Invitations for the ICLR 2019 conference::


	iclr19_invitations = client.get_invitations(
		regex='ICLR.cc/2019/Conference/.*',
		limit=10,
		offset=0)

Like `get_notes`, `get_invitations` will return up to the first 1000 Invitations (`limit=1000`). To retrieve Invitations beyond the first 1000, you can adjust the `offset` parameter, or use the function `tools.iterget_invitations`::


	iclr19_invitations_iterator = openreview.tools.iterget_invitations(
		client, regex='ICLR.cc/2019/Conference/.*')


Retrieving all Official Reviews for a conference
-------------------------------------------------

Like comments and submissions, reviews are also usually represented as Notes. Conferences often distinguish reviews written by official conference reviewers with the invitation suffix `Official_Review`.

For example, the reviews in ICLR 2019 all have invitations with the following pattern::


	>>> ICLR.cc/2019/Conference/-/Paper.*/Official_Review

To retrieve the Official Reviews for a given ICLR 2019 paper, do the following::

	paper123_reviews = client.get_notes(
		invitation='ICLR.cc/2019/Conference/-/Paper123/Official_Review')

The specific structure of the review's ``content`` field is determined by the conference, but a typical review's content will include fields like ``title``, ``review``, ``rating``, and ``confidence``::


	review0 = paper123_reviews[0]
	print(review0.content['rating'])
	'8: Top 50% of accepted papers, clear accept'

Conferences as large as ICLR 2019 will often have a number of reviews that exceeds the default API limit. To retrieve all Official Reviews for all ICLR 2019 papers, create an iterator over reviews by doing the following::


	>>> review_iterator = openreview.tools.iterget_notes(client, invitation='ICLR.cc/2019/Conference/-/Paper.*/Official_Review')
	>>> for review in review_iterator:
	>>>     #do something

Retrieving all accepted Submissions for a conference (Single-blind)
-------------------------------------------------------------------
Since the Submissions do not contain the decisions, we first need to retrieve all the Decision notes, filter the accepted notes and use their forum ID to locate its corresponding Submission. We break down these steps below.

Retrieve Submissions and Decisions.


	id_to_submission = {
    	note.id: note for note in openreview.tools.iterget_notes(client, invitation = 'MIDL.io/2019/Conference/-/Full_Submission')
	}
	all_decision_notes = openreview.tools.iterget_notes(client, invitation = 'MIDL.io/2019/Conference/-/Paper.*/Decision')

It is convenient to place all the submissions in a dictionary with their id as the key so that we can retrieve an accepted submission using its id.

We then filter the Decision notes that were accepted and use their forum ID to get the corresponding Submission.


	accepted_submissions = [id_to_submission[note.forum] for note in all_decision_notes if note.content['decision'] == 'Accept']

Retrieving all accepted Submissions for a conference (Double-blind)
-------------------------------------------------------------------
This is very similar to the previous example. The only difference is that we need to get the blind notes with the added details parameter to get the Submission.

Retrieve Submissions and Decisions.

	>>> blind_notes = {note.id: note for note in openreview.tools.iterget_notes(client, invitation = 'auai.org/UAI/2019/Conference/-/Blind_Submission', details='original')}

	>>> all_decision_notes = openreview.tools.iterget_notes(client, invitation = 'auai.org/UAI/2019/Conference/-/Paper.*/Decision')

We then filter the Decision notes that were accepted and use their forum ID to get the corresponding Submission.

	>>> accepted_submissions = [blind_notes[decision_note.forum].details['original'] for decision_note in all_decision_notes if 'Accept' in decision_note.content['decision']]

Retrieving all the author names and e-mails from accepted Submissions
---------------------------------------------------------------------
First we need to retrieve the Accepted Submissions. Please refer to 'Retrieving all accepted Submissions for a conference'. Once we get the Accepted Submissions we can easily extract the author's information from them.

	>>> author_emails = []
	>>> author_names = []
	>>> for submission in accepted_submissions:
	... 	author_emails += submission['content']['authorids']
	... 	author_names += submission['content']['authors']

Retrieving comments made on a forum
----------------------------------------

All comments made on a particular forum/submission can be extracted like this::

	>>>iclr19_forum_comments = client.get_notes(forum="<forum-id>")

Also, the public comments on a particular forum can be extracted like this::

	>>>iclr19_forum_public_comments = client.get_notes(forum="<forum-id>", invitation="ICLR.cc/2019/Conference/-/Paper.*/Public_Comment")

Accessing data in comments
------------------------------

The data in a comment, or basically Notes objects, can be accessed like this::

	>>>print(iclr19_forum_public_comments[0].content["title"])
	>>>print(iclr19_forum_public_comments[0].content["comment"])


Getting ICLR 2019 data
--------------------------------

The following example script can be used to retrieve all ICLR 2019 metadata and PDFs::

	import argparse
	import json
	import os
	from collections import defaultdict
	from tqdm import tqdm
	import openreview


	def download_iclr19(client, outdir='./', get_pdfs=False):
	    '''
	    Main function for downloading ICLR metadata (and optionally, PDFs)
	    '''
	    # pylint: disable=too-many-locals

	    print('getting metadata...')
	    # get all ICLR '19 submissions, reviews, and meta reviews, and organize them by forum ID
	    # (a unique identifier for each paper; as in "discussion forum").
	    submissions = openreview.tools.iterget_notes(
	        client, invitation='ICLR.cc/2019/Conference/-/Blind_Submission')
	    submissions_by_forum = {n.forum: n for n in submissions}

	    # There should be 3 reviews per forum.
	    reviews = openreview.tools.iterget_notes(
	        client, invitation='ICLR.cc/2019/Conference/-/Paper.*/Official_Review')
	    reviews_by_forum = defaultdict(list)
	    for review in reviews:
	        reviews_by_forum[review.forum].append(review)

	    # Because of the way the Program Chairs chose to run ICLR '19, there are no "decision notes";
	    # instead, decisions are taken directly from Meta Reviews.
	    meta_reviews = openreview.tools.iterget_notes(
	        client, invitation='ICLR.cc/2019/Conference/-/Paper.*/Meta_Review')
	    meta_reviews_by_forum = {n.forum: n for n in meta_reviews}

	    # Build a list of metadata.
	    # For every paper (forum), get the review ratings, the decision, and the paper's content.
	    metadata = []
	    for forum in submissions_by_forum:

	        forum_reviews = reviews_by_forum[forum]
	        review_ratings = [n.content['rating'] for n in forum_reviews]

	        forum_meta_review = meta_reviews_by_forum[forum]
	        decision = forum_meta_review.content['recommendation']

	        submission_content = submissions_by_forum[forum].content

	        forum_metadata = {
	            'forum': forum,
	            'review_ratings': review_ratings,
	            'decision': decision,
	            'submission_content': submission_content
	        }
	        metadata.append(forum_metadata)

	    print('writing metadata to file...')
	    # write the metadata, one JSON per line:
	    with open(os.path.join(outdir, 'iclr19_metadata.jsonl'), 'w') as file_handle:
	        for forum_metadata in metadata:
	            file_handle.write(json.dumps(forum_metadata) + '\n')

	    # if requested, download pdfs to a subdirectory.
	    if get_pdfs:
	        pdf_outdir = os.path.join(outdir, 'iclr19_pdfs')
	        os.makedirs(pdf_outdir)
	        for forum_metadata in tqdm(metadata, desc='getting pdfs'):
	            pdf_binary = client.get_pdf(forum_metadata['forum'])
	            pdf_outfile = os.path.join(pdf_outdir, '{}.pdf'.format(forum_metadata['forum']))
	            with open(pdf_outfile, 'wb') as file_handle:
	                file_handle.write(pdf_binary)


	if __name__ == '__main__':
	    parser = argparse.ArgumentParser()
	    parser.add_argument(
	        '-o', '--outdir', default='./', help='directory where data should be saved')
	    parser.add_argument(
	        '--get_pdfs', default=False, action='store_true', help='if included, download pdfs')
	    parser.add_argument('--baseurl', default='https://openreview.net')
	    parser.add_argument('--username', default='', help='defaults to empty string (guest user)')
	    parser.add_argument('--password', default='', help='defaults to empty string (guest user)')

	    args = parser.parse_args()

	    outdir = args.outdir

	    client = openreview.Client(
	        baseurl=args.baseurl,
	        username=args.username,
	        password=args.password)

	    download_iclr19(client, outdir, get_pdfs=args.get_pdfs)


You can also call this script with the `openreview` package::

	>>> python -m openreview.scripts.download_iclr19 --get_pdfs

