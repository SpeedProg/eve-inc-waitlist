import logging
import math
from datetime import datetime
from typing import List, Union, Optional, Any

import flask
from flask import render_template, url_for, request
from flask_login import current_user, AnonymousUserMixin
from flask_principal import Identity, UserNeed, RoleNeed, identity_loaded
from werkzeug.utils import redirect

from waitlist import principals, app, db, login_manager
from waitlist.blueprints.fc_sso import get_sso_redirect
from waitlist.storage.database import Account, Character
from waitlist.utility import config
from waitlist.utility.account import force_logout
from waitlist.utility.eve_id_utils import is_char_banned, get_account_from_db, get_char_from_db
from waitlist.utility.login import invalidate_all_sessions_for_current_user
from waitlist.utility.manager import owner_hash_check_manager

logger = logging.getLogger(__name__)


@principals.identity_loader
def load_identity_when_session_expires():
    if hasattr(current_user, 'get_id'):
        return Identity(current_user.get_id())


@app.before_request
def check_user_owner_hash():
    # we want to allow requests to accounts.account_self_edit here
    # and sso
    allowed_endpoints = [url_for('fc_sso.login_cb')]

    # if it is allowed let it continue with an other handle
    if request.path in allowed_endpoints:
        logger.debug("request.path %s in allowed_endpoints, not checking owner_hash", request.path)
        return None

    user: Optional[Union[Account, Character, AnonymousUserMixin]] = current_user

    if not hasattr(user, 'type'):
        logger.debug("AnonymouseUserMixin no need to check hashes")
        return

    if user.type == 'account':
        # if no auth for alts is required there is no reason to check the owner_hash
        if not config.require_auth_for_chars:
            logger.debug("Skipping owner_hash check because it is disabled in the configuration")
            return
        user: Account = user
        # if there is NO main character set ignore the hash check
        if user.current_char is None:
            logger.debug("%s has no current character set, ignore owner_hash check.", user)
            return

        if not owner_hash_check_manager.is_ownerhash_valid(user):
            logger.info("owner_hash for %s was invalid. Removing connected character %s.", user, user.current_char_obj)
            flask.flash(f"Your set current character {user.get_eve_name()}"
                        f" was unset because the provided token got invalidated."
                        f" Go to Own Settings to re-add.", 'danger')
            user.current_char = None
            db.session.commit()
            return redirect(url_for('index'))

    else:
        if not owner_hash_check_manager.is_ownerhash_valid(user):
            user.current_char = None
            logger.info("owner_hash for %s was invalid. Invalidating all sessions and logging out.", user)
            invalidate_all_sessions_for_current_user()
            force_logout()
            return redirect(url_for('index'))

    # else
    logger.debug("Everything okay, the request can continue")
    return None


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


@app.before_request
def check_all_alts_authorized():
    # the requirement is disabled
    user: Account = current_user
    if not config.require_auth_for_chars:
        return

    # alts are only for 'account' type users
    if (not user.is_authenticated) or (user.type != 'account'):
        return

    # we want to allow requests to accounts.account_self_edit here
    # and sso
    allowed_endpoints = [url_for('accounts.account_self_edit'), url_for('fc_sso.login_cb'), url_for('logout')]

    # if it is allowed let it continue with an other handle
    if request.path in allowed_endpoints:
        return None

    unauthed_chars: List[Character] = []
    # check all the chars are authorized
    # basically there is a sso token for all the alts

    # TODO: this could be done with an sql query
    for character in user.characters:
        found_key: bool = False
        for sso_token in user. ssoTokens:
            if sso_token.characterID == character.id:
                found_key = True
                break

        if not found_key:
            unauthed_chars.append(character)

    # we found at least 1 not authed character
    if len(unauthed_chars) > 0:
        return get_view_to_unauthed_character_list(unauthed_chars)

    # we have no unauthed characters
    return None


def get_view_to_unauthed_character_list(unauthed_chars: List[Account]) -> str:

    return render_template("account/unauthed_characters_form.html", char_list=unauthed_chars, account=current_user)


@login_manager.user_loader
def load_user(unicode_id):
    user: Optional[Union[Account, Character]] = get_user_from_db(unicode_id)

    if user is None:
        return None

    return user


def get_user_from_db(unicode_id: str) -> Optional[Union[Character, Account]]:
    if '_' not in unicode_id:
        return None

    if unicode_id.startswith("acc"):
        unicode_id = unicode_id.replace("acc", "", 1)

        acc_id, session_key = unicode_id.split("_", 2)
        account: Account = get_account_from_db(int(acc_id))

        logger.debug("Loading account from db id=%s session_key=%s", acc_id, session_key)
        if account is None:
            logger.debug("Account with id=%s not found", acc_id)
        else:
            logger.debug("Found %s", account)

        return account if account is not None and account.session_key == int(session_key) else None

    if unicode_id.startswith("char"):
        unicode_id = unicode_id.replace("char", "", 1)

        char_id, session_key = unicode_id.split("_", 2)
        char: Character = get_char_from_db(int(char_id))

        logger.debug("Loading character from db id=%s session_key=%s", char_id, session_key)
        if char is None:
            logger.debug("Account with id=%s not found", char_id)
        else:
            logger.debug("Found %s", char)

        return char if char is not None and char.session_key == int(session_key) else None

    return None


@identity_loaded.connect_via(app)
def on_identity_loaded(_: Any, identity):
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

    return get_sso_redirect('linelogin', 'publicData')


@app.template_filter('waittime')
def jinja2_waittime_filter(value):
    current_utc = datetime.utcnow()
    waited_time = current_utc - value
    return str(int(math.floor(waited_time.total_seconds()/60)))
