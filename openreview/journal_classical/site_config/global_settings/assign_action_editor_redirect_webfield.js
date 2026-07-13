var main = function() {
  var target = typeof ASSIGN_AE_ASSIGNMENT_PAGE_URL !== 'undefined' ? ASSIGN_AE_ASSIGNMENT_PAGE_URL : '';
  if (!target) {
    Webfield2.ui.setup('#invitation-container', 'JMLR', {
      title: 'Assign Action Editor',
      instructions: '<p class="text-danger">The Action Editor assignment page is unavailable for this launcher.</p>',
      fullWidth: true
    });
    Webfield2.ui.done();
    return;
  }
  if (globalThis.top) globalThis.top.location.replace(target);
  else globalThis.location.replace(target);
};

main();
