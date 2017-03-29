from flask import Response
from flask.blueprints import Blueprint
import logging
from flask_login import login_required

from werkzeug.utils import redirect
from flask.globals import request, session, _app_ctx_stack
from flask_seasurf import randrange
import hashlib

from waitlist.permissions import perm_manager
from waitlist.utility.config import crest_return_url, crest_client_id
import flask
from urllib.parse import urlencode

from waitlist.utility.login import member_login_cb

bp = Blueprint('fc_sso', __name__)
logger = logging.getLogger(__name__)

perm_manager.define_permission('fleet_manage')

perm_fleet_manage = perm_manager.get_permission('fleet_manage')

sso_handler = {}


def add_sso_handler(key: str, handler):
    sso_handler[key] = handler


def remove_handler(key: str):
    sso_handler.pop(key, None)


@bp.route("/login")
@login_required
@perm_fleet_manage.require(http_exception=401)
def login_redirect() -> Response:
    return get_sso_redirect("setup", 'esi-ui.open_window.v1 esi-fleets.read_fleet.v1 esi-fleets.write_fleet.v1')


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

    handle_key = state.split('-', 1)[0]
    handler = sso_handler.get(handle_key)
    if handler is None:
        logger.error(f'No handler for sso return handle_key[{handle_key}] found. State[{state}]')
        flask.abort(400, 'No Handler for this sso return found!')
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

add_sso_handler('linelogin', member_login_cb)
