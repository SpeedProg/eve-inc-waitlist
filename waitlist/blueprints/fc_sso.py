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
from waitlist import db
from flask.helpers import url_for
bp = Blueprint('fc_sso', __name__)
logger = logging.getLogger(__name__)

@bp.route("/login")
@login_required
@perm_management.require(http_exception=401)
def login_redirect():
    csrf_token = get_csrf_token()
    return redirect("https://login.eveonline.com/oauth/authorize?response_type=code&redirect_uri=http%3A%2F%2Fspeedprog.ddns.net%3A81%2Ffc_sso%2Fcb&client_id=6f5fa2e4ff05442f88feaea8a34b4799&scope=fleetRead%20fleetWrite&state=setup-"+csrf_token, code=302)

@bp.route("/cb")
@login_required
@perm_management.require(http_exception=401)
def login_cb():
    code = request.args.get('code')
    state = request.args.get('state')

    header = {'Authorization': 'Basic '+base64.b64encode("6f5fa2e4ff05442f88feaea8a34b4799:i9ob7wY72cy6ETVQtxHQVvPnHG5uhf5qmoFPuJOF"),
              'Content-Type': 'application/x-www-form-urlencoded',
              'Host': 'login.eveonline.com'}
    params = {'grant_type': 'authorization_code',
              'code': code}
    r = requests.post("https://login.eveonline.com/oauth/token", headers=header, params=params)
    json = r.json()

    re_token = json['refresh_token']
    acc_token = json['access_token']
    exp_in = int(json['expires_in'])
    current_user.refresh_token = re_token
    current_user.access_token = acc_token
    current_user.access_token_expires = datetime.utcnow() + timedelta(seconds=exp_in)
    db.session.commit()
    
    if state.startswith("setup-"):
        return redirect(url_for("fleet.setup_start"))
    else:
        return redirect(url_for("fleet.take_form"))
def get_csrf_token():
    csrf_name = '_csrf_token'
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