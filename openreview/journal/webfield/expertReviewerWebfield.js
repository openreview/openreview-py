// Webfield component
return {
    component: 'GroupDirectory',
    properties: {
      title: `${domain.id} Expert Reviewers`,
      description: `*${domain.id} is proud to highlight the following Expert Reviewers, i.e. reviewers for ${domain.id} who have done exemplary work in evaluating ${domain.id} submissions. They have stood out in various ways, including by writing detailed reviews, engaging deeply with authors and performing their work in a timely fashion.
  To highlight their contribution and expertise, the accepted ${domain.id} papers they author are also given an Expert Certification.*`,
      links: entity.members
    }
  }