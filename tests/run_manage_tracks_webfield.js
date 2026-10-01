'use strict'

const fs = require('fs')
const vm = require('vm')
const assert = require('assert')

const handlers = {}
const elements = {}
function element (selector) {
  if (!elements[selector]) {
    elements[selector] = {
      value: '', textValue: '',
      html: function (value) {
        if (value === undefined) return this.htmlValue
        this.htmlValue = value; return this
      },
      text: function (value) {
        if (value === undefined) return this.textValue
        this.textValue = String(value); return this
      },
      on: function (event, child, callback) {
        handlers[selector + ':' + event] = callback || child; return this
      },
      each: function () { return this },
      prop: function () { return false },
      val: function (value) {
        if (value === undefined) return this.value
        this.value = value; return this
      },
      find: function () { return this },
      attr: function () { return undefined },
      closest: function () { return this }
    }
  }
  return elements[selector]
}
function $ (selector) {
  if (typeof selector === 'string' && selector === '<div>') {
    return {
      text: function (value) { this.value = String(value); return this },
      html: function () {
        return this.value.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      }
    }
  }
  return element(selector)
}

let revision = 10
let tracks = [{ id: 'Regular', name: 'Track " autofocus onfocus="alert(1) & <tag>', open: true }]
let postCount = 0
let failNextGet = false
const api = {
  get: function () {
    if (failNextGet) {
      failNextGet = false
      return Promise.reject(new Error('Authoritative reload failed.'))
    }
    return Promise.resolve({ groups: [{ tmdate: revision, content: {
      tracks: { value: tracks }
    } }] })
  },
  post: function (_path, edit) {
    if (edit.content) throw new Error('Track edits must not carry a base revision')
    postCount += 1
    tracks = edit.group.content.tracks.value
    revision += 1
    return Promise.resolve({})
  }
}

const context = {
  $, console,
  Webfield2: { api, ui: { done: function () {} } },
  Promise, setTimeout, clearTimeout
}
vm.runInNewContext(fs.readFileSync(process.argv[2], 'utf8'), context)

const flush = () => new Promise(resolve => setImmediate(resolve))
async function main () {
  await flush()
  assert(element('#journal-track-body').html().includes(
    'value="Track &quot; autofocus onfocus=&quot;alert(1) &amp; &lt;tag&gt;">'))
  handlers['#journal-track-save:click']()
  await flush(); await flush()
  handlers['#journal-track-save:click']()
  await flush(); await flush()
  failNextGet = true
  handlers['#journal-track-save:click']()
  await flush(); await flush()
  const reloadStatus = element('#journal-track-status').text()
  revision += 1 // a serial later save accepts the editor's complete order
  handlers['#journal-track-save:click']()
  await flush(); await flush()
  process.stdout.write(JSON.stringify({
    postCount,
    reloadStatus,
    status: element('#journal-track-status').text()
  }))
}
main().catch(error => { console.error(error); process.exitCode = 1 })
