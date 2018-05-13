from datetime import datetime, timedelta
from typing import Optional, Union

import flask
import logging

from flask import current_app, session, Response
from flask import redirect
from flask import url_for
from flask_login import login_user, current_user
from flask_principal import identity_changed, Identity

from waitlist import db
from waitlist.blueprints.fc_sso import get_sso_redirect, add_sso_handler
from waitlist.sso import authorize, who_am_i
from waitlist.storage.database import Account, Character, SSOToken, EveApiScope
from waitlist.utility import config
from waitlist.utility.eve_id_utils import get_character_by_id_and_name, is_char_banned
from waitlist.utility.manager import OwnerHashCheckManager

logger = logging.getLogger(__name__)


def login_account_by_username_or_character(char: Character, owner_hash: str) -> Response:
    """
    Handle login, when accounts should be loggedin by username matching the character name
    :param char: Character we got the authentication for
    :param owner_hash: current owner_hash of the character
    :return: a Response that should be delivered to the client
    """
    # see if there is an fc account connected
    # noinspection PyPep8
    acc = db.session.query(Account).filter(
        (Account.username == char.get_eve_name()) & (Account.disabled == False)).first()
    if acc is not None:  # accs are allowed to ignore bans
        login_account(acc)


    return login_character(char, owner_hash)


def login_character(char: Character, owner_hash: str) -> Response:
    """
    Login a character and update the owner_hash/invalidate all existing sessions
    if the owner_hash changed
    This also checks if the character is banned before letting him login
    :param char: the Character to login
    :param owner_hash: the owner_hash to check and update
    :return: a redirect to the next page the client should visite
    """
    # update owner_hash if different

    # if the owner_hash is empty or None, this ist he first timet he character is accessed
    if char.owner_hash is None or char.owner_hash == '':
        char.owner_hash = owner_hash
        db.session.commit()

    # if the hash is there but different the owner changed we need to invalidate sessions and update
    elif char.owner_hash != owner_hash:
        char.owner_hash = owner_hash
        invalidate_all_sessions_for_current_user()
        db.session.commit()

    logger.info(f"Logging character eve_name={char.get_eve_name()} id={char.get_eve_id()} in")
    is_banned, reason = is_char_banned(char)
    if is_banned:
        logger.info(f"Character is banned eve_name={char.get_eve_name()} id={char.get_eve_id()}")
        return flask.abort(401, 'You are banned, because your ' + reason + " is banned!")

    login_user(char, remember=True)
    logger.debug("Member Login by %s successful", char.get_eve_name())
    return redirect(url_for("index"))


def login_account(acc: Account) -> Response:
    """
    Logs in an account and creates the session information, Accounts ignore banns
    :param acc: The account to create the session for
    :return: a redirect to the index page
    """
    logger.info(f"Logging account username={acc.username} id={acc.id} in")
    login_user(acc, remember=True)
    identity_changed.send(current_app._get_current_object(),
                          identity=Identity(acc.id))
    return redirect(url_for("index"))


def login_accounts_by_alts_or_character(char: Character, owner_hash: str) -> Response:
    """
    Handle login, when an account should be loggedin by a connected alt who has no owner_hash or the owner_hash matches
    the current one
    If no matching account is found or more then one account is found, login as user and use flash for a message
    :param char: Character we got the authentication for
    :param owner_hash: current owner_hash of the character
    :return: a Response that should be delivered to the client
    """
    # this will store our account if the character is eligible for login into an account
    acc: Optional[Account] = None

    # lets check if there is any accounts connected
    logger.info(f"{len(char.accounts)} accounts connected with this character")

    account_count = len(char.accounts)

    # if there is no account connected, login as character
    if account_count == 0:
        return login_character(char, owner_hash)

    if account_count > 0:
        # if we never had a owner hash lets set it
        # it doesn't matter since we need to auth all characters for existing accounts
        if char.owner_hash is None or char.owner_hash == "":
            logger.debug("Character owner_hash is empty, %s is accessed for the first time."
                         " Setting owner_hash to %s", char, owner_hash)
            char.owner_hash = owner_hash
            db.session.commit()

        # character changed owner, so not eligible for account login anymore
        elif char.owner_hash != owner_hash:
            logger.debug("Character owner_hash for %s did not match."
                         " Invalidating all sessions and removing character as alt from all accounts.", char)
            flask.flash("You character seemed to have changed owner."
                        " You where removed as eligible character for account login.", 'danger')
            invalidate_all_sessions_for_given_user(char)
            if len(char.accounts) > 0:
                # TODO: send signal here that an alt is removed from this account
                char.accounts = []

            return login_character(char, owner_hash)

        else:
            logger.debug("Character owner_hash for %s did match", char)

            if len(char.accounts) > 1: # this character is connected with more then 1 account
                logger.error("%s connected to multiple accounts, logging in as character.", char)
                flask.flash(f"Your character {char_name} is connected to more than one Waitlist Account,"
                            f" please contact an Administrator."
                            f" Meanwhile, you are logged in as a normal character.", "danger")

                return login_character(char, owner_hash)

            else:  # connected exactly one account since > 0 and not > 1
                logger.debug("%s connected to one account", char)
                acc = char.accounts[0]

                if acc.disabled:  # this account is disabled -> login as character
                    logger.debug("The Account %s is disabled logging in a character", acc)
                    return login_character(char, owner_hash)

                # set no character as active char for the account
                # we will set the login char further in the progress
                # or we will send to reauth if there is no proper api token
                acc.current_char = None

                valid: bool = OwnerHashCheckManager.\
                    is_auth_valid_for_account_character_pair(acc, char)

                if not valid:
                    # log the account in with no character and request alt verification
                    logger.info(f"Logging account username={acc.username} id={acc.id} in")
                    login_user(acc, remember=True)
                    identity_changed.send(current_app._get_current_object(),
                                          identity=Identity(acc.id))
                    session['link_charid'] = char.id
                    return get_sso_redirect("alt_verification", 'publicData')
                else:
                    # set the accounts current character to this character
                    acc.current_char = char.id
                    return login_account(acc)
    else: # not connected to an account

        return login_character(char, owner_hash)


def member_login_cb(code):
    auth = authorize(code)
    refresh_token = auth['refresh_token']
    access_token = auth['access_token']
    expires_in = int(auth['expires_in'])

    token: SSOToken = SSOToken(refresh_token=refresh_token, access_token=access_token,
                               access_token_expires=(datetime.utcnow() + timedelta(seconds=expires_in)))

    auth_info = who_am_i(token)
    char_id = auth_info['CharacterID']
    char_name = auth_info['CharacterName']
    owner_hash = auth_info['CharacterOwnerHash']

    if char_id is None or char_name is None:
        logger.error("Failed to get character auth info")
        flask.abort(400, "Getting Character from AuthInformation Failed!")

    char: Character = get_character_by_id_and_name(char_id, char_name)

    # if we don't need authorization to set a character on an account
    # we get this handled in an other function
    if not config.require_auth_for_chars:
        return login_account_by_username_or_character(char, owner_hash)

    return login_accounts_by_alts_or_character(char, owner_hash)


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

add_sso_handler('linelogin', member_login_cb)