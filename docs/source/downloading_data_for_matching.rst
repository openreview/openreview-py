Downloading data from OpenReview to run matching locally from CLI
======================================================================

To be able to run matching locally, you would require the package openreview-matcher (https://github.com/openreview/openreview-matcher) installed on your local development environment.


Understanding CLI inputs for OpenReview matcher
--------------------------------------------------

To run matcher locally through CLI, use the following command:

    >>> python -m matcher \
	>>> --scores affinity_scores.csv \
    >>> --constraints conflicts.csv \
    >>> --max_papers max_papers.csv \
	>>> --weights 1 \
	>>> --min_papers_default 1 \
	>>> --max_papers_default 10 \
	>>> --num_reviewers 3 \
	>>> --num_alternates 3

To learn about the arguments, run the module with the --help flag like so:

    >>> python -m matcher --help

The matcher accepts files for these arguments:
1. scores - expected format: each line having comma-separated paperID, userID, score in this order)
2. constraints - expected format: each line having comma-separated paperID, reviewerID, constraint_value in this order where the constraint_value must be -1 (conflict), 1 (forced assignment), or 0 (no effect))
3. max_papers - expected format: each line having comma-separated paperID, max_paper in this order

Following are instructions on how you can download this data from OpenReview.

Scores
---------

Multiple type of affinity scores can be input using a file for each type of score. Some common score types are OpenReview affinity scores, TPMS scores, bid scores, AC recommendations, subject area overlap scores, etc.

The matcher then aggregates all scores into a single aggregated score by linearly combining the scores after multiplying each with the corresponding weight you provide using the `weights` argument which expects a comma separated list of floating point values.

OpenReview stores scores as edge objects. So, given that you have the necessary permissions to read these edges, you should be able to download these edges and write them into csv files.

For instance, to download ELMo score edges for ICLR 2020 Conference you can do the following:

    >>> import openreview
    >>> import csv
    >>> client = openreview.Client(baseurl = 'https://openreview.net', username=<>, password=<>)
    >>> score_groups = client.get_grouped_edges(invitation='ICLR.cc/2020/Conference/Reviewers/-/ELMo_Score', groupby='head', select='head,tail,weight')
    >>> with open('ELMo_scores.csv', 'w') as f:
    >>>     csv_writer = csv.writer(f)
    >>>     for edge_group in score_group:
    >>>         for edge in edge_group:
    >>>             csv_writer.writerow([edge['head], edge['tail], edge['weight]])


Constraints
--------------

