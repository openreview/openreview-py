/*
 * Thin source entrypoint for the Production Editor console webfield.
 *
 * The generated OpenReview webfield is assembled by scripts/build/site_config.py
 * from production_editor_console_webfield_parts/*.js so the source can be split
 * by console functionality while generated behavior remains equivalent.
 */

if (typeof module === 'object' && module.exports) {
  module.exports = require('./production_editor_console_webfield_parts/core.js')
}
