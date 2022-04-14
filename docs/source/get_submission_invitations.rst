Getting Submissions
========================================

All the Invitation Ids for Submissions can be retrieved like this::

    >>> import openreview
    >>> c = openreview.Client(baseurl='https://api.openreview.net')
    >>> invitations = openreview.tools.get_submission_invitations(c)
    >>> print(*invitations, sep="\n")
    machineintelligence.cc/MIC/2018/Conference/-/Submission
    machineintelligence.cc/MIC/2018/Abstract/-/Submission
    ICLR.cc/2018/Workshop/-/Withdraw_Submission
    ICLR.cc/2018/Workshop/-/Withdrawn_Submission
    aclweb.org/NAACL/2018/Preprint/-/Blind_Submission
    aclweb.org/NAACL/2018/Preprint/-/Submission
    ICLR.cc/2018/Conference/-/Withdrawn_Submission
    ICLR.cc/2013/conference/-/submission
    ICLR.cc/2014/-/submission/workshop
    ICLR.cc/2014/-/submission/conference
    ICLR.cc/2014/-/submission
    ICML.cc/2013/PeerReview/-/submission
    ICML.cc/2013/Inferning/-/submission
    ICLR.cc/2013/-/submission
    AKBC.ws/2013/-/submission
    ICLR.cc/2016/workshop/-/submission
    ICML.cc/2018/Workshop/NAMPI/-/Submission
    NIPS.cc/2017/Workshop/Autodiff/-/Submission
    ICLR.cc/2018/Conference/-/Blind_Submission
    roboticsfoundation.org/RSS/2017/RCW_Workshop/-_Proceedings/-/Submission
    ICML.cc/2018/Workshop/NAMPI/-/Blind_Submission
    ISMIR.net/2018/WoRMS/-/Submission
    ICLR.cc/2018/Conference/-/Submission
    auai.org/UAI/2018/-/Blind_Submission
    swsa.semanticweb.org/ISWC/2017/DeSemWeb/-/Submission
    auai.org/UAI/2017/-/submission
    auai.org/UAI/2018/-/Submission
    auai.org/UAI/2017/-/blind-submission
    NIPS.cc/2016/workshop/NAMPI/-/submission
    NIPS.cc/2017/Workshop/MLITS/-/Submission
    swsa.semanticweb.org/ISWC/2018/DeSemWeb/-/Submission
    IEEE.org/2018/ITSC/-/Blind_Submission
    MIDL.amsterdam/2018/Abstract/-/Submission
    ICML.cc/2017/RML/-/Submission
    ICLR.cc/2018/Workshop/-/Submission
    OpenReview.net/Anonymous_Preprint/-/Submission
    ICLR.cc/2017/workshop/-/submission
    ECCV2016.org/BNMW/-/submission
    IEEE.org/2018/ITSC/-/Submission
    OpenReview.net/Anonymous_Preprint/-/Blind_Submission
    ICML.cc/2018/RML/-/Submission
    roboticsfoundation.org/RSS/2017/RCW_Workshop/-_Poster/-/Submission
    NIPS.cc/2016/workshop/MLITS/-/submission
    ICLR.cc/2014/conference/-/submission
    ICLR.cc/2017/conference/-/submission
    ICML.cc/2017/MLAV/-/Submission
    ICML.cc/2017/WHI/-/Submission
    ICLR.cc/2014/workshop/-/submission
    cv-foundation.org/CVPR/2017/BNMW/-/Submission
    MIDL.amsterdam/2018/Conference/-/Submission
    ICML.cc/2018/ECA/-/Submission

Using these Invitation Ids we can extract the relevant notes like this::

    >>> notes = c.get_notes(invitation='ICLR.cc/2018/Conference/-/Blind_Submission')
    >>> print(notes[0])
    {'cdate': 1518730187619,
     'content': {u'TL;DR': u'Neural phrase-based machine translation with linear decoding time',
                 u'_bibtex': u'@inproceedings{\nhuang2018towards,\ntitle={Towards Neural Phrase-based Machine Translation},\nauthor={Po-Sen Huang and Chong Wang and Sitao Huang and Dengyong Zhou and Li Deng},\nbooktitle={International Conference on Learning Representations},\nyear={2018},\nurl={https://openreview.net/forum?id=HktJec1RZ},\n}',
                 u'abstract': u'In this paper, we present Neural Phrase-based Machine Translation (NPMT). Our method explicitly models the phrase structures in output sequences using Sleep-WAke Networks (SWAN), a recently proposed segmentation-based sequence modeling method. To mitigate the monotonic alignment requirement of SWAN, we introduce a new layer to perform (soft) local reordering of input sequences. Different from existing neural machine translation (NMT) approaches, NPMT does not use attention-based decoding mechanisms.  Instead, it directly outputs phrases in a sequential order and can decode in linear time. Our experiments show that NPMT achieves superior performances on IWSLT 2014 German-English/English-German and IWSLT 2015 English-Vietnamese machine translation tasks compared with strong NMT baselines. We also observe that our method produces meaningful phrases in output languages.',
                 u'authorids': [u'huang.person@gmail.com',
                                u'chongw@google.com',
                                u'shuang91@illinois.edu',
                                u'dennyzhou@gmail.com',
                                u'l.deng@ieee.org'],
                 u'authors': [u'Po-Sen Huang',
                              u'Chong Wang',
                              u'Sitao Huang',
                              u'Dengyong Zhou',
                              u'Li Deng'],
                 u'keywords': [u'Neural Machine Translation',
                               u'Sequence to Sequence',
                               u'Sequence Modeling'],
                 u'paperhash': u'huang|towards_neural_phrasebased_machine_translation',
                 u'pdf': u'/pdf/b907f63a962c897b8193743aec2e9ac67eb5f79a.pdf',
                 u'title': u'Towards Neural Phrase-based Machine Translation'},
     'ddate': None,
     'forum': u'HktJec1RZ',
     'forumContent': None,
     'id': u'HktJec1RZ',
     'invitation': u'ICLR.cc/2018/Conference/-/Blind_Submission',
     'nonreaders': [],
     'number': 143,
     'original': None,
     'overwriting': None,
     'readers': [u'everyone'],
     'referent': None,
     'replyto': None,
     'signatures': [u'ICLR.cc/2018/Conference'],
     'tcdate': 1509036001039,
     'tmdate': 1531951157137,
     'writers': [u'ICLR.cc/2018/Conference']}
