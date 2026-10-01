'use strict'

const fs = require('fs')
const vm = require('vm')

const handlers = {}
const elements = {}
function element (selector) {
  if (!elements[selector]) {
    elements[selector] = {
      value: '', checked: false,
      html: function () { return this }, text: function () { return this },
      val: function (value) { if (value === undefined) return this.value; this.value = value; return this },
      prop: function (name, value) { if (value === undefined) return name === 'checked' ? this.checked : false; this[name] = value; return this },
      on: function (event, child, callback) { handlers[selector + ':' + event + ':' + (callback ? child : '')] = callback || child; return this },
      find: function (child) { return element(selector + ' ' + child) },
      closest: function () { return this }, attr: function () { return undefined }
    }
  }
  return elements[selector]
}
function $ (selector) {
  if (typeof selector === 'string' && selector === '<div>') return { text: function () { return this }, html: function () { return '' } }
  if (typeof selector !== 'string') return selector
  return element(selector)
}
$.extend = function (_target, ...sources) { return Object.assign({}, ...sources) }

let managed = [
  { id: 'first', tail: '~AE1', label: 'OSS' },
  { id: 'second', tail: '~AE1', label: 'OSS' }
]
const retired = []
const api = {
  get: function (path, query) {
    if (path === '/groups' && query.id.endsWith('/Action_Editors')) return Promise.resolve({ groups: [{ members: ['~AE1'] }] })
    if (path === '/groups') return Promise.resolve({ groups: [{ content: { tracks: { value: [{ id: 'Regular', name: 'Regular', open: true }, { id: 'OSS', name: 'OSS', open: true }] } } }] })
    if (path === '/profiles') return Promise.resolve({ profiles: [{ content: { names: [{ fullname: 'AE One' }] } }] })
    return Promise.resolve({})
  },
  getAll: function (_path, query) { return Promise.resolve(query.invitation.endsWith('Track_Eligible') ? managed : []) },
  post: function (_path, body) {
    if (body.ddate) { retired.push(body.id); managed = managed.filter(edge => edge.id !== body.id) }
    return Promise.resolve({})
  }
}

const context = { $, console, Webfield2: { api, ui: { done: function () {} } }, Promise, setTimeout, clearTimeout }
vm.runInNewContext(fs.readFileSync(process.argv[2], 'utf8'), context)
const flush = () => new Promise(resolve => setImmediate(resolve))
async function main () {
  await flush(); await flush()
  element('#journal-extra-track').val('OSS')
  handlers['#journal-extra-track:change:'].call(element('#journal-extra-track'))
  const row = element('row')
  row.attr = function () { return '~AE1' }
  row.find = function (selector) { const item = element(selector); item.checked = selector.indexOf('Regular') >= 0; return item }
  const button = element('button'); button.closest = function () { return row }
  handlers['#invitation-container:click:.journal-save'].call(button)
  await flush(); await flush(); await flush()
  process.stdout.write(JSON.stringify({ retired: retired.sort(), remaining: managed.length }))
}
main().catch(error => { console.error(error); process.exitCode = 1 })
