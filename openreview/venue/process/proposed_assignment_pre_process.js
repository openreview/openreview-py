async function process(client, edge, invitation) {
  client.throwErrors = true

  const committeeName = invitation.content.committee_name?.value;
  const { groups } = await client.getGroups({ id: invitation.domain });
  const domain = groups[0];

  const customMaxPapersId = domain.content[committeeName.toLowerCase() + '_custom_max_papers_id']?.value;

  if (edge.ddate) {
    return
  }

  if (edge.tcdate !== edge.tmdate) {
    return
  }

  if (!customMaxPapersId) {
    return
  }

  const [res1, res2] = await Promise.all([
    client.getEdges({ invitation: customMaxPapersId, tail: edge.tail }),
    client.getEdges({ invitation: edge.invitation, label: edge.label, tail: edge.tail })
  ])    
  let customMaxPapers = (res1.count > 0 && res1.edges[0].weight) || 0;
  const assignmentEdges = res2.edges;

  if (!customMaxPapers) {
    const { invitations } = await client.getInvitations({ id: customMaxPapersId });
    customMaxPapers = invitations[0].edge.weight.param.default;
  }

  if (assignmentEdges.length >= customMaxPapers) {
    const { profiles } = await client.getProfiles({ id: edge.tail });
    const profile = profiles[0];
    return Promise.reject(new OpenReviewError({ name: 'Error', message: 'Max Papers allowed reached for ' + client.tools.getPreferredName(profile) }));
  }

}
