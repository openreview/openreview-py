var getTaskSortOrder = function(task) {
  var rawTaskName = task.id.split('/-/').pop().replace(/_/g, ' ');
  if (task.id.includes('/Reviewers/-/Assignment')) return 10;
  if (rawTaskName === REVIEW_NAME) return 20;
  if (rawTaskName === 'Rating') return 40;
  if (rawTaskName === DECISION_NAME) return 50;
  if (rawTaskName === CAMERA_READY_VERIFICATION_NAME) return 55;
  return 60;
};

var renderPendingTasks = function(container, tasks) {
  $(container).empty();
  if (!tasks.length) {
    $(container).append('<p>No pending tasks for this venue</p>');
    return;
  }

  var sortedTasks = tasks.slice().sort(function(a, b) {
    if (a.submissionNumber === b.submissionNumber) {
      return getTaskSortOrder(a) - getTaskSortOrder(b);
    }
    return (a.duedate || a.cdate || 0) - (b.duedate || b.cdate || 0);
  });
  var list = $('<ul class="list-unstyled"></ul>');
  sortedTasks.forEach(function(task) {
    var item = $('<li></li>');
    var link = $('<a></a>').attr('href', task.url).text(getTaskLabel(task));
    var primaryLine = $('<div class="ae-pending-task-primary"></div>');
    primaryLine.append(link);
    primaryLine.append($('<span></span>').text(getTaskDueDate(task)));
    item.append(primaryLine);
    var actionLine = $('<div class="ae-pending-task-actions" style="margin-top: 4px;"></div>');
    (task.actions || []).forEach(function(action) {
      actionLine.append(
        $('<a class="btn btn-xs btn-default"></a>')
          .attr('href', action.url)
          .text(action.name)
      );
    });
    if ((task.actions || []).length) {
      item.append(actionLine);
    }
    list.append(item);
  });
  $(container).append(list);
};

// Main function is the entry point to the webfield code
