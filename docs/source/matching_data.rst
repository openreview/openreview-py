OpenReview Matcher
=========================================================================

OpenReview Matcher is a tool for computing optimal paper-reviewer matches for peer review, subject to constraints and affinity scores. This tool comes with a simple web server designed for integration with the OpenReview server application. The tool also allows you to execute these matches locally on your setup. For more details about the tool itself refer to https://github.com/openreview/openreview-matcher.

To be able to run matching locally, you would require the package openreview-matcher installed on your local development environment.
Next, if the data needed to run the matcher locally is available in OpenReview, you can use the OpenReview-py API to download this data.

Understanding CLI inputs for OpenReview matcher
--------------------------------------------------

To run matcher locally through CLI, use the following command:

    >>> python -m matcher \
	...     --scores affinity_scores.csv \
        ...     --constraints conflicts.csv \
        ...     --max_papers max_papers.csv \
	...     --weights 1 \
	...     --min_papers_default 1 \
	...     --max_papers_default 10 \
	...     --num_reviewers 3 \
	...     --num_alternates 3

To learn about the arguments, run the module with the --help flag like so:

    >>> python -m matcher --help

The matcher accepts files for these arguments:

1. scores - expected format: each line having comma-separated paperID, userID, score in this order)
2. constraints - expected format: each line having comma-separated paperID, reviewerID, constraint_value in this order where the constraint_value must be -1 (conflict), 1 (forced assignment), or 0 (no effect))
3. max_papers - expected format: each line having comma-separated userID, max_paper in this order


Following are instructions on how you can download this data from OpenReview.

Downloading Scores
---------------------

Multiple type of affinity scores can be input using a file for each type of score. Some common score types are OpenReview affinity scores, TPMS scores, bid scores, AC recommendations, subject area overlap scores, etc.

The matcher then aggregates all scores into a single aggregated score by linearly combining the scores after multiplying each with the corresponding weight you provide using the `weights` argument which expects a comma separated list of floating point values.

OpenReview stores scores as edge objects. So, given that you have the necessary permissions to read these edges, you should be able to download these edges and write them into csv files.

For instance, to download ELMo score edges for ICLR 2020 Conference you can do the following:

    >>> import openreview
    >>> import csv
    >>> client = openreview.Client(baseurl = 'https://openreview.net', username=<>, password=<>)
    >>> all_ELMo_edges = openreview.tools.iterget_edges(client, invitation='ICLR.cc/2020/Conference/Reviewers/-/ELMo_Score')
    >>> with open('ELMo_scores.csv', 'w') as f:
    ...     csv_writer = csv.writer(f)
    ...     for edge in all_ELMo_edges:
    ...         csv_writer.writerow([edge.head, edge.tail, edge.weight])

Please note that this is usually a time consuming task as there could be millions of edges for a single type of score (in the order of (# of papers) * (# of reviewers)).


Downloading Constraints
-------------------------

You can use this option to input constraint scores using a file for each type of constraint. This is the option used to input conflicts.

OpenReview stores constraints as edge objects. So, given that you have the necessary permissions to read these edges, you should be able to download these edges and write them into csv files.

To download conflict edges for ICLR 2020 Conference you can do the following:

    >>> import openreview
    >>> import csv
    >>> client = openreview.Client(baseurl = 'https://openreview.net', username=<>, password=<>)
    >>> all_conflict_edges = openreview.tools.iterget_edges(client, invitation='ICLR.cc/2020/Conference/Reviewers/-/Conflict')
    >>> with open('conflict_scores.csv', 'w') as f:
    ...     csv_writer = csv.writer(f)
    ...     for edge_group in all_conflict_edges:
    ...         csv_writer.writerow([edge.head, edge.tail, edge.weight])


Downloading Custom max papers
--------------------------------

The option --max_papers can be used to optionally provide a file containing max number of papers to be assigned to each user(reviewer or Area Chair).

If this data is available in OpenReview, it would be as edge objects with an invitation like "ICLR.cc/2020/Conference/Reviewers/-/Custom_Max_Papers".

    >>> import openreview
    >>> import csv
    >>> client = openreview.Client(baseurl = 'https://openreview.net', username=<>, password=<>)
    >>> all_max_paper_edges = openreview.tools.iterget_edges(client, invitation='ICLR.cc/2020/Conference/Reviewers/-/Custom_Max_Papers')
    >>> with open('max_papers.csv', 'w') as f:
    ...     csv_writer = csv.writer(f)
    ...     for edge_group in all_max_paper_edges:
    ...         csv_writer.writerow([edge.tail, edge.weight])
