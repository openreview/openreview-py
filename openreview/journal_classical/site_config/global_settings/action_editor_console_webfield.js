/*
 * Thin source entrypoint for the Action Editor console webfield.
 *
 * The generated OpenReview webfield is assembled by scripts/build/site_config.py
 * from action_editor_console_webfield_parts/*.js so the source can be split by
 * console functionality while generated behavior remains equivalent.
 */

if (typeof module === 'object' && module.exports) {
  module.exports = require('./action_editor_console_webfield_parts/99_render.js')
}
