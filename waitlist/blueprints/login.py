from flask_login.utils import login_required, logout_user, login_user
from waitlist.base import db
import flask
from flask_principal import identity_changed, AnonymousIdentity, Identity
from flask.globals import current_app, request
from flask.templating import render_template
import logging
from waitlist.utility import config
from waitlist.storage.database import Account
from werkzeug.utils import redirect
from flask.helpers import url_for
from flask.blueprints import Blueprint
from gettext import gettext as _

logger = logging.getLogger(__name__)

bp = Blueprint('login', __name__)

@bp.route('/logout')
@login_required
def logout():
    logout_user()

    for key in ('identity.name', 'identity.auth_type'):
        flask.globals.session.pop(key, None)

    # Tell Flask-Principal the user is anonymous
    identity_changed.send(current_app._get_current_object(),
                          identity=AnonymousIdentity())

    return render_template("logout.html")

# callable like /tokenauth?token=359th8342rt0f3uwf0234r
@bp.route('/tokenauth')
def login_token():
    if not config.debug_enabled:
        flask.abort(404, _("Tokens where removed, please use the EVE SSO"))
        return

    token = request.args.get('token')
    user = db.session.query(Account).filter(Account.login_token == token).first()

    # token was not found
    if user is None:
        return flask.abort(401)

    if user.disabled:
        return flask.abort(403)

    logger.info("Got User %s", user)
    login_user(user)
    logger.info("Logged in User %s", user)

    # notify principal extension
    identity_changed.send(current_app._get_current_object(),
                          identity=Identity(user.id))

    return redirect(url_for('index'), code=303)