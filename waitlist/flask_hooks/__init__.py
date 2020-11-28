import logging
import math
from datetime import datetime
from typing import List, Union, Optional, Any, Dict, Callable

import flask
from flask import render_template, url_for, request, jsonify
from flask_login import current_user, AnonymousUserMixin
from flask_principal import Identity, UserNeed, RoleNeed, identity_loaded
from werkzeug.utils import redirect
from flask_babel import gettext
from flask.wrappers import Response
from sqlalchemy import distinct
from sqlalchemy.inspection import inspect

from waitlist.utility.settings import sget_insert
from waitlist.data.version import version
from waitlist.permissions import perm_manager
from waitlist.utility.mainmenu import main_nav
from waitlist.utility.outgate.exceptions import ApiException
from waitlist.base import principals, app, db, login_manager
from waitlist.blueprints.fc_sso import get_sso_redirect
from waitlist.utility.config import cdn_eveimg, cdn_eveimg_webp, cdn_eveimg_js, influence_link, title
from waitlist.storage.database import Account, Character, Role, roles, SSOToken
from waitlist.utility import config
from waitlist.utility.account import force_logout
from waitlist.utility.eve_id_utils import is_char_banned, get_account_from_db, get_char_from_db
from waitlist.utility.i18n.locale import get_locale, get_langcode_from_locale
from waitlist.utility.login import invalidate_all_sessions_for_current_user
from waitlist.utility.manager import owner_hash_check_manager

logger = logging.getLogger(__name__)


def load_identity_when_session_expires():
    if hasattr(current_user, 'get_id'):
        return Identity(current_user.get_id())


def check_user_owner_hash():
    # we want to allow requests to accounts.account_self_edit here
    # and sso

    # if it is static path let it continue
    static_path_root = url_for('static', filename='')
    if request.path.startswith(static_path_root):
        logger.debug("request.path %s in static_path_root %s, not checking owner_hash", request.path, static_path_root)
        return None

    # if it is allowed let it continue with an other handle
    allowed_endpoints = [url_for('fc_sso.login_cb'), ]
    if request.path in allowed_endpoints:
        logger.debug("request.path %s in allowed_endpoints, not checking owner_hash", request.path)
        return None

    user: Optional[Union[Account, Character, AnonymousUserMixin]] = current_user

    if not hasattr(user, 'type'):
        logger.debug("AnonymouseUserMixin no need to check hashes")
        return
    try:
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
                flask.flash(gettext(
                    "Your set current character %(eve_name)s" +
                    " was unset because the provided token got invalidated."+
                    " Go to Own Settings to re-add.",
                    eve_name=user.get_eve_name()),
                    'danger')
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
    except Exception:
        logger.exception('Exception during user owner_hash check!')
    # else
    logger.debug("Everything okay, the request can continue")
    return None


def check_ban():
    if current_user.is_authenticated:
        if current_user.type == "character":
            is_banned, _ = is_char_banned(current_user)
            if is_banned:
                force_logout()
        elif current_user.type == "account":
            if current_user.disabled:
                force_logout()


def check_all_alts_authorized():
    # the requirement is disabled
    user: Account = current_user
    if not config.require_auth_for_chars:
        return

    # alts are only for 'account' type users
    if (not user.is_authenticated) or (user.type != 'account'):
        return

    # if it is static path let it continue
    static_path_root = url_for('static', filename='')
    if request.path.startswith(static_path_root):
        logger.debug("request.path %s in static_path_root %s, not checking alts authorized",
                     request.path, static_path_root)
        return None

    # we want to allow requests to accounts.account_self_edit here
    # and sso
    allowed_endpoints = [url_for('accounts.account_self_edit'), url_for('fc_sso.login_cb'), url_for('logout'), url_for('static', filename='')]

    # if it is allowed let it continue with an other handle
    if request.path in allowed_endpoints:
        logger.debug("request.path %s in allowed_endpoints %s, not checking alts authorized",
                     request.path, allowed_endpoints)
        return None

    # check all the chars are authorized
    # basically there is a sso token for all the alts
    accountSSOTokenCharacterIDs = db.session.query(distinct(SSOToken.characterID)).\
        filter(SSOToken.accountID == current_user.id)

    unauthed_chars: List[Character] = db.session.query(Character).\
        join(Account.characters).\
        filter(Account.id == current_user.id, Character.id.notin_(accountSSOTokenCharacterIDs)).\
        all()
    # we found at least 1 not authed character
    if len(unauthed_chars) > 0:
        return get_view_to_unauthed_character_list(unauthed_chars)

    # we have no unauthed characters
    return None


def get_view_to_unauthed_character_list(unauthed_chars: List[Account]) -> str:

    return render_template("account/unauthed_characters_form.html", char_list=unauthed_chars, account=current_user)

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

def on_identity_loaded(_: Any, identity):
    # Set the identity user object
    identity.user = current_user
    # Add the UserNeed to the identity
    logger.debug("loading identity for %s", current_user)
    if hasattr(current_user, 'id'):
        identity.provides.add(UserNeed(current_user.id))

    if hasattr(current_user, "type"):  # it is a custom user class
        if current_user.type == "account":  # it is an account, so it can have roles
            acc_roles = db.session.query(Role.name).join(roles).filter(roles.c.account_id == current_user.id).all()
            for role in acc_roles:
                logger.debug("Add role %s", role.name)
                identity.provides.add(RoleNeed(role.name))

def unauthorized_ogb():
    """
    Handle unauthorized users that visit with an out of game browser
    -> Redirect them to SSO
    """
    return get_sso_redirect('linelogin', 'publicData')


def jinja2_waittime_filter(value):
    current_utc = datetime.utcnow()
    waited_time = current_utc - value
    return str(int(math.floor(waited_time.total_seconds()/60)))


def handle_invalid_usage(error: ApiException) -> Response:
    response = jsonify(error.to_dict())
    response.status_code = error.code
    return response

def eve_image(browser_webp: bool) -> Callable[[str, str], str]:
    if browser_webp and cdn_eveimg_webp:
        def _eve_image(path: str, _: str) -> str:
            return cdn_eveimg.format(path, 'webp')
    else:
        def _eve_image(path: str, suffix: str) -> str:
            return cdn_eveimg.format(path, suffix)
    return _eve_image


def get_header_insert():
    return sget_insert('header')

def inject_data() -> Dict[str, Any]:
    is_account = False
    if hasattr(current_user, 'type'):
        is_account = (current_user.type == "account")

    req_supports_webp = 'image/webp' in request.headers.get('accept', '')
    eve_image_macro: Callable[[str, str], str] = eve_image(req_supports_webp)
    return dict(version=version,
                perm_manager=perm_manager, get_header_insert=get_header_insert,
                eve_proxy_js=cdn_eveimg_js, eve_cdn_webp=cdn_eveimg_webp,
                browserSupportsWebp=req_supports_webp, eve_image=eve_image_macro,
                influence_link=influence_link, is_account=is_account,
                title=title, lang_code=get_langcode_from_locale(get_locale(app)),
                main_nav=main_nav
                )

def get_pk(obj):
    return inspect(obj).identity

def register_hooks(app) -> None:
    app.context_processor(inject_data)
    app.errorhandler(ApiException)(handle_invalid_usage)
    app.template_filter('waittime')(jinja2_waittime_filter)
    login_manager.unauthorized_handler(unauthorized_ogb)
    identity_loaded.connect_via(on_identity_loaded)
    login_manager.user_loader(load_user)
    app.before_request(check_all_alts_authorized)
    app.before_request(check_ban)
    app.before_request(check_user_owner_hash)
    principals.identity_loader(load_identity_when_session_expires)
    app.jinja_env.globals.update(get_pk=get_pk)

