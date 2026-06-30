/*
 * Thin source entrypoint for JMLR permission helpers.
 *
 * The browser bundle is assembled by scripts/build/site_config.py from
 * permission_helpers_parts/*.js so functionality can be split into small files
 * while generated OpenReview output remains equivalent.
 */

;(function(root, factory) {
  if (typeof module === 'object' && module.exports) {
    module.exports = factory()
  } else {
    root.JMLRPermissionHelpers = factory()
  }
})(typeof self !== 'undefined' ? self : this, function() {
  if (typeof require === 'function') {
    return require('./permission_helpers_parts/core.js')
  }
  if (typeof JMLRPermissionHelpersBundled !== 'undefined') {
    return JMLRPermissionHelpersBundled
  }
  throw new Error('JMLR permission helper bundle is not available')
})
