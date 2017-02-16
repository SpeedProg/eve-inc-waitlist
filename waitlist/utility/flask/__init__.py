import logging
from datetime import datetime

import math
from flask_login import current_user
from flask_principal import Identity, UserNeed, RoleNeed, identity_loaded
from sqlalchemy.exc import StatementError

from waitlist import principals, app, db, login_manager
from waitlist.blueprints.fc_sso import get_sso_redirect
from waitlist.storage.database import Account
from waitlist.utility.account import force_logout
from waitlist.utility.eve_id_utils import is_char_banned, get_account_from_db, get_char_from_db

logger = logging.getLogger(__name__)


@principals.identity_loader
def load_identity_when_session_expires():
    if hasattr(current_user, 'get_id'):
        return Identity(current_user.get_id())


@app.before_request
def check_ban():
    if current_user.is_authenticated:
        if current_user.type == "character":
            is_banned, _ = is_char_banned(current_user)
            if is_banned:
                force_logout()
        elif current_user.type == "account":
            if current_user.disabled:
                force_logout()


@login_manager.user_loader
def load_user(unicode_id):
    # it is an account
    try:
        return get_user_from_db(unicode_id)
    except StatementError:
        db.session.rollback()
        logger.exception("Failed to get user from db")
        return get_user_from_db(unicode_id)


def get_user_from_db(unicode_id):
    if unicode_id.startswith("acc"):
        unicode_id = unicode_id.replace("acc", "", 1)
        return get_account_from_db(int(unicode_id))

    if unicode_id.startswith("char"):
        unicode_id = unicode_id.replace("char", "", 1)
        return get_char_from_db(int(unicode_id))

    return None


@identity_loaded.connect_via(app)
def on_identity_loaded(sender, identity):
    # Set the identity user object
    identity.user = current_user
    # Add the UserNeed to the identity
    logger.info("loading identity for %s", current_user)
    if hasattr(current_user, 'id'):
        identity.provides.add(UserNeed(current_user.id))

    if hasattr(current_user, "type"):  # it is a custom user class
        if current_user.type == "account":  # it is an account, so it can have roles
            account = db.session.query(Account).filter(Account.id == current_user.id).first()
            for role in account.roles:
                logger.info("Add role %s", role.name)
                identity.provides.add(RoleNeed(role.name))


@login_manager.unauthorized_handler
def unauthorized_ogb():
    """
    Handle unauthorized users that visit with an out of game browser
    -> Redirect them to SSO
    """
    return get_sso_redirect('linelogin', '')


@app.template_filter('waittime')
def jinja2_waittime_filter(value):
    current_utc = datetime.utcnow()
    waited_time = current_utc - value
    return str(int(math.floor(waited_time.total_seconds()/60)))
