async function process(client, edit, invitation) {
  client.throwErrors = true;

  const json = edit.content?.json?.value;
  const note = Tools.convertORCIDJsonToNote(json);

  note.id = edit.note.id;

  // TODO: Remove this block once @openreview/client is published with the
  // formatCreditName fix (converts "Last, First" to "First Last") and replace
  // with the commented-out code below.
  //
  // --- Start: replace with this once @openreview/client is updated ---
  // const convertedAuthors = note.content.authors?.value || [];
  // if (convertedAuthors.length > 0 && typeof convertedAuthors[0] === 'string') {
  //   const authorids = note.content.authorids?.value || [];
  //   note.content.authors = {
  //     value: convertedAuthors.map((name, i) => ({ fullname: name, username: authorids[i] || '' }))
  //   };
  //   delete note.content.authorids;
  // }
  // --- End ---

  // --- Start: remove once @openreview/client is updated ---
  // Build authors directly from the ORCID JSON to ensure correct "First Last"
  // name ordering regardless of what the convert function returns.
  const formatCreditName = (name) => {
    if (!name) return '';
    const commaIndex = name.indexOf(',');
    if (commaIndex === -1) return name.trim();
    const last = name.substring(0, commaIndex).trim();
    const first = name.substring(commaIndex + 1).trim();
    return first ? `${first} ${last}` : last;
  };

  const contributors = json?.contributors?.contributor || [];
  note.content.authors = {
    value: contributors.map((p) => {
      const fullname = formatCreditName(p['credit-name']?.value);
      let username = '';
      if (p['contributor-orcid']?.uri) {
        username = p['contributor-orcid'].uri;
      } else if (fullname) {
        username = `https://orcid.org/orcid-search/search?searchQuery=${fullname}`;
      }
      return { fullname, username };
    })
  };
  delete note.content.authorids;
  // --- End: remove once @openreview/client is updated ---

  const { notes } = await client.getNotes({ id: edit.note.id });
  const existingAuthors = notes[0].content.authors?.value;

  if (existingAuthors) {
    note.content.authors.value = note.content.authors.value.map((author, index) => {
      const existing = existingAuthors[index];
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
    signatures: [`${edit.domain}/ORCID.org/Uploader`],
    readers: ['everyone'],
    writers: [`${edit.domain}/ORCID.org`],
    note: note
  });

}