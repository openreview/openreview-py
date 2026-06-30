var JMLR_RATING_LAUNCHER_ITEMS_HTML = __JMLR_RATING_LAUNCHER_ITEMS_HTML_JSON__;
var JMLR_RATING_LAUNCHER_FORUM_URL = __JMLR_RATING_LAUNCHER_FORUM_URL_JSON__;
var JMLR_RATING_LAUNCHER_PAPER_LABEL = __JMLR_RATING_LAUNCHER_PAPER_LABEL_JSON__;

return [
  '<style>',
    '.jmlr-reviewer-rating-launcher .reviewer-rating-item{border:1px solid #ddd;border-radius:4px;padding:12px;margin:12px 0;background:#fff;}',
    '.jmlr-reviewer-rating-launcher .reviewer-rating-review{max-height:320px;overflow:auto;white-space:pre-wrap;background:#f8f8f8;border:1px solid #e5e5e5;border-radius:4px;padding:10px;margin:8px 0;}',
    '.jmlr-reviewer-rating-launcher .reviewer-rating-actions{margin-top:8px;}',
  '</style>',
  '<div class="jmlr-reviewer-rating-launcher">',
    '<h4>Rate reviewers for ' + JMLR_RATING_LAUNCHER_PAPER_LABEL + '</h4>',
    '<p>The decision has been submitted. Review each submitted review below, then open the rating form for that reviewer.</p>',
    '<div>',
      JMLR_RATING_LAUNCHER_ITEMS_HTML,
    '</div>',
    '<p class="small text-muted" style="margin-top: 12px;">',
      'Ratings are visible only to Editors-in-Chief and the paper Action Editors. ',
      '<a href="' + JMLR_RATING_LAUNCHER_FORUM_URL + '">Return to the paper forum</a>.',
    '</p>',
  '</div>'
].join('');
