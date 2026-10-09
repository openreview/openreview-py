async function process(client, edit, invitation) {
  client.throwErrors = true;

  const note = Tools.convertACLJsonToNote(edit.content?.json?.value);

  note.id = edit.note.id;

  // The poster links themselves to their own profile; keep those links and let the
  // Anthology page links stand for everybody else.
  const existingAuthors = edit.note.content.authors?.value;
  if (existingAuthors) {
    note.content.authors.value = note.content.authors.value.map((author, index) => {
      const existing = existingAuthors[index];
      if (existing?.username?.startsWith('~')) {
        // A profile id is only valid next to a name that profile answers to, and the
        // Anthology does not always spell a name the way its owner's profile does.
        return { fullname: existing.fullname, username: existing.username };
      }
      if (existing?.username) {
        return { ...author, username: existing.username };
      }
      return author;
    });
  }

  note.content.venueid = {
    value: edit.domain
  }

  await client.postNoteEdit({
    invitation: `${edit.domain}/-/Edit`,
    signatures: [`${edit.domain}/ACL_Anthology.org/Uploader`],
    readers: ['everyone'],
    writers: [`${edit.domain}/ACL_Anthology.org`],
    note: note
  });

}
