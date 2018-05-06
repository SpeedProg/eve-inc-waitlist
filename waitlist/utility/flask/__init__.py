import logging
from datetime import datetime, timedelta, timezone

import math

from esipy import EsiSecurity
from esipy.exceptions import APIException
from typing import List, Union, Optional, Dict

from flask import render_template, url_for, request
from flask_login import current_user, AnonymousUserMixin
from flask_principal import Identity, UserNeed, RoleNeed, identity_loaded
from sqlalchemy.exc import StatementError

from waitlist import principals, app, db, login_manager
from waitlist.blueprints.fc_sso import get_sso_redirect
from waitlist.permissions import perm_manager
from waitlist.sso import who_am_i
from waitlist.storage.database import Account, Character
from waitlist.utility import config
from waitlist.utility.account import force_logout
from waitlist.utility.eve_id_utils import is_char_banned, get_account_from_db, get_char_from_db
from waitlist.utility.login import set_token_data, invalidate_all_sessions_for_current_user

logger = logging.getLogger(__name__)


@principals.identity_loader
def load_identity_when_session_expires():
    if hasattr(current_user, 'get_id'):
        return Identity(current_user.get_id())


@app.before_request
def check_user_owner_hash():
    user: Optional[Union[Account, Character, AnonymousUserMixin]] = current_user

    if not hasattr(user, 'type'):
        logger.info("AnonymouseUserMixin no need to check hashes")
        return

    if user.type == 'account':
        logger.info("Account type, we need to check hashes")
        user: Account = user
        # if there is NO main character set just force a logout
        if user.current_char_obj is None:
            logger.info("Force logount because %s has no current_char_object", user)
            force_logout()
            return

        char_id = user.current_char

        if not need_to_do_owner_hash_check(char_id):
            logger.debug("We already did the owner_hash check during the current window")
            return

        if user.sso_token is None:
            logger.info("%s sso_token is None, force logout and invalidate all sessions", user)
            invalidate_all_sessions_for_current_user()
            force_logout()
            return None

        security = EsiSecurity('', client_id=config.crest_client_id, secret_key=config.crest_client_secret)
        security.refresh_token = user.sso_token.refresh_token
        try:
            security.refresh()

            # the token still works
            auth_info = who_am_i(security.access_token)
            owner_hash = auth_info['CharacterOwnerHash']
            scopes = auth_info['Scopes']

            set_token_data(user.sso_token, security.access_token, security.refresh_token,
                           datetime.fromtimestamp(security.token_expiry), scopes)
            db.session.commit()
            if owner_hash != user.current_char_obj.owner_hash:
                logger.info("%s owner_hash did not match, force logout and invalidate all sessions", user)
                invalidate_all_sessions_for_current_user()
                force_logout()
                return None

            # owner hash still matches
            set_last_successful_owner_hash_check(user.get_eve_id())
            logger.debug("%s owner_hash did match, let the request continue", user)
            return None

        except APIException as e:
            # if this happens the token doesn't work anymore
            # => owner probably changed or for other reason
            logger.exception("API Error during token validation, invalidating all sessions and forcing logout", e)
            invalidate_all_sessions_for_current_user()
            force_logout()
            return None

    elif user.type == 'character':
        logger.info("Character type, we need to check owner_hash")
        user: Character = user
        if not need_to_do_owner_hash_check(user.id):
            logger.info("Hash check was already successfully done after the last downtime")
            return None
        security = EsiSecurity('', client_id=config.crest_client_id, secret_key=config.crest_client_secret)
        if user.sso_token is None:
            logger.info("User sso token is None, logging out")
            invalidate_all_sessions_for_current_user()
            force_logout()
            return None

        security.refresh_token = user.sso_token.refresh_token
        try:
            security.refresh()
            # the token still works
            auth_info = who_am_i(security.access_token)
            owner_hash = auth_info['CharacterOwnerHash']
            scopes = auth_info['Scopes']

            set_token_data(user.sso_token, security.access_token, security.refresh_token,
                           datetime.fromtimestamp(security.token_expiry), scopes)
            db.session.commit()

            # this is probably never gonna happen, since the token shouldn't work anymore after an owner change
            if owner_hash != user.owner_hash:
                logger.info("Characters current owner_hash did not match owner_hash in database")
                invalidate_all_sessions_for_current_user()
                force_logout()
                return None

            set_last_successful_owner_hash_check(user.get_eve_id())
            # owner hash still matches
            logger.debug("%s owner_hash did match, let the request continue", user)
            return None

        except APIException as e:
            # if this happens the token doesn't work anymore
            # => owner probably changed or for other reason
            logger.exception("API Error during token validation, invalidating all sessions and forcing logout", e)
            invalidate_all_sessions_for_current_user()
            force_logout()
            return None

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
    allowed_endpoints = [url_for('accounts.account_self_edit'), url_for('fc_sso.login_cb')]

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


last_owner_hash_check_lookup: Dict[int, datetime] = dict()


@login_manager.user_loader
def load_user(unicode_id):
    user: Optional[Union[Account, Character]] = get_user_from_db(unicode_id)

    if user is None:
        return None

    return user


def need_to_do_owner_hash_check(character_id: int) -> bool:
    if character_id in last_owner_hash_check_lookup:
        last_check: datetime = last_owner_hash_check_lookup[character_id]
        # if the last check was before the last downtime do a check
        if last_check < get_last_downtime():
            return True
        return False

    return True


def set_last_successful_owner_hash_check(character_id: int) -> None:
    last_owner_hash_check_lookup[character_id] = datetime.now(timezone.utc)


def get_last_downtime():
    # get current utc time
    current_time = datetime.utcnow()
    # downtime is at 11:00 UTC every day
    if current_time.hour < 11:
        # last downtime was 11 utc 1 day earlier
        current_time -= timedelta(days=1)

    # if we are past dt, dt was today at 11 UTC no need to substract
    current_time = current_time.replace(hour=11, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)

    return current_time


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
    return get_sso_redirect('linelogin', 'publicData')


@app.template_filter('waittime')
def jinja2_waittime_filter(value):
    current_utc = datetime.utcnow()
    waited_time = current_utc - value
    return str(int(math.floor(waited_time.total_seconds()/60)))
