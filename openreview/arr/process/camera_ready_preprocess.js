async function process(client, edit, invitation) {
  client.throwErrors = true;
  const { invitations } = await client.getInvitations({ id: invitation.invitations[0] });
  const metaInvitation = invitations[0];
  const script = metaInvitation.content.revision_preprocess_script.value;
  eval(`var process = ${script}`);
  await process(client, edit, invitation);
}
