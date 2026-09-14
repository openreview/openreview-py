Journal Editors-in-Chief Console
================================

The Journal Editors-in-Chief console uses the venue's meta invitation to load
invitation definitions through the supported invitations API. The browser
client retrieves every result page, preserves creation-date ordering, includes
expired definitions, and then filters complete venue, reviewer, action-editor,
and numbered-paper ID boundaries locally.

A valid response with no matching invitations produces the ordinary empty
console state. If the invitation request fails because of a network or
permission error, console loading fails visibly through the standard retryable
webfield error instead of reporting an empty task list.

The console continues to link to the native assignment browser, proposed
Action Editor assignments page, recruitment forum, role groups, and paper
tasks. Loading the console does not write assignments, memberships, or papers.
