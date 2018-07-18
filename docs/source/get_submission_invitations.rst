Getting all the submission invitations
========================================

All the Invitation Ids can be retrieved like this::

    >>> import openreview
    >>> c = openreview.Client(baseurl='https://dev.openreview.net')
    >>> invitations = openreview.get_submission_invitations(c)
    >>> invitations
    [u'ICLR.cc/2018/Conference/-/Blind_Submission', u'auai.org/UAI/2018/-/Blind_Submission', u'auai.org/UAI/2018/-/Submission', u'naacl.org/NAACL/2018/Preprint/-/Blind_Submission', u'naacl.org/NAACL/2018/Preprint/-/Submission']

Using these Invitation Ids we can extract the relevant notes like this::

    >>> notes = c.get_notes(invitation='ICLR.cc/2018/Conference/-/Blind_Submission')
    >>> notes[0].signatures
    [u'ICLR.cc/2018/Conference']
    >>> notes[0].content['authorids']
    [u'ICLR.cc/2018/Conference/Paper291/Authors']
    