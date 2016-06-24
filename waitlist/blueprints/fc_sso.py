from flask.blueprints import Blueprint
import logging
from flask_login import login_required, current_user
from waitlist.data.perm import perm_management
from werkzeug.utils import redirect
from flask.globals import request, session, _app_ctx_stack
from flask_seasurf import randrange, _MAX_CSRF_KEY
import hashlib
import requests
import base64
from datetime import datetime, timedelta
from waitlist.base import db
from flask.helpers import url_for
from urllib import urlencode
from waitlist.utility.config import crest_return_url, crest_client_secret, crest_client_id
from evelink import account
from waitlist.utility.crest import create_token_cb
from pycrest.eve import AuthedConnectionB
import flask

bp = Blueprint('fc_sso', __name__)
logger = logging.getLogger(__name__)

sso_handler = {}

def add_sso_handler(key, handler):
    sso_handler[key] = handler

def remove_handler(key):
    sso_handler.pop(key, None)

@bp.route("/login")
@login_required
@perm_management.require(http_exception=401)
def login_redirect():
    return get_sso_redirect("setup", 'fleetRead fleetWrite')

def get_sso_redirect(action, scopes):
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

def get_sso_token():
    csrf_name = '_sso_token'
    csrf_token = session.get(csrf_name, None)
    if not csrf_token:
        csrf_token = generate_token()
        setattr(_app_ctx_stack.top,
                    csrf_name,
                    csrf_token)
    else:
        setattr(_app_ctx_stack.top, csrf_name, csrf_token)
    return csrf_token

def generate_token():
    salt = str(randrange(0, _MAX_CSRF_KEY)).encode('utf-8')
    return hashlib.sha1(salt).hexdigest()