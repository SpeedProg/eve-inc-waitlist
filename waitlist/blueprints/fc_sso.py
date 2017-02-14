from flask import Response
from flask.blueprints import Blueprint
import logging
from flask_login import login_required
from waitlist.data.perm import perm_management
from werkzeug.utils import redirect
from flask.globals import request, session, _app_ctx_stack
from flask_seasurf import randrange
import hashlib
from waitlist.utility.config import crest_return_url, crest_client_id
import flask
from urllib.parse import urlencode

bp = Blueprint('fc_sso', __name__)
logger = logging.getLogger(__name__)

sso_handler = {}


def add_sso_handler(key: str, handler):
    sso_handler[key] = handler


def remove_handler(key: str):
    sso_handler.pop(key, None)


@bp.route("/login")
@login_required
@perm_management.require(http_exception=401)
def login_redirect() -> Response:
    return get_sso_redirect("setup", 'fleetRead fleetWrite')


def get_sso_redirect(action, scopes) -> Response:
    sso_token = get_sso_token()
    params = urlencode({
                        'response_type': 'code',
                        'redirect_uri': crest_return_url,
                        'client_id': crest_client_id,
                        'state': action+'-'+sso_token,
                        'scope': scopes
                        })
    return redirect("https://login.eveonline.com/oauth/authorize?"+params, code=302)


@bp.route("/cb")
def login_cb():
    code = request.args.get('code')
    state = request.args.get('state')

    handle_key = state.split('-', 2)[0]
    handler = sso_handler.get(handle_key)
    if handler is None:
        flask.abort(400)
    else:
        return handler(code)


def get_sso_token() -> str:
    csrf_name = '_sso_token'
    csrf_token = session.get(csrf_name, None)
    if not csrf_token:
        csrf_token = generate_token()
        setattr(_app_ctx_stack.top, csrf_name, csrf_token)
    else:
        setattr(_app_ctx_stack.top, csrf_name, csrf_token)
    return csrf_token


def generate_token():
    salt = str(randrange(0, 2 << 63)).encode('utf-8')
    return hashlib.sha1(salt).hexdigest()
