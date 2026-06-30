/*
 * Thin source entrypoint for the JMLR venue landing/router webfield.
 *
 * The generated OpenReview webfield is assembled by scripts/build/site_config.py
 * from jmlr_meta_parts/*.js so source responsibilities remain separated while
 * generated behavior remains equivalent.
 */

if (typeof module === 'object' && module.exports) {
  module.exports = require('./jmlr_meta_parts/90_render.js')
}
