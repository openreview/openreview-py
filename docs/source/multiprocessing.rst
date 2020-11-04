Parallel Execution
==================

The tools package includes utilities that makes it easy to run a set of requests in parallel using a multiprocessing pool:

    >>> notes = list(tools.iterget_notes(client, invitation='ICLR.cc/2019/Conference/-/Blind_Submission'))
    >>> openreview.tools.parallel_exec(notes, do_work)

The function do_work must be defined as a pickled function, for more info see: https://docs.python.org/3/library/pickle.html#what-can-be-pickled-and-unpickled
