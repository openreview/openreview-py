Classes:

Client(username=None, password=None, baseurl=None)



Examples:

initialize the client and get a group
```
>>> from openreview import *
>>> client = Client()
>>> iclr_group = client.get_group('ICLR.cc/2017/pcs')
```

get all notes submitted via a given invitation
```
>>> notes = client.get_notes(invitation='ICLR.cc/2017/conference/-/submission')
>>> first_note = notes[0]
>>> second_note = notes[1]
```
