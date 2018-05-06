import datetime
from typing import Optional, List, Union

import flask
import logging

from esipy import EsiSecurity
from esipy.exceptions import APIException
from flask import current_app
from flask import redirect
from flask import url_for
from flask_login import login_user, current_user
from flask_principal import identity_changed, Identity

from waitlist import db
from waitlist.sso import authorize, who_am_i
from waitlist.storage.database import Account, Character, SSOToken, EveApiScope
from waitlist.utility import config
from waitlist.utility.eve_id_utils import get_character_by_id_and_name, is_char_banned

logger = logging.getLogger(__name__)


def member_login_cb(code):
    auth = authorize(code)
    access_token = auth['access_token']
    refresh_token = auth['refresh_token']
    expires_at = datetime.datetime.utcnow() + datetime.timedelta(seconds=(auth['expires_in']-10))

    auth_info = who_am_i(access_token)
    char_id = auth_info['CharacterID']
    char_name = auth_info['CharacterName']
    owner_hash = auth_info['CharacterOwnerHash']
    scopes = auth_info['Scopes']

    if 'publicData' not in scopes:
        logger.error(f"Missing scope publicData in token.")
        flask.flash("The token we got back from you did not contain the required scope publicData.", "error")
        return redirect(url_for('logout'))

    if char_id is None or char_name is None:
        logger.error("Failed to get character auth info")
        flask.abort(400, "Getting Character from AuthInformation Failed!")

    char: Character = get_character_by_id_and_name(char_id, char_name)

    # this will store our account if the character is eligible for login into an account
    acc: Optional[Account] = None

    # lets check if there is any accounts connected
    logger.info(f"{len(char.accounts)} accounts connected with this character")
    if len(char.accounts) > 0:

        # if we never had a owner hash lets set it
        # it doesn't matter since we need to auth all characters for existing accounts
        if char.owner_hash is None or char.owner_hash == "":
            logger.info("Character owner_hash is empty, this char is accessed for the first time")
            char.owner_hash = owner_hash
            db.session.commit()

        # character changed owner not eligible for account login anymore
        if char.owner_hash != owner_hash:
            logger.info("Character owner_hash did not match")
            invalidate_all_sessions_for_given_user(char)
            char.accounts = []
            char.owner_hash = owner_hash
            db.session.commit()

        else:  # character is still owned by the same person
            logger.info("Character owner_hash did match")
            if len(char.accounts) > 1: # this character is connected with more then 1 account
                logger.error("Connected to multiple accounts, logging in as character.")
                flask.flash(f"Your character {char_name} is connected to more than one Waitlist Account,"
                            f" please contact an Administrator."
                            f" Meanwhile, you are logged in as a normal character.", "danger")
                if char.sso_token is None:
                    char.sso_token = SSOToken()
                else:
                    char.sso_token.accountID = None

                set_token_data(char.sso_token, access_token, refresh_token, expires_at, scopes)
                db.session.commit()

            else:  # connected exactly to 1 account, since <= 1 and > 0
                logger.info("Connected to 1 account")
                acc = char.accounts[0]
                # set the character that was logged in with as active character
                acc.current_char_obj = char

                # does the current token have more scopes AND work?
                if acc.sso_token is not None:
                    # the token has some scopes
                    if len(acc.sso_token.scopes) > 0:
                        # it has more/other scopes then publicData
                        if len(acc.sso_token.scopes) > 1 or \
                                (len(acc.sso_token.scopes) == 1 and acc.sso_token.scopes[0].scopeName != 'publicData'):
                            # it has other scopes, lets try to keep it
                            security: EsiSecurity = EsiSecurity('', config.crest_client_id,
                                                                config.crest_client_secret)
                            security.refresh_token = acc.sso_token.refresh_token
                            try:
                                security.refresh()
                                # if this doesn't throw an exception, we don't update
                            except APIException as e:
                                # this probably happens because the token is invalid now
                                set_token_data(acc.sso_token, access_token, refresh_token, expires_at, scopes)
                                db.session.commit()
                        else:
                            # has same scopes as this, just replace it
                            set_token_data(acc.sso_token, access_token, refresh_token, expires_at, scopes)
                            db.session.commit()

                    else:
                        # old token has no scopes
                        acc.sso_token = SSOToken()
                        set_token_data(acc.sso_token, access_token, refresh_token, expires_at, scopes)
                        db.session.commit()
                else:
                    # no old token
                    acc.sso_token = SSOToken()
                    set_token_data(acc.sso_token, access_token, refresh_token, expires_at, scopes)
                    db.session.commit()

    if acc is not None and not acc.disabled:  # accs are allowed to ignore bans
        logger.info(f"Logging account username={acc.username} id={acc.id} in")
        login_user(acc, remember=True)
        identity_changed.send(current_app._get_current_object(),
                              identity=Identity(acc.id))
        return redirect(url_for("index"))

    # update owner_hash if different
    if char.owner_hash != owner_hash:
        char.owner_hash = owner_hash
        invalidate_all_sessions_for_current_user()

    # update token for this character
    if char.sso_token is None:
        char.sso_token = SSOToken()

    set_token_data(char.sso_token, access_token, refresh_token, expires_at, scopes)
    db.session.commit()

    logger.info(f"Logging character eve_name={char.get_eve_name()} id={char.get_eve_id()} in")
    is_banned, reason = is_char_banned(char)
    if is_banned:
        logger.info(f"Character is banned eve_name={char.get_eve_name()} id={char.get_eve_id()}")
        return flask.abort(401, 'You are banned, because your ' + reason + " is banned!")

    login_user(char, remember=True)
    logger.debug("Member Login by %s successful", char.get_eve_name())
    return redirect(url_for("index"))


def set_token_data(token: SSOToken, access_token: str, refresh_token: str, expires_at: datetime, scopes: str) -> None:
    """
    :param scopes space seperated list of scopes
    """

    token.access_token = access_token
    token.refresh_token = refresh_token
    token.access_token_expires = expires_at
    scope_name_list: List[str] = scopes.split(" ")
    token_scopes: List[EveApiScope] = []

    for scope_name in scope_name_list:
        token_scopes.append(EveApiScope(scopeName=scope_name))

    token.scopes = token_scopes


def invalidate_all_sessions_for_current_user() -> None:
    """
    Invalidates all active session for the current user.
    Not just the current session like force_logout()
    This needs to be called before calling force_logout()
    :return: Nothing
    """

    invalidate_all_sessions_for_given_user(current_user)


def invalidate_all_sessions_for_given_user(user: Union[Character, Account]) -> None:
    """
    Invalidates all active session for the given user.
    Not just the current session like force_logout()
    This needs to be called before calling force_logout()
    :return: Nothing
    """
    user.session_key = user.session_key + 1
    db.session.commit()