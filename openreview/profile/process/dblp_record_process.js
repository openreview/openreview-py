async function process(client, edit, invitation) {
  client.throwErrors = true;

  const note = Tools.convertDblpXmlToNote(edit.content?.xml?.value);

  note.id = edit.note.id;
  const authorids = edit.note.content.authorids?.value;
  if (authorids) {
    note.content.authorids.value = note.content.authorids.value.map((authorid, index) => authorids[index] || authorid);
  }

  const html = note.content.html?.value;
  let abstractError = false;

  try {
    if (html) {
      const { abstract, pdf, error } = await Tools.extractAbstract(html);
      console.log('abstract: ' + abstract);
      console.log('pdf: ' + pdf);
      console.log('error: ' + error);
      if (abstract) {
        note.content.abstract = { value: abstract };
      }
      if (pdf) {
        note.content.pdf = { value: pdf };
      }
    } else {
      console.log('html field is empty');
    }
  } catch (error) {
    console.log('error: ' + JSON.stringify(error.toJson()));
    abstractError = error;
  }

  await client.postNoteEdit({
    invitation: 'DBLP.org/-/Edit',
    signatures: ['DBLP.org/Uploader'],
    readers: ['everyone'],
    writers: ['DBLP.org'],
    note: note
  });

  if (abstractError) {
    throw abstractError;
  }
}