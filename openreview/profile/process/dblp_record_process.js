async function process(client, edit, invitation) {
  client.throwErrors = true;

  const note = Tools.convertDblpXmlToNote(edit.content?.xml?.value);

  note.id = edit.note.id;
  const authorids = edit.note.content.authorids?.value;
  if (authorids) {
    note.content.authorids.value = note.content.authorids.value.map((authorid, index) => authorids[index] || authorid);
  }

  const html = note.content.html?.value;
  const extractAbstractFnUrl = null;

  try {
    if (html && extractAbstractFnUrl) {
      const { abstract, pdf, error } = await fetch(`${extractAbstractFnUrl}?url=${html}`.then(response => response.json()));
      console.log('abstract: ' + abstract);
      console.log('pdf: ' + pdf);
      console.log('error: ' + error);
      if (abstract) {
        note.content.abstract = { value: abstract };
      }
      if (pdf) {
        note.content.pdf = { value: pdf };
      }
    }
  } catch (error) {
    console.log('error: ' + error);
  }



  await client.postNoteEdit({
    invitation: 'DBLP.org/-/Edit',
    signatures: ['DBLP.org/Uploader'],
    readers: ['everyone'],
    writers: ['DBLP.org'],
    note: note
  });
}