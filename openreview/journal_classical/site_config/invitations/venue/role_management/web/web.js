// JMLR delta: Journal has no compact venue-role navigation page.
(function () {
  var root = '#invitation-container';
  var links = [
    ['Manage Action Editors', '/invitation?id=JMLR%2F-%2FManage_Action_Editors'],
    ['Manage Tracks', '/invitation?id=JMLR%2F-%2FManage_Tracks'],
    ['Manage AE Availability', '/group?id=JMLR%2FAction_Editors'],
    ['Edit Editors-in-Chief', '/group/edit?id=JMLR%2FEditors_In_Chief'],
    ['Edit Reviewers', '/group/edit?id=JMLR%2FReviewers'],
    ['Edit Production Editors', '/group/edit?id=JMLR%2FProduction_Editors'],
    ['Recruit Action Editors or Reviewers', '/forum?id={{PROD_JOURNAL_ID}}']
  ];
  $(root).html('<h2>JMLR Role Management</h2><p>Recruitment is owned by the Journal Request forum. Availability remains Journal’s standard private control.</p><ul>' +
    links.map(function (item) { return '<li><a href="' + item[1] + '">' + item[0] + '</a></li>'; }).join('') +
    '</ul><h3>Venue membership lookup</h3><p>Shows venue-level JMLR groups only; paper groups are omitted.</p>' +
    '<div class="form-inline"><input id="jmlr-member-id" class="form-control" placeholder="~Profile_ID"><button id="jmlr-member-search" class="btn btn-default">Search</button></div><div id="jmlr-member-result"></div>');
  $('#jmlr-member-search').on('click', function () {
    var id = String($('#jmlr-member-id').val() || '').trim();
    if (!/^~[A-Za-z0-9_.-]+$/.test(id)) {
      $('#jmlr-member-result').text('Enter a valid OpenReview profile ID.');
      return;
    }
    $('#jmlr-member-result').text('Loading...');
    var request = Webfield2.api.get('/groups', {member: id, prefix: 'JMLR'});
    request.then(function (result) {
      var groups = (result.groups || []).map(function (group) { return group.id; })
        .filter(function (groupId) { return groupId.indexOf('/Paper') < 0; }).sort();
      $('#jmlr-member-result').html(groups.length ? '<ul>' + groups.map(function (groupId) {
        return '<li><a href="/group?id=' + encodeURIComponent(groupId) + '">' + $('<div>').text(groupId).html() + '</a></li>';
      }).join('') + '</ul>' : '<p>No venue-level JMLR memberships found.</p>');
    });
    request.fail(function (error) {
      var detail = error && error.responseJSON || request.responseJSON || error || {};
      var status = error && error.status || request.status || detail.status;
      var message = String(detail.message || error && error.message || '');
      if (status === 404 || detail.name === 'NotFoundError' || /not found/i.test(message)) {
        $('#jmlr-member-result').html('<p>No venue-level JMLR memberships found.</p>');
      } else {
        $('#jmlr-member-result').text(message || 'Profile not found or membership lookup failed. Retry Search.');
      }
    });
  });
}());
