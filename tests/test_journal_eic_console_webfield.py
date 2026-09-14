import json
from pathlib import Path
import shutil
import subprocess

import pytest


WEBFIELD = Path(__file__).parents[1] / "openreview/journal/webfield/editorsInChiefWebfield.js"
NODE = shutil.which("node")


def run_webfield_probe(invitations):
    if not NODE:
        pytest.skip("Node.js is required for the Journal webfield unit test")

    script = r"""
const fs = require('fs');
const vm = require('vm');

let source = fs.readFileSync(process.argv[1], 'utf8')
  .replace("var VENUE_ID = '';", "var VENUE_ID = 'TMLR';")
  .replace("var REVIEWERS_NAME = '';", "var REVIEWERS_NAME = 'Reviewers';")
  .replace("var ACTION_EDITOR_NAME = '';", "var ACTION_EDITOR_NAME = 'Action_Editors';")
  .replace(/\nmain\(\);\s*$/, '');
const invitations = JSON.parse(process.argv[2]);
let request;
const context = {
  console: console,
  encodeURIComponent: encodeURIComponent,
  Webfield2: {
    api: {
      getAll: function(path, params) {
        request = { path: path, params: params };
        return Promise.resolve(invitations);
      }
    },
    utils: {}
  }
};
vm.createContext(context);
vm.runInContext(source, context);

(async function() {
  const collections = await context.getEicInvitations();
  let rejection;
  context.Webfield2.api.getAll = function() {
    return Promise.reject(new Error('permission denied'));
  };
  try {
    await context.getEicInvitations();
  } catch (error) {
    rejection = error.message;
  }
  process.stdout.write(JSON.stringify({ request, collections, rejection }));
}()).catch(function(error) {
  console.error(error);
  process.exit(1);
});
"""
    completed = subprocess.run(
        [NODE, "-e", script, str(WEBFIELD), json.dumps(invitations)],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def test_eic_console_uses_supported_paginated_invitation_query():
    result = run_webfield_probe([])

    assert result["request"] == {
        "path": "/invitations",
        "params": {
            "invitation": "TMLR/-/Edit",
            "type": "all",
            "select": "id,cdate,duedate,expdate",
            "expired": True,
            "sort": "cdate:asc",
            "domain": "TMLR",
        },
    }
    assert result["rejection"] == "permission denied"


def test_eic_console_filters_complete_id_boundaries_and_preserves_order():
    invitations = [
        {"id": "OTHER/-/Decision"},
        {"id": "TMLR/Paperwork1/-/Review"},
        {"id": "TMLR/Paper2/-/Review", "marker": "first"},
        {"id": "TMLR/Paper2/-/Review", "marker": "last"},
        {"id": "TMLR/Paper10/-/Decision", "expdate": 1},
        {"id": "TMLR/-/Submission"},
        {"id": "TMLR/-/Decision"},
        {"id": "TMLR2/-/Decision"},
        {"id": "TMLR/Reviewers/-/Assignment"},
        {"id": "TMLR/Reviewers_Extra/-/Assignment"},
        {"id": "TMLR/Action_Editors/-/Assignment"},
        {"id": "TMLR/Action_Editors_Archived/-/Assignment"},
        {},
    ]
    collections = run_webfield_probe(invitations)["collections"]

    assert list(collections["invitationsById"]) == [
        "TMLR/Paper2/-/Review",
        "TMLR/Paper10/-/Decision",
    ]
    assert collections["invitationsById"]["TMLR/Paper2/-/Review"]["marker"] == "last"
    assert [item["id"] for item in collections["superInvitationIds"]] == [
        "TMLR/-/Submission",
        "TMLR/-/Decision",
    ]
    assert [item["id"] for item in collections["reviewerInvitationIds"]] == [
        "TMLR/Reviewers/-/Assignment"
    ]
    assert [item["id"] for item in collections["aeInvitationIds"]] == [
        "TMLR/Action_Editors/-/Assignment"
    ]
