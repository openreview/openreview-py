def get_webfield(header='', title='', info='', url='', invitation=''):
    webfield = """
    <html>
      <head>
      </head>
      <body>
        <div id='main'>
          <div id='header'></div>
          <div id='invitation'></div>
          <div id='notes'></div>
        </div>
        <script type="text/javascript">
        $(function() {

          $attach('#header', 'mkHostHeader', [
          '%s', '%s', '%s', '%s'
          ], true);

          var sm = mkStateManager();

          var httpGetP = function(url, queryOrBody) {
            var df = $.Deferred();
            httpGet(url, queryOrBody,
            function(result) {
              df.resolve(result);
            },
            function(result) {
              df.reject(result);
            });
            return df.promise();
          };

          var invitationP = httpGetP('invitations', {id: '%s'}).then(function(result) {
            var valid_invitations = _.filter(result.invitations, function(inv){
              return inv.duedate > Date.now();
            })

            return valid_invitations[0];

          },
          function(error){
            return error
          });

          var notesP = httpGetP('notes', {invitation: '%s'}).then(function(result) {
            return result.notes;
          },
          function(error){
            return error
          });


          $.when(invitationP, notesP).done(function(invitation, notes) {
            console.log('invitation',invitation)
            if(invitation){
              sm.update('invitationTrip', {
                invitation: invitation
              });
            }
            sm.update('notes', notes);

            sm.addHandler('conference', {
              invitationTrip: function(invitationTrip) { if (invitationTrip) {
                var invitation = invitationTrip.invitation;
                $attach('#invitation', 'mkInvitationButton', [invitation, function() {
                  if (user && !user.id.startsWith('guest_') && invitation) {
                    view.mkNewNoteEditor(invitation, null, null, user, {
                      onNoteCreated: function(idRecord) {
                        httpGetP('notes', {
                          invitation: '%s'
                        }).then(function(result) {
                          console.log("time to update notes: " + result.notes.length);
                          sm.update('notes', result.notes);
                        },
                        function(error){
                          return error
                        });
                      },
                      onCompleted: function(editor) {
                        $('#notes').prepend(editor);
                      },
                      onError: function(error) {
                        if (error) {
                          var errors = error.responseJSON ? error.responseJSON.errors : null;
                          var message = errors ? errors[0] : 'Something went wrong';
                          if(message == "Invitation has expired") {
                            promptError("The submission is closed");
                          } else {
                            promptError(message);
                         }
                        }
                      }
                    });
                  } else {
                   promptLogin(user);
                  }
                }], true);
              }},

              notes: function(notes) {
                if (notes) {
                  $('#notes').empty();
                  _.forEach(notes, function(note) {
                    $attach('#notes', 'mkNotePanel', [note, {
                      titleLink: 'HREF',
                      withReplyCount: true
                    }], true);
                  });
                }
              }
            });

          })
          .fail(function(){
            console.log("Invitation and/or notes not found")
          });
        });
        </script>
     </body>
    </html>
    """ % (header, title, info, url, invitation, invitation, invitation)
    return webfield
