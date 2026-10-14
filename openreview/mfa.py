import sys
from . import tools


def _is_interactive():
    """Check if interactive input is available (terminal or notebook)."""
    if sys.stdin.isatty():
        return True
    try:
        if 'IPKernelApp' in get_ipython().config:
            return True
    except NameError:
        pass
    return False

def _default_mfa_method_chooser(mfa_methods, preferred_method):
    """Phase 1: Choose MFA method interactively."""
    supported = [m for m in mfa_methods if m in ('totp', 'emailOtp', 'passkey')]
    if not supported:
        return None
    print('\nMulti-factor authentication is required.')
    if len(supported) == 1:
        print(f'Using method: {supported[0]}')
        return supported[0]
    print(f'Available methods: {", ".join(supported)}')
    method_input = input(f'Choose method [{preferred_method}]: ').strip()
    return method_input if method_input in supported else preferred_method

def _default_mfa_code_prompt(method):
    """Phase 2: Prompt for the verification code."""
    prompts = {
        'totp': 'Enter TOTP code from your authenticator app: ',
        'emailOtp': 'Enter the verification code sent to your email: ',
    }
    return input(prompts.get(method, f'Enter {method} code: ')).strip()

def _passkey_browser_flow(client, mfa_pending_token, timeout=120):
    """
    Open browser to API's WebAuthn page, receive auth token via local callback.
    Returns token_response_dict or None on timeout/failure.
    """
    import http.server
    import threading
    import webbrowser
    import urllib.parse
    import json as _json

    baseurl = client.baseurl
    result = {}

    site_url = tools.get_site_url(client)

    class CallbackHandler(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length).decode('utf-8')
            parsed = urllib.parse.parse_qs(body)
            result['token'] = parsed.get('token', [None])[0]
            result['user'] = parsed.get('user', [None])[0]
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            page = (
                '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
                '<meta name="viewport" content="width=device-width,initial-scale=1">'
                '<link rel="stylesheet" href="https://fonts.googleapis.com/css?family=Noto+Sans:400,700&display=swap">'
                '<title>Authentication Complete | OpenReview</title>'
                '<style>'
                '*{box-sizing:border-box;margin:0;padding:0}'
                'body{font-family:"Noto Sans","Helvetica Neue",Helvetica,Arial,sans-serif;'
                'background:#fffdfa;color:#2c3a4a;min-height:100vh;display:flex;flex-direction:column}'
                '.navbar{background-color:#8c1b13;padding:12px 0}'
                '.navbar-inner{max-width:960px;margin:0 auto;padding:0 15px}'
                '.navbar-brand{color:#fff;font-size:18px;text-decoration:none}'
                '.navbar-brand strong{font-weight:700}'
                '.main{flex:1;display:flex;justify-content:center;align-items:center;padding:40px 15px}'
                '.card{background:#fff;border:1px solid #ddd;border-radius:4px;'
                'padding:36px 40px;max-width:420px;width:100%;text-align:center}'
                '.card h1{font-size:22px;font-weight:700;color:#2c3a4a;margin-bottom:6px}'
                '.card .icon{font-size:48px;margin-bottom:12px}'
                '.card p{font-size:14px;color:#555;line-height:1.5}'
                '.footer{text-align:center;padding:16px 15px;font-size:12px;color:#999;border-top:1px solid #eee}'
                '.footer a{color:#4d8093;text-decoration:none}'
                '</style></head><body>'
                '<nav class="navbar"><div class="navbar-inner">'
                f'<a class="navbar-brand" href="{site_url}"><strong>OpenReview</strong>.net</a>'
                '</div></nav>'
                '<div class="main"><div class="card">'
                '<div class="icon">&#10003;</div>'
                '<h1>Authentication Complete</h1>'
                '<p>You may close this tab and return to your terminal.</p>'
                '</div></div>'
                '<footer class="footer">'
                f'<a href="{site_url}">OpenReview</a> &mdash; '
                'Open Peer Review. Open Publishing. Open Access.</footer>'
                '</body></html>'
            )
            self.wfile.write(page.encode('utf-8'))
        def log_message(self, format, *args):
            pass

    server = http.server.HTTPServer(('127.0.0.1', 0), CallbackHandler)
    port = server.server_address[1]
    server.timeout = timeout

    url = (f'{baseurl}/mfa/webauthn-auth'
           f'?pendingToken={urllib.parse.quote(mfa_pending_token)}'
           f'&callbackPort={port}')

    thread = threading.Thread(target=server.handle_request, daemon=True)
    thread.start()
    print('Opening browser for passkey authentication...')
    webbrowser.open(url)
    thread.join(timeout=timeout)
    server.server_close()

    if result.get('token'):
        return {'token': result['token'], 'user': _json.loads(result['user'])}
    return None
